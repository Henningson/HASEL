#!/usr/bin/env python3

"""
"Segment Images"
"Generate Points"
"Remove Points"
"Add Points"
"Remove Bounding Boxes"
"Compute Correspondences"
"Show Bounding Boxes"
"Show Pointlabels"
"""

import os, sys, glob
from functools import partial
from PyQt5 import QtCore, QtSql
from PyQt5.QtGui import QPixmap, QTransform, QImage
from os.path import expanduser, dirname
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QGraphicsScene,
    QGraphicsView,
    QMenu,
    QLabel,
    QLineEdit,
    QFileDialog,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QGraphicsRectItem,
    QGridLayout,
    QGraphicsLineItem,
)
import skvideo.io
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QPushButton,
    QAction,
    QGraphicsPolygonItem,
    QGraphicsEllipseItem,
)
from PyQt5.QtCore import QSize, pyqtSignal, QPointF, QRectF, QLineF, QRect, QPoint
from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor
import torch
from VFLabel.nn.UNet import Model
from VFLabel.utils.LSQ import LSQLocalization
import numpy as np
import cv2
import albumentations as A
from albumentations.pytorch import ToTensorV2
from tqdm import tqdm
import VFLabel.utils.Visualizer as Visualizer
import VFLabel.utils.utils as utils

from VFLabel.vision.Camera import Camera
from VFLabel.vision.Laser import Laser

DEVICE = "cpu"  # "cuda" if torch.cuda.is_available() else "cpu"


def cvImgToQT(image):
    height, width, channel = image.shape
    bytesPerLine = 3 * width
    return QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)


class ZoomableView(QGraphicsView):
    pointSignal = pyqtSignal(QPointF)
    wheelSignal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(ZoomableView, self).__init__(parent)

    def wheelEvent(self, event):
        mouse = event.angleDelta().y() / 120
        self.wheelSignal.emit(mouse > 0)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction("Zoom in               +, E", shufti.zoomIn)
        menu.addAction("Zoom out              -, D", shufti.zoomOut)
        menu.addAction("Toggle fullscreen     F11", shufti.toggleFullscreen)
        menu.addAction("Next image            D", shufti.nextImage)
        menu.addAction("Previous image        D", shufti.prevImage)
        menu.addAction("Forward n frames      E", shufti.nextImage)
        menu.addAction("Backward n frames     A", shufti.prevImage)
        menu.addAction("Fit view              F", shufti.fitView)
        menu.addAction("Reset zoom            1", shufti.zoomReset)
        menu.addAction("Validate Segmentation Enter", shufti.validateSegmentation)
        menu.addAction("Quit                  ESC", shufti.close)
        menu.exec_(event.globalPos())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        point = self.mapToScene(self.mapFromGlobal(event.globalPos()))
        self.pointSignal.emit(point)


class MainWindow(QMainWindow):
    def __init__(self, video_path):
        QMainWindow.__init__(self)
        self.setMinimumSize(QSize(800, 600))

        self.setWindowTitle("Vocalfold Segmentator")

        self.video = skvideo.io.vread(video_path)
        self.current_img_index = 0

        self.img = QPixmap(cvImgToQT(self.video[self.current_img_index]))
        self.scene = QGraphicsScene()
        self.scene.addPixmap(self.img)
        self.view = ZoomableView(self)
        self.view.setScene(self.scene)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.mainwidget = QWidget()
        self.menu_widget = LeftMenuWidget()
        self.base_layout = QHBoxLayout(self.menu_widget)
        self.base_layout.addWidget(self.menu_widget)
        self.base_layout.addWidget(self.view)
        self.mainwidget.setLayout(self.base_layout)
        ## Set the central widget of the Window.
        self.setCentralWidget(self.mainwidget)

        self.menu_widget.button_dict["Open Video"].clicked.connect(self.openVideo)
        self.menu_widget.button_dict["Draw Initial Segmentation"].clicked.connect(
            self.toggleInitialSegmentationMode
        )
        self.menu_widget.button_dict["Transform"].clicked.connect(
            self.toggleTransformMode
        )
        self.menu_widget.button_dict["Interpolate Segmentations"].clicked.connect(
            self.interpolateSegmentations
        )
        self.menu_widget.button_dict["Toggle Segmentation"].clicked.connect(
            self.toggleDrawSegmenation
        )
        self.menu_widget.button_dict["Save Segmentations"].clicked.connect(
            self.saveSegmentations
        )

        self.view.pointSignal.connect(self.segmentationPointAdded)
        self.view.wheelSignal.connect(self.mouseScrollEvent)

        self.initialSegmentationMode = False
        self.transformMode = False
        self.drawSegmentation = True

        self.baseSegmentation = None
        self.transforms = []
        self.lerpedTransforms = None
        self.segmentationPoints = []

        self.pen = QPen(QColor(128, 255, 128, 255))
        self.brush = QBrush(QColor(128, 255, 128, 128))

        self.lerpPen = QPen(QColor(128, 128, 255, 255))
        self.lerpBrush = QBrush(QColor(128, 128, 255, 128))

        self.savePen = QPen(QColor(255, 255, 255, 255))
        self.saveBrush = QBrush(QColor(255, 255, 255, 255))

        self.zoom = 1.0

        self.scale = 1.0
        self.rotAngle = 0.0
        self.translateX = 0.0
        self.translateY = 0.0
        self.saveTransform()

    def openVideo(self):
        video_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", "", "Video Files (*.avi *.mp4 *.mkv *.AVI *.MP4)"
        )

        self.video = skvideo.io.vread(video_path)
        self.current_img_index = 0

        self.initialSegmentationMode = False
        self.transformMode = False
        self.drawSegmentation = True

        self.baseSegmentation = None
        self.transforms = []
        self.lerpedTransforms = None
        self.segmentationPoints = []

        self.zoom = 1.0

        self.scale = 1.0
        self.rotAngle = 0.0
        self.translateX = 0.0
        self.translateY = 0.0
        self.saveTransform()

        self.redraw()

    def saveSegmentations(self):
        save_folder = QFileDialog.getExistingDirectory(
            self, "Open Video", "", QFileDialog.ShowDirsOnly
        )

        self.fitView()
        for i in range(self.video.shape[0]):
            # render scene here
            self.scene.clear()
            self.img = QPixmap(cvImgToQT(self.video[i] * 0.0))
            focusRect = self.scene.addPixmap(self.img).boundingRect()

            topLeft = self.view.mapFromScene(focusRect.topLeft()) + QPoint(1, 1)
            bottomRight = self.view.mapFromScene(focusRect.bottomRight())

            if self.lerpedTransforms is not None:
                pol = QGraphicsPolygonItem(self.baseSegmentation)
                pol.setPen(self.savePen)
                pol.setBrush(self.saveBrush)

                pol.setTransformOriginPoint(pol.boundingRect().center())
                pol.setScale(self.lerpedTransforms[i]["Scale"])
                pol.setRotation(self.lerpedTransforms[i]["Rot"])
                pol.moveBy(
                    self.lerpedTransforms[i]["Trans_X"],
                    self.lerpedTransforms[i]["Trans_Y"],
                )

                self.scene.addItem(pol)

            pixmap = self.view.grab().copy(QRect(topLeft, bottomRight))
            pixmap = pixmap.scaled(self.video.shape[2], self.video.shape[1])
            pixmap.save(os.path.join(save_folder, "{:05d}.png".format(i)))

    def toggleDrawSegmenation(self):
        self.drawSegmentation = not self.drawSegmentation
        self.redraw()

    def toggleTransformMode(self):
        self.transformMode = not self.transformMode

        if self.transformMode:
            self.menu_widget.disableEverythingExcept("Transform")
        else:
            self.menu_widget.enableEverything()

            if self.baseSegmentation is not None:
                self.saveTransform()

    def saveTransform(self):
        self.transforms.append(
            {
                "Frame": self.current_img_index,
                "Scale": self.scale,
                "Trans_X": self.translateX,
                "Trans_Y": self.translateY,
                "Rot": self.rotAngle,
            }
        )

    def toggleInitialSegmentationMode(self):
        self.initialSegmentationMode = not self.initialSegmentationMode

        if self.initialSegmentationMode:
            self.menu_widget.disableEverythingExcept("Draw Initial Segmentation")
        else:
            self.menu_widget.enableEverything()

    @QtCore.pyqtSlot(QPointF)
    def segmentationPointAdded(self, point):
        if not self.initialSegmentationMode:
            return

        if point.x() < 0 or point.y() < 0:
            return

        if (
            point.y() > self.video[0].shape[0] - 1
            or point.x() > self.video[0].shape[1] - 1
        ):
            return

        self.segmentationPoints.append(point)
        self.baseSegmentation = QPolygonF(self.segmentationPoints)
        self.redraw()

    def exitCall(self):
        print("Exit app")

    def saveCall(self):
        print("Save")

    def toggleFullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def downscale(self):
        self.scale -= 0.01
        self.redraw()

    def upscale(self):
        self.scale += 0.01
        self.redraw()

    def rotateClockwise(self):
        self.rotAngle += 0.1
        self.redraw()

    def rotateAntiClockwise(self):
        self.rotAngle -= 0.1
        self.redraw()

    def translateRight(self):
        self.translateX += 1.0
        self.redraw()

    def translateLeft(self):
        self.translateX -= 1.0
        self.redraw()

    def translateDown(self):
        self.translateY += 1.0
        self.redraw()

    def translateUp(self):
        self.translateY -= 1.0
        self.redraw()

    @QtCore.pyqtSlot(bool)
    def mouseScrollEvent(self, bool):
        if not self.transformMode:
            if bool:
                self.zoomIn()
            else:
                self.zoomOut()
            return

        if bool:
            self.rotateClockwise()
        else:
            self.rotateClockwise()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_D:
            self.nextImage()
        elif event.key() == QtCore.Qt.Key_A:
            self.prevImage()

        if self.transformMode:
            if event.key() == QtCore.Qt.Key_Space:
                self.saveTransform()
                self.toggleTransformMode()

            elif event.key() == QtCore.Qt.Key_W:
                self.upscale()
            elif event.key() == QtCore.Qt.Key_S:
                self.downscale()

            elif event.key() == QtCore.Qt.Key_Q:
                self.rotateClockwise()
            elif event.key() == QtCore.Qt.Key_E:
                self.rotateAntiClockwise()

            elif event.key() == QtCore.Qt.Key_I:
                self.translateUp()
            elif event.key() == QtCore.Qt.Key_J:
                self.translateLeft()
            elif event.key() == QtCore.Qt.Key_K:
                self.translateDown()
            elif event.key() == QtCore.Qt.Key_L:
                self.translateRight()

    def lerp(self, v0, v1, t):
        return (1 - t) * v0 + t * v1

    def interpolateSegmentations(self):
        self.lerpedTransforms = []
        for i in range(len(self.transforms) - 1):
            transformA = self.transforms[i]
            transformB = self.transforms[i + 1]

            numFrames = transformB["Frame"] - transformA["Frame"]
            for frame in range(0, numFrames):
                t = frame / numFrames

                new_transform = {}
                new_transform["Scale"] = self.lerp(
                    transformA["Scale"], transformB["Scale"], t
                )
                new_transform["Trans_X"] = self.lerp(
                    transformA["Trans_X"], transformB["Trans_X"], t
                )
                new_transform["Trans_Y"] = self.lerp(
                    transformA["Trans_Y"], transformB["Trans_Y"], t
                )
                new_transform["Rot"] = self.lerp(
                    transformA["Rot"], transformB["Rot"], t
                )

                self.lerpedTransforms.append(new_transform)

        new_transform = {}
        new_transform["Scale"] = self.lerpedTransforms[-1]["Scale"]
        new_transform["Trans_X"] = self.lerpedTransforms[-1]["Trans_X"]
        new_transform["Trans_Y"] = self.lerpedTransforms[-1]["Trans_Y"]
        new_transform["Rot"] = self.lerpedTransforms[-1]["Rot"]

        self.lerpedTransforms.append(new_transform)

        self.redraw()

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
        prev_index = (
            self.video.shape[0] - 1
            if self.current_img_index - 1 == -1
            else self.current_img_index - 1
        )
        self.current_img_index = prev_index
        self.redraw()

    def nextImage(self):
        next_index = (
            0
            if self.current_img_index + 1 == self.video.shape[0]
            else self.current_img_index + 1
        )
        self.current_img_index = next_index
        self.redraw()

    def redraw(self):
        print(self.current_img_index)
        self.scene.clear()
        self.img = QPixmap(cvImgToQT(self.video[self.current_img_index]))
        self.scene.addPixmap(self.img)

        if self.baseSegmentation is not None and self.drawSegmentation:
            pol = QGraphicsPolygonItem(self.baseSegmentation)
            pol.setPen(self.pen)
            pol.setBrush(self.brush)

            pol.setTransformOriginPoint(pol.boundingRect().center())
            pol.setScale(self.scale)
            pol.setRotation(self.rotAngle)
            pol.moveBy(self.translateX, self.translateY)

            self.scene.addItem(pol)

        if self.lerpedTransforms is not None:
            pol = QGraphicsPolygonItem(self.baseSegmentation)
            pol.setPen(self.lerpPen)
            pol.setBrush(self.lerpBrush)

            pol.setTransformOriginPoint(pol.boundingRect().center())
            pol.setScale(self.lerpedTransforms[self.current_img_index]["Scale"])
            pol.setRotation(self.lerpedTransforms[self.current_img_index]["Rot"])
            pol.moveBy(
                self.lerpedTransforms[self.current_img_index]["Trans_X"],
                self.lerpedTransforms[self.current_img_index]["Trans_Y"],
            )

            self.scene.addItem(pol)

    def resetScroll(self):
        self.view.verticalScrollBar().setValue(0)
        self.view.horizontalScrollBar().setValue(0)

    def getScreenRes(self):
        self.screen_res = app.desktop().availableGeometry()
        self.screenw = self.screen_res.width()
        self.screenh = self.screen_res.height()


class LeftMenuWidget(QWidget):
    def __init__(self, parent=None):
        super(LeftMenuWidget, self).__init__()
        # self.setStyle(QFrame.Panel | QFrame.Raised)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.button_dict = {}
        self.edit_dict = {}

        self.addButton("Open Video")
        self.addButton("Draw Initial Segmentation")
        self.addButton("Toggle Segmentation")
        self.addButton("Transform")
        self.addButton("Interpolate Segmentations")
        self.addButton("Save Segmentations")

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    shufti = MainWindow("../HLEDataset/dataset/CF/CF.avi")
    shufti.show()
    sys.exit(app.exec_())
