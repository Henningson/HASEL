#!/usr/bin/env python3

'''
"Segment Images"
"Generate Points"
"Remove Points"
"Add Points"
"Remove Bounding Boxes"
"Compute Correspondences"
"Show Bounding Boxes"
"Show Pointlabels"
'''

import os, sys, glob

#os.environ["CUDA_VISIBLE_DEVICES"]=""

from functools import partial
from PyQt5 import QtCore, QtSql
from PyQt5.QtGui import QPixmap, QTransform, QImage
from os.path import expanduser, dirname
from PyQt5.QtWidgets import QMainWindow, QApplication, QGraphicsScene, QProgressDialog, QGraphicsView, QMenu, QLabel, QFileDialog, QFormLayout, QHBoxLayout, QGraphicsRectItem, QGridLayout, QGraphicsLineItem
import skvideo.io
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QAction, QGraphicsPolygonItem, QGraphicsEllipseItem
from PyQt5.QtCore import QSize, pyqtSignal, QPointF, QRectF, QLineF
from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor
import torch
from models.UNet import Model
from models.LSQ import LSQLocalization
import numpy as np
import cv2
import albumentations as A
from albumentations.pytorch import ToTensorV2
from tqdm import tqdm
import Visualizer
import utils
import json
import shutil


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def cvImgToQT(image):
    height, width, channel = image.shape
    bytesPerLine = 3 * width
    return QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)


class ZoomableView(QGraphicsView):
    pointSignal = pyqtSignal(QPointF)
    removePointSignal = pyqtSignal(QPointF)

    def __init__(self, parent=None):
        super(ZoomableView, self).__init__(parent)
        self.pointRemovalMode = False

    def togglePointRemovalMode(self):
        self.pointRemovalMode = not self.pointRemovalMode

        if self.pointRemovalMode:
            shufti.menu_widget.disableEverythingExcept("Remove Points")
        else:
            shufti.menu_widget.enableEverything()

    def wheelEvent(self, event):
        mouse = event.angleDelta().y()/120
        if mouse > 0:
            shufti.zoomIn()
        elif mouse < 0:
            shufti.zoomOut()

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction('Zoom in               +, E', shufti.zoomIn)
        menu.addAction('Zoom out              -, D', shufti.zoomOut)
        menu.addAction('Toggle fullscreen     F11',  shufti.toggleFullscreen)
        menu.addAction('Next image            D',    shufti.nextImage)
        menu.addAction('Previous image        D',    shufti.prevImage)
        menu.addAction('Forward n frames      E',    shufti.nextImage)
        menu.addAction('Backward n frames     A',    shufti.prevImage)
        menu.addAction('Fit view              F',    shufti.fitView)
        menu.addAction('Reset zoom            1',    shufti.zoomReset)
        menu.addAction('Quit                  ESC',  shufti.close)
        menu.exec_(event.globalPos())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        point = self.mapToScene(self.mapFromGlobal(event.globalPos()))
        
        print(type(self.scene().itemAt(point, QTransform())))

        if not self.pointRemovalMode:
            self.pointSignal.emit(point)
        elif type(self.scene().itemAt(point, QTransform())) == QGraphicsEllipseItem:
            self.scene().removeItem(self.scene().itemAt(point, QTransform()))
            self.removePointSignal.emit(point)

class MainWindow(QMainWindow):    
    def createAction(self, text, shortcut, statustip, function):
        action = QAction(text, self)        
        action.setShortcut(shortcut)
        action.setStatusTip(statustip)
        action.triggered.connect(function)
        return action

    def initMemberVariables(self):
        self.segmentation_mode = False
        self.pointAddMode = False
        self.removeSearchLineMode = False
        self.searchLineMode = False

        self.points2d = []
        self.labeledpoints2d = []
        self.labels = []
        self.segmentationPoints = []
        self.segmentation = None

        self.showSearchLines = True
        self.showLabels = True
        self.showLabeledPoints = True
        self.showGeneratedPoints = True

        self.searchLineTuple = [None, None]
        self.searchLines = []
        self.searchLineIndex = 0
        self.currentButton = [0, 0]

        self.polygonhandle = None

        self.video = None
        self.current_img_index = 0

        self.pointArray = np.zeros([1, 18, 18, 2], dtype=np.float32)
        self.pointArray[:] = np.nan

        self.zoom = 1.0

    def __init__(self):
        QMainWindow.__init__(self)
        self.initMemberVariables()

        self.setMinimumSize(QSize(800, 600))            

        # Create new action
        newAction = self.createAction('&New', 'Ctrl+N', 'New Project', self.newCall)
        loadAction = self.createAction('&Load', 'Ctrl+O', 'Load Project', self.loadCall)
        saveAction = self.createAction('&Save', 'Ctrl+S', 'Save Project', self.saveCall)
        exitAction = self.createAction('&Exit', 'Ctrl+Q', 'Exit program', self.exitCall)

        # Create menu bar and add action
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(newAction)
        fileMenu.addAction(loadAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(exitAction)

        self.setWindowTitle("Structured Light Labelling")

        self.img = QPixmap(cvImgToQT(np.zeros([800, 800, 3], dtype=np.uint8)))
        self.scene = QGraphicsScene()
        self.scene.addPixmap(self.img)
        self.view = ZoomableView(self)
        self.view.setScene(self.scene)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.pointsize = 10

        self.mainwidget = QWidget()
        self.menu_widget = LeftMenuWidget()
        self.base_layout = QHBoxLayout(self.menu_widget)
        self.base_layout.addWidget(self.menu_widget)
        self.base_layout.addWidget(self.view)
        self.mainwidget.setLayout(self.base_layout)
        ## Set the central widget of the Window.
        self.setCentralWidget(self.mainwidget)

        self.menu_widget.button_dict["Segment Images"].clicked.connect(self.toggleSegmentation)
        self.menu_widget.button_dict["Generate Points"].clicked.connect(self.generatePoints)
        self.menu_widget.button_dict["Remove Points"].clicked.connect(self.view.togglePointRemovalMode)
        self.menu_widget.button_dict["Add Points"].clicked.connect(self.togglePointAddMode)
        self.menu_widget.buttonGrid.buttonSignal.connect(self.getGridButtonClicked)
        self.menu_widget.button_dict["Compute Correspondences"].clicked.connect(self.computeCorrespondences)
        self.menu_widget.button_dict["Interpolate Correspondences"].clicked.connect(self.interpolate)
        self.menu_widget.button_dict["Remove Search Lines"].clicked.connect(self.toggleRemoveSearchLineMode)
        self.menu_widget.button_dict["Show Search Lines"].clicked.connect(self.toggleShowSearchLines)
        self.menu_widget.button_dict["Show Generated Points"].clicked.connect(self.toggleShowGeneratedPoints)
        self.menu_widget.button_dict["Show Labeled Points"].clicked.connect(self.toggleShowLabeledPoints)
        self.menu_widget.button_dict["Show Pointlabels"].clicked.connect(self.toggleShowLabels)

        self.view.pointSignal.connect(self.segmentationPointAdded)
        self.view.removePointSignal.connect(self.removePoint)
        self.view.pointSignal.connect(self.addPoint)
        self.view.pointSignal.connect(self.generateSearchLine)
        self.view.pointSignal.connect(self.removeSearchLine)
        
        self.menu_widget.disableEverythingExcept(None)

    def closeEvent(self, event):
        self.winState()

    def newCall(self):
        video_path, _ = QFileDialog.getOpenFileName(self, 'Open Video', '', "Video Files (*.avi *.mp4 *.mkv *.AVI *.MP4)")
        self.folder_path = os.path.join("projects", os.path.splitext(os.path.basename(video_path))[0])

        self.setWindowTitle("Structured Light Labelling - " + os.path.splitext(os.path.basename(video_path))[0])

        try:
            os.mkdir(self.folder_path)
            shutil.copy(video_path,  os.path.join(self.folder_path, os.path.basename(video_path)))
        except:
            print("Folder {0} already exists.".format(self.folder_path))
        
        self.initMemberVariables()
        self.video = skvideo.io.vread(video_path)[:10, :, :, :]
        self.current_img_index = 0
        self.pointArray = np.zeros([self.video.shape[0], 18, 18, 2], dtype=np.float32)
        self.pointArray[:] = np.nan

        self.menu_widget.buttonGrid.reset()
        self.menu_widget.enableEverything()
        self.redraw()

    def loadCall(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, 'Open Folder')

        if self.folder_path == '':
            return

        self.initMemberVariables()
        self.menu_widget.buttonGrid.reset()


        self.setWindowTitle("Structured Light Labelling - " + os.path.basename(self.folder_path))

        self.video = skvideo.io.vread(os.path.join(self.folder_path, os.path.basename(self.folder_path) + ".mp4"))[:10, :, :, :]
        self.segmentation = self.loadSegmentationMask(os.path.join(self.folder_path, "segmentation.png"))
        self.segmentationPoints = self.loadSegmentationPoints(os.path.join(self.folder_path, "segmentation_points.npy"))
        self.points2d = self.loadGeneratedPoints(os.path.join(self.folder_path, "generated_points.json"))
        self.searchLines = self.loadSearchLines(os.path.join(self.folder_path, "search_lines.json"))
        self.labels, self.labeledpoints2d = self.loadLabelsAndPoints(os.path.join(self.folder_path, "labeled_points.json"))
        self.pointArray = self.loadPointArray(os.path.join(self.folder_path, "pointsInGrid.npy"))

        self.menu_widget.enableEverything()
        self.redraw()

    def exitCall(self):
        self.close()
        print('Exit app')

    def saveCall(self):
        if len(self.segmentationPoints) != 0:
            self.saveSegmentationPoints()

        if self.segmentation is not None:
            self.saveSegmentationMask()

        if len(self.points2d) != 0:
            self.saveGeneratedPoints()

        if len(self.searchLines) != 0:
            self.saveSearchLines()

        if len(self.labels) != 0:
            self.saveLabeledPoints()

        if not np.isnan(self.pointArray).all():
            self.savePointArray()

    def toggleRemoveSearchLineMode(self):
        self.removeSearchLineMode = not self.removeSearchLineMode

        if self.removeSearchLineMode:
            self.menu_widget.disableEverythingExcept("Remove Search Lines")
        else:
            self.menu_widget.enableEverything()

    def toggleShowSearchLines(self):
        self.showSearchLines = not self.showSearchLines
        self.redraw()

    def toggleShowGeneratedPoints(self):
        self.showGeneratedPoints = not self.showGeneratedPoints
        self.redraw()

    def toggleShowLabeledPoints(self):
        self.showLabeledPoints = not self.showLabeledPoints
        self.redraw()

    def computeCorrespondences(self, threshold=3.0):
        self.labels = []
        self.labeledpoints2d = self.points2d.copy()

        progress = QProgressDialog("Computing Correspondences", None, 0, len(self.points2d), self)
        progress.setWindowModality(Qt.WindowModal)

        for frame_num, perFramePoints in enumerate(self.points2d):
            progress.setValue(frame_num)
            self.labels.append([])

            test_labels = []
            foundPoints = np.zeros(perFramePoints.shape[0], dtype=np.bool8)
            for line in self.searchLines:
                for i in range(perFramePoints.shape[0]):
                    # Already matched this point, continue
                    if foundPoints[i]:
                        continue
                    
                    pointLineDistance = utils.pointLineSegmentDistance(np.array([line.p1().y(), line.p1().x()]), np.array([line.p2().y(), line.p2().x()]), perFramePoints[i])
                    if pointLineDistance < self.menu_widget.getValueFromEdit("Threshold"):
                        x = line.x
                        y = line.y
                        self.pointArray[frame_num, x, y, 1] = perFramePoints[i, 0]
                        self.pointArray[frame_num, x, y, 0] = perFramePoints[i, 1]
                        self.labels[-1].append([x, y])
                        foundPoints[i] = True
                        test_labels.append(perFramePoints[i])

                # Remove foundPoints from perFramePoints
            self.labeledpoints2d[frame_num] = np.stack(test_labels)

        progress.setValue(len(self.points2d))
        self.redraw()

    def interpolate(self):
        try:
            if np.isnan(self.pointArray).all():
                print("Please compute correspondences first.")
                return

            video_length, height, width, _ = self.pointArray.shape
            progress = QProgressDialog("Interpolating Correspondences", None, 0, video_length - 2, self)
            progress.setWindowModality(Qt.WindowModal)

            for i in range(1, video_length - 1):
                progress.setValue(i - 1)

                for y in range(height):
                    for x in range(width):
                        # Check point at (FRAME[i-1 -> i+1] x X x Y x 2 )
                        points = self.pointArray[i-1:i+2, y, x, :]
                        if np.isnan(points[0]).any():
                            continue

                        if np.isnan(points[2]).any():
                            continue

                        if np.isnan(points[1]).any():
                            new_point = (points[0] + points[2]) / 2.0
                            self.pointArray[i, y, x, :] = new_point
                            self.labels[i].append([y, x])
                            self.labeledpoints2d[i] = np.concatenate([self.labeledpoints2d[i], np.expand_dims(new_point, 0)[:, [1, 0]]])


            progress.setValue(video_length - 2)
            self.redraw()
        except Exception as e:
            print(e)



    def toggleShowLabels(self):
        self.showLabels = not self.showLabels
        self.redraw()

    def toggleSearchLineMode(self):
        self.searchLineMode = not self.searchLineMode

        if self.searchLineMode:
            self.menu_widget.disableEverythingExcept("")
        else:
            self.menu_widget.enableEverything()

    QtCore.pyqtSlot(QPointF)
    def generateSearchLine(self, point):
        if not self.searchLineMode:
            return

        if self.searchLineIndex == 0:
            self.searchLineTuple[0] = point
            self.searchLineIndex = 1
            return

        if self.searchLineIndex == 1:
            self.searchLineTuple[1] = point
            self.searchLineIndex = 0

        x = self.currentButton[0]
        y = self.currentButton[1]

        self.searchLines.append(IdentifiableLineItem(self.searchLineTuple[0].toPoint(), self.searchLineTuple[1].toPoint(), x, y))
        self.toggleSearchLineMode()
        self.redraw()

    @QtCore.pyqtSlot(QPointF)
    def removeSearchLine(self, point):
        if not self.removeSearchLineMode:
            return

        for searchLine in self.searchLines:
            item = self.scene.itemAt(point, QTransform())
            if type(item) == QGraphicsLineItem and searchLine.isEqualsToQGraphicsLine(item):
                self.searchLines.remove(searchLine)

        self.redraw()

    @QtCore.pyqtSlot(int, int)
    def getGridButtonClicked(self, x, y):
        print("Setting laser point {} {}".format(x, y))
        self.currentButton = (x, y)
        self.boundingBoxIndex = 0
        self.toggleSearchLineMode()
    
    @QtCore.pyqtSlot(QPointF)
    def segmentationPointAdded(self, point):
        if not self.segmentation_mode:
            return

        if point.x() < 0 or point.y() < 0:
            return

        if point.y() > self.video[0].shape[0] - 1 or point.x() > self.video[0].shape[1] - 1:
            return

        self.segmentationPoints.append(point)

        if len(self.segmentationPoints) > 0:
            self.drawSegmentation()

    @QtCore.pyqtSlot(QPointF)
    def removePoint(self, clicked_point):
        points = self.points2d[self.current_img_index]
        clicked_point = np.array([clicked_point.y(), clicked_point.x()]).reshape(-1, 2)
        minimum = np.sqrt(np.sum((points - clicked_point)**2, axis=1)).argmin()
        self.points2d[self.current_img_index] = np.delete(points, minimum, axis=0)

    def togglePointAddMode(self):
        self.pointAddMode = not self.pointAddMode

        if self.pointAddMode:
            self.menu_widget.disableEverythingExcept("Add Points")
        else:
            self.menu_widget.enableEverything()

    @QtCore.pyqtSlot(QPointF)
    def addPoint(self, clicked_point):
        if not self.pointAddMode:
            return

        point = np.array([clicked_point.y(), clicked_point.x()])
        self.points2d[self.current_img_index] = np.concatenate([self.points2d[self.current_img_index], point.reshape(-1, 2)])
        self.redraw()

    def toggleSegmentation(self):
        self.segmentation_mode = not self.segmentation_mode

        if self.segmentation_mode:
            self.menu_widget.disableEverythingExcept("Segment Images")
        else:
            self.menu_widget.enableEverything()


        if len(self.segmentationPoints) > 2:
            self.generateCVSegmentation()

    def drawSegmentation(self):
        if self.polygonhandle:
            self.scene.removeItem(self.polygonhandle)

        self.polygonhandle = self.scene.addPolygon(QPolygonF(self.segmentationPoints), QPen(QColor(128, 128, 255, 128)), QBrush(QColor(128, 128, 255, 128)))

    def drawSearchLines(self):
        for searchLine in self.searchLines:
            self.scene.addLine(searchLine, QPen(QColor(128, 255, 128, 128)))

    def drawLabels(self):
        try:
            for label, pos in zip(self.labels[self.current_img_index], self.labeledpoints2d[self.current_img_index].tolist()):
                if np.isnan(np.array(pos)).any():
                    continue

                text = self.scene.addText("{},{}".format(label[0], label[1]))
                text.setPos(pos[1], pos[0])
                text.setDefaultTextColor(QColor(255, 128, 128, 255))
        except:
            return

    def generateCVSegmentation(self):
        base = np.zeros((self.video[0].shape[0], self.video[0].shape[1]), dtype=np.uint8)
        np_points = np.array([[point.x(), point.y()] for point in self.segmentationPoints], dtype=np.int32)
        test = cv2.drawContours(base, [np_points], 0, thickness=-1, color=1)
        self.segmentation = test

    def generatePoints(self):
        if self.segmentation is None:
            print("Please generate a segmentation")
            return

        model = Model(in_channels=1, out_channels=2, state_dict=torch.load("rhine_hard_net_large.pth.tar", map_location=DEVICE), features=[32, 64, 128, 256, 512, 1024]).to(DEVICE)
        loc = LSQLocalization(local_maxima_window=25, device=DEVICE)
        transform = A.Compose([A.Resize(height=1200, width=800), A.Normalize(mean=[0.0], std=[1.0], max_pixel_value=255.0,), ToTensorV2(), ])
        segment_transform = A.Compose([A.Resize(height=1200, width=800), ToTensorV2(),])


        progress = QProgressDialog("Generating Points", None, 0, self.video.shape[0], self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)

        with torch.no_grad():
            for count in range(self.video.shape[0]):
                progress.setValue(count)
                image = cv2.cvtColor(self.video[count], cv2.COLOR_RGB2GRAY)
                image = transform(image=image)["image"].to(DEVICE)
                segment = segment_transform(image=self.segmentation)["image"].to(DEVICE)

                with torch.cuda.amp.autocast():
                    prediction = model(image.unsqueeze(0)).softmax(dim=1)
                    #_, mean, _ = loc.test_with_image(image, prediction, segmentation=segment)
                    _, mean, _ = loc.test(prediction, segmentation=segment)
                    means = mean[0].detach().cpu().numpy()

                    self.points2d.append(means[~np.isnan(means).any(axis=1)])


        progress.setValue(self.video.shape[0])
        self.redraw()

    def drawGeneratedPoints(self):
        if not len(self.points2d) > 0:
            return

        print("Num of Points2D at Frame {0}: {1}".format(self.current_img_index, self.points2d[self.current_img_index].shape[0]))

        for point in self.points2d[self.current_img_index].tolist():
            self.scene.addEllipse(point[1] - self.pointsize//2, point[0] - self.pointsize//2, self.pointsize, self.pointsize, QPen(QColor(128, 128, 255, 128)), QBrush(QColor(128, 128, 255, 128)))

    def drawLabeledPoints(self):
        if not len(self.labeledpoints2d) > 0:
            return

        print("Num of Points2D at Frame {0}: {1}".format(self.current_img_index, self.points2d[self.current_img_index].shape[0]))

        for point in self.labeledpoints2d[self.current_img_index].tolist():
            self.scene.addEllipse(point[1] - self.pointsize//2, point[0] - self.pointsize//2, self.pointsize, self.pointsize, QPen(QColor(255, 128, 128, 128)), QBrush(QColor(255, 128, 128, 128)))

    def saveSegmentationPoints(self):
        np.save(os.path.join(self.folder_path, "segmentation_points.npy"), np.array(self.segmentationPoints))

    def loadSegmentationPoints(self, path):
        try: 
            return np.load(path)
        except:
            return []

        return []

    def saveSegmentationMask(self):
        segmentation_image_file_path = os.path.join(self.folder_path, "segmentation.png")
        cv2.imwrite(segmentation_image_file_path, self.segmentation*255)

    def loadSegmentationMask(self, path):
        try:
            return cv2.imread(path, 0) // 255
        except:
            return None

    def saveGeneratedPoints(self):
        generated_points_file_path = os.path.join(self.folder_path, "generated_points.json")

        point_dict = {}
        for frame, per_frame_points in enumerate(self.points2d):
            frame_list = []
            for point in per_frame_points.tolist():
                frame_list.append({"position_x": float(point[1]), "position_y": float(point[0])})
            point_dict["Frame{0}".format(frame)] = frame_list

        with open(generated_points_file_path, "w") as fp:
            json.dump(point_dict,fp)

    def loadGeneratedPoints(self, path):
        try:
            data = json.load(open(path))
            points = []
            keys = data.keys()
            sorted(keys)

            for key in keys:
                framePoints = []
                for point in data[key]:
                    framePoints.append(np.array((point["position_y"], point["position_x"])))
                framePoints = np.array(framePoints)
                points.append(framePoints)

            return points
        except:
            return []

    def loadPointArray(self, path):
        try:
            return np.load(path)
        except:
            return np.zeros([self.video.shape[0], 18, 18, 2], dtype=np.float32)


    def savePointArray(self):
        np.save(os.path.join(self.folder_path, "pointsInGrid.npy"), self.pointArray)

    def saveSearchLines(self):
        search_lines_file_path = os.path.join(self.folder_path, "search_lines.json")
        search_line_dict = {}
        for count, line in enumerate(self.searchLines):
            search_line_dict["Line{0}".format(count)] = {
                "x0": float(line.p1().x()), 
                "x1": float(line.p2().x()), 
                "y0": float(line.p1().y()), 
                "y1": float(line.p2().y()), 
                "label_x": int(line.x), 
                "label_y": int(line.y)}

        with open(search_lines_file_path, "w") as fp:
            json.dump(search_line_dict, fp)

    def loadSearchLines(self, path):
        try:
            data = json.load(open(path))
            searchLines = []
            for key in data.keys():
                x = data[key]["label_x"]
                y = data[key]["label_y"]
                
                self.menu_widget.buttonGrid.getButton(y, x).setActivated()
                searchLines.append(IdentifiableLineItem(QPointF(data[key]["x0"], data[key]["y0"]), QPointF(data[key]["x1"], data[key]["y1"]), x, y))
            return searchLines
        except:
            []

    def saveLabeledPoints(self):
        labeled_points_file_path = os.path.join(self.folder_path, "labeled_points.json")

        point_dict = {}
        for frame, (per_frame_labels, per_frame_points) in enumerate(zip(self.labels, self.labeledpoints2d)):
            frame_list = []
            for label, point in zip(per_frame_labels, per_frame_points.tolist()):
                frame_list.append({"position_x": float(point[1]), "position_y": float(point[0]), "label_x": int(label[0]), "label_y": int(label[1])})
            point_dict["Frame{0}".format(frame)] = frame_list

        with open(labeled_points_file_path, "w") as fp:
            json.dump(point_dict,fp)
    
    def loadLabelsAndPoints(self, path):
        try:
            data = json.load(open(path))
            points = []
            labels = []
            keys = data.keys()
            sorted(keys)

            for key in keys:
                frameLabels = []
                framePoints = []
                
                for point in data[key]:
                    framePoints.append(np.array((point["position_y"], point["position_x"])))
                    frameLabels.append([point["label_x"], point["label_y"]])

                framePoints = np.array(framePoints)
                points.append(framePoints)
                labels.append(frameLabels)

            return labels, points
        except:
            return [], []

    def toggleFullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F11:
            self.toggleFullscreen()
        elif event.key() == QtCore.Qt.Key_Equal or event.key() == QtCore.Qt.Key_W:
            self.zoomIn()
        elif event.key() == QtCore.Qt.Key_Minus or event.key() == QtCore.Qt.Key_S:
            self.zoomOut()
        elif event.key() == QtCore.Qt.Key_1:
            self.zoomReset()
        elif event.key() == QtCore.Qt.Key_F:
            self.fitView()
        elif event.key() == QtCore.Qt.Key_D:
            self.nextImage()
        elif event.key() == QtCore.Qt.Key_A:
            self.prevImage()
        elif event.key() == QtCore.Qt.Key_Q:
            self.close()

    def zoomIn(self):
        self.zoom *= 1.1
        self.updateView()

    def zoomOut(self):
        self.zoom /= 1.1
        self.updateView()

    def zoomReset(self):
        self.zoom = 1
        self.updateView()

    def fitView(self):
        self.view.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        self.zoom = self.view.transform().m11()

    def updateView(self):
        self.view.setTransform(QTransform().scale(self.zoom, self.zoom))

    def winState(self):
        self.winsizex = self.geometry().width()
        self.winsizey = self.geometry().height()
        self.vscroll = self.view.verticalScrollBar().value()
        self.hscroll = self.view.horizontalScrollBar().value()
        self.winposx = self.pos().x()
        self.winposy = self.pos().y()

    def prevImage(self):
        prev_index = self.current_img_index - 1 if self.current_img_index > 0 else self.current_img_index
        self.current_img_index = prev_index

        self.setImage(self.video[self.current_img_index])

    def nextImage(self):
        next_index = self.current_img_index + 1 if self.current_img_index < self.video.shape[0] - 1 else self.current_img_index
        self.current_img_index = next_index

        self.setImage(self.video[self.current_img_index])

    def setImage(self, image):
        self.scene.clear()
        self.img = QPixmap(cvImgToQT(image))
        self.scene.addPixmap(self.img)

        if self.showGeneratedPoints:
            self.drawGeneratedPoints()
        
        if self.showLabeledPoints:
            self.drawLabeledPoints()

        if self.showSearchLines:
            self.drawSearchLines()

        if self.showLabels:
            self.drawLabels()

    def redraw(self):
        self.scene.clear()
        self.img = QPixmap(cvImgToQT(self.video[self.current_img_index]))
        self.scene.addPixmap(self.img)

        if self.showGeneratedPoints:
            self.drawGeneratedPoints()
        
        if self.showLabeledPoints:
            self.drawLabeledPoints()

        if self.showSearchLines:
            self.drawSearchLines()

        if self.showLabels:
            self.drawLabels()

    def resetScroll(self):
        self.view.verticalScrollBar().setValue(0)
        self.view.horizontalScrollBar().setValue(0)

    def getScreenRes(self):
        self.screen_res = app.desktop().availableGeometry()
        self.screenw = self.screen_res.width()
        self.screenh = self.screen_res.height()


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton
from gridbuttonclick import ButtonGrid

class LeftMenuWidget(QWidget):
    def __init__(self, parent=None):
        super(LeftMenuWidget, self).__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)
        self.button_dict = {}
        self.edit_dict = {}
        self.buttonGrid = ButtonGrid()

        self.addButton("Segment Images")
        self.addButton("Generate Points")
        self.addButton("Remove Points")
        self.addButton("Add Points")
        self.addButton("Show Search Lines")
        self.addButton("Show Pointlabels")
        self.addButton("Show Generated Points")
        self.addButton("Show Labeled Points")
        self.layout().addWidget(self.buttonGrid)
        self.addButton("Remove Search Lines")
        self.addLineEdit("Threshold", 3.0)
        self.addButton("Compute Correspondences")
        self.addButton("Interpolate Correspondences")

    def getValueFromEdit(self, key):
        return float(self.edit_dict[key].text())

    def disableEverythingExcept(self, button_key):
        for key in self.button_dict.keys():
            if button_key != key:
                self.button_dict[key].setEnabled(False)

    def enableEverything(self):
        for button in self.button_dict.values():
            button.setEnabled(True)

    def addLineEdit(self, label, defaultvalue):
        widget = QWidget()
        widget.setLayout(QFormLayout())
        lineedit = QLineEdit(str(defaultvalue), widget)
        widget.layout().addRow(QLabel(label, widget), lineedit)
        self.edit_dict[label] = lineedit
        self.layout().addWidget(widget)

    def addButton(self, label):
        button = QPushButton(label)
        self.layout().addWidget(button)
        self.button_dict[label] = button


class IdentifiableRectItem(QRectF):
    def __init__(self, pointa, pointb, x, y):
        super(IdentifiableRectItem, self).__init__(pointa, pointb)
        self.x = x
        self.y = y

    def isEquals(self, x, y):
        return self.x == x and self.y == y

    def isEqualsToQGraphicsRect(self, qGraphicsRect):
        return self == qGraphicsRect.rect()


class IdentifiableLineItem(QLineF):
    def __init__(self, pointa, pointb, x, y):
        super(IdentifiableLineItem, self).__init__(pointa, pointb)
        self.x = x
        self.y = y

    def isEquals(self, x, y):
        return self.x == x and self.y == y

    def isEqualsToQGraphicsLine(self, qGraphicsLine):
        return self == qGraphicsLine.line()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    shufti = MainWindow()
    shufti.show()
    sys.exit(app.exec_())