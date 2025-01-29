import os
import cv2

from typing import List

from PyQt5.QtCore import Qt, QLineF, QPoint, QRect, QRectF
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMenu, QGraphicsPixmapItem
from PyQt5.QtGui import QBrush, QColor, QCursor, QImage, QPen, QPainter, QPixmap
import PyQt5.QtCore as QtCore
import numpy as np


import gui.videoViewWidget
import VFLabel.utils.transforms as transforms
import VFLabel.utils.enums as enums
from VFLabel.gui.progressDialog import ProgressDialog

from VFLabel.utils.defines import COLOR


class GlottisSegmentationMaskView(gui.videoViewWidget.VideoViewWidget):
    def __init__(self, segmentation_video, project_path: str, parent=None):
        super().__init__(segmentation_video, parent)

        self.setMouseTracking(True)
        self.previous_point = None
        self.segmentation_video = segmentation_video
        self.project_path = project_path
        self.draw_mode = enums.DRAW_MODE.OFF

        self.brush_size = 20
        self.brush = QBrush(QColor(0, 0, 0, 0))
        self.pen = QPen(QColor(128, 128, 128, 255))
        self.drawing_brush = None

        self.per_frame_circles = (
            [[] for _ in range(len(self.images))] if segmentation_video else None
        )  # Holds the drawn circles for each frame.
        self.added_circles_stack = (
            [] if segmentation_video else None
        )  # Holds the frames, which had points added last.

    def add_video(self, video: List[QImage]) -> None:
        self.images = video
        self._num_frames = len(self.images)

        self.per_frame_circles = [
            [] for _ in range(len(self.images))
        ]  # Holds the drawn circles for each frame.
        self.added_circles_stack = []  # Holds the frames, which had points added last.

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction("Zoom in\tMouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out\tMouseWheel Down", self.zoomOut)
        menu.addAction("Frame forward\tRight Arrow", self.frame_forward)
        menu.addAction("Frame backward\tLeft Arrow", self.frame_backward)
        menu.addAction("Increase brush size\t+", self.increase_brush_size)
        menu.addAction("Decrease brush size\t-", self.decrease_brush_size)
        menu.addAction("Undo\tr", self.undo)
        menu.addAction("Reset Zoom", self.zoomReset)
        menu.addAction("Recompute Segmentations", self.generate_new_segmentations)
        menu.exec_(event.globalPos())

    def keyPressEvent(self, event):
        if not self.images:
            return

        super().keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_Plus:
            self.increase_brush_size()

        if event.key() == QtCore.Qt.Key_Minus:
            self.decrease_brush_size()

        if event.key() == QtCore.Qt.Key_R:
            self.undo()

    def mousePressEvent(self, event):
        if not self.images:
            return

        if self.draw_mode == enums.DRAW_MODE.ON:
            mouse_cursor_position = self.mapToScene(event.pos())

            if event.button() == Qt.LeftButton:
                height = self.images[self._current_frame].height()
                width = self.images[self._current_frame].width()

                if (
                    0 <= mouse_cursor_position.x() < width
                    and 0 <= mouse_cursor_position.y() < height
                ):
                    circle_pointer = self.scene().addEllipse(
                        mouse_cursor_position.x() - self.brush_size / 2,
                        mouse_cursor_position.y() - self.brush_size / 2,
                        self.brush_size,
                        self.brush_size,
                        QPen(QColor(0, 0, 0)),
                        QBrush(QColor(0, 0, 0)),
                    )
                    self.per_frame_circles[self._current_frame].append(circle_pointer)
                    self.added_circles_stack.append(self._current_frame)

                self.redraw()
        else:
            if self.drawing_brush:
                self.scene().removeItem(self.drawing_brush)
                self.redraw()
            super().mousePressEvent(event)

    def generate_new_segmentations(self) -> List[QImage]:
        images = []

        current_frame = self._current_frame
        for i in range(len(self.images)):
            if i == 85:
                a = 1
            self.change_frame(i)
            self.fit_view()

            pixmap_item = next(
                (
                    item
                    for item in self.scene().items()
                    if isinstance(item, QGraphicsPixmapItem)
                ),
                None,
            )
            focus_rect = pixmap_item.boundingRect()  # Get the scene dimensions
            topLeft = self.mapFromScene(focus_rect.topLeft()) + QPoint(1, 1)
            bottomRight = self.mapFromScene(focus_rect.bottomRight()) - QPoint(1, 1)

            pixmap = QPixmap(self.images[0].width(), self.images[0].height())
            painter = QPainter(pixmap)
            self.render(
                painter,
                QRectF(0, 0, self.images[0].width(), self.images[0].height()),
                QRect(topLeft, bottomRight),
            )  # Render the scene onto the pixmap
            painter.end()
            qimage = pixmap.toImage().convertToFormat(QImage.Format_RGB888)
            images.append(qimage)

        self.images = images
        self.change_frame(current_frame)

        return self.images

    def mouseMoveEvent(self, event):
        if self.draw_mode == enums.DRAW_MODE.ON:
            mouse_cursor_position = self.mapToScene(event.pos())

            if not self.drawing_brush:
                self.drawing_brush = self.scene().addEllipse(
                    mouse_cursor_position.x() - self.brush_size / 2,
                    mouse_cursor_position.y() - self.brush_size / 2,
                    self.brush_size,
                    self.brush_size,
                    self.pen,
                    self.brush,
                )
            else:
                self.drawing_brush.setRect(
                    mouse_cursor_position.x() - self.brush_size / 2,
                    mouse_cursor_position.y() - self.brush_size / 2,
                    self.brush_size,
                    self.brush_size,
                )

                # self.redraw()

    def toggle_draw_state(self):
        self.setFocus()
        if self.draw_mode == enums.DRAW_MODE.OFF:
            self.draw_mode = enums.DRAW_MODE.ON
        elif self.draw_mode == enums.DRAW_MODE.ON:
            self.redraw()
            self.draw_mode = enums.DRAW_MODE.OFF

    def increase_brush_size(self) -> None:
        self.brush_size += 1

    def decrease_brush_size(self) -> None:
        self.brush_size = 0 if self.brush_size <= 1 else self.brush_size - 1

    def undo(self):
        if len(self.added_circles_stack) == 0:
            return

        frame = self.added_circles_stack.pop()
        self.per_frame_circles[frame].pop()

        self.redraw()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.previous_point = None

    def qImage_list_2_black_white_np_list(self, images: list) -> list:
        images_list = []
        for img in images:
            img_np = transforms.qImage_2_np(img)
            mask = np.all(img_np == COLOR.GLOTTIS, axis=-1)
            img_np[mask] = np.array([255, 255, 255])
            images_list.append(img_np)

        return images_list

    def redraw(self) -> None:
        for item in self.scene().items():
            self.scene().removeItem(item)

        if self.images:
            self.set_image(self.images[self._current_frame])

        if self.per_frame_circles:
            for ellipse in self.per_frame_circles[self._current_frame]:
                self.scene().addItem(ellipse)

        if self.drawing_brush and self.draw_mode == enums.DRAW_MODE.ON:
            self.scene().addItem(self.drawing_brush)

    def save_segmentation_mask(self):
        QApplication.processEvents()
        save_folder = os.path.join(self.project_path, "glottis_segmentation")
        os.makedirs(save_folder, exist_ok=True)

        images_list = self.qImage_list_2_black_white_np_list(self.images)

        for frame_index, seg in enumerate(
            ProgressDialog(images_list, "Saving Segmentations")
        ):
            image_save_path = os.path.join(save_folder, f"{frame_index:05d}.png")
            cv2.imwrite(image_save_path, seg)
