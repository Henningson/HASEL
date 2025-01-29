import os
import cv2

from PyQt5.QtCore import Qt, QLineF, QPoint
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMenu
import PyQt5.QtCore as QtCore

import gui.videoViewWidget
import VFLabel.utils.transforms as transforms
import VFLabel.utils.enums as enums
from VFLabel.utils.defines import COLOR


class GlottisSegmentationMaskView(gui.videoViewWidget.VideoViewWidget):
    def __init__(self, segmentation_video, project_path, parent=None):
        super().__init__(segmentation_video, parent)
        self.previous_point = None
        self.segmentation_video = segmentation_video
        self.project_path = project_path
        self.draw_mode = enums.DRAW_MODE.OFF
        self.img_np = None
        self.list_old_points = []
        self.last_current_frame = 0

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction("Zoom in\tMouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out\tMouseWheel Down", self.zoomOut)
        menu.addAction("Frame forward\tRight Arrow", self.frame_forward)
        menu.addAction("Frame backward\tLeft Arrow", self.frame_backward)
        menu.addAction("Reset Zoom", self.zoomReset)
        menu.addAction("Reset last edit\tr", self.remove_last_drawing)
        menu.exec_(event.globalPos())

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_R:
            self.remove_last_drawing()

    def mousePressEvent(self, event):
        if self.draw_mode.value:
            if self._current_frame != self.last_current_frame:
                self.list_old_points = []
            if event.button() == Qt.LeftButton:
                self.previous_point = self.mapToScene(event.pos())
                pos = self.previous_point.toPoint()

                height = self.images[self._current_frame].height()
                width = self.images[self._current_frame].width()

                if 0 <= pos.x() < width and 0 <= pos.y() < height:
                    if self.images[self._current_frame].pixelColor(pos) != QColor(
                        0, 0, 0
                    ):
                        self.list_old_points.append(pos)
                    self.images[self._current_frame].setPixelColor(pos, QColor(0, 0, 0))

                self.last_current_frame = self._current_frame
                self.redraw()

    def mouseMoveEvent(self, event):
        if self.draw_mode.value:
            if self._current_frame != self.last_current_frame:
                self.list_old_points = []
            if self.previous_point:
                current_point = self.mapToScene(event.pos())

                list_points = []

                line = QLineF(self.previous_point, current_point)
                for i in range(0, 100):
                    i = 0.01 * i

                    pos = line.pointAt(i).toPoint()

                    height = self.images[self._current_frame].height()
                    width = self.images[self._current_frame].width()

                    if 0 <= pos.x() < width and 0 <= pos.y() < height:
                        if self.images[self._current_frame].pixelColor(pos) != QColor(
                            0, 0, 0
                        ):
                            list_points.append(pos)
                        self.images[self._current_frame].setPixelColor(
                            pos, QColor(0, 0, 0)
                        )

                self.previous_point = current_point
                if list_points:
                    self.list_old_points.append(list_points)
                self.last_current_frame = self._current_frame
                self.redraw()

    def change_draw_state(self, state):
        if state == 2:
            self.draw_mode = enums.DRAW_MODE.ON
        elif state == 0:
            self.draw_mode = enums.DRAW_MODE.OFF
        else:
            pass

    def remove_last_drawing(self):
        if self._current_frame == self.last_current_frame:
            if len(self.list_old_points):
                points = self.list_old_points.pop()
                if isinstance(points, QPoint):
                    points = [points]

                for p in points:
                    self.images[self._current_frame].setPixelColor(
                        p, QColor(102, 194, 165)
                    )

                self.redraw()
        else:
            self.list_old_points = []

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.previous_point = None

    def qImage_list_2_black_white_np_list(self, images: list) -> list:
        images_list = []
        for img in images:
            img_np = transforms.qImage_2_np(img)
            img_np[img_np > 0] = 255
            images_list.append(img_np)

        return images_list

    def save_segmentation_mask(self):
        QApplication.processEvents()
        save_folder = os.path.join(self.project_path, "glottis_segmentation")
        os.makedirs(save_folder, exist_ok=True)

        images_list = self.qImage_list_2_black_white_np_list(self.images)

        self.img_np = images_list

        for frame_index, seg in enumerate(images_list):
            image_save_path = os.path.join(save_folder, f"{frame_index:05d}.png")
            cv2.imwrite(image_save_path, seg)
