import VFLabel.gui.zoomableViewWidget as zoomableViewWidget
import VFLabel.utils.enums as enums
import VFLabel.utils.transforms as transforms

from typing import List
from PyQt5.QtCore import QPointF, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor, QPixmap
from PyQt5.QtWidgets import QGraphicsView, QMenu, QGraphicsEllipseItem, QGraphicsScene
from PyQt5 import QtCore
from PyQt5.QtGui import QImage
import PyQt5.Qt
import numpy as np
from PyQt5.QtCore import Qt, QTimer


class InterpolateSegmentationWidget(zoomableViewWidget.ZoomableViewWidget):
    def __init__(
        self,
        images: List[QImage],
        polygon_points: List[QPointF],
        final_transform: List[float],
        parent=None,
    ):
        super(InterpolateSegmentationWidget, self).__init__(parent)
        self._polygonpen = QPen(QColor(255, 128, 128, 255))
        self._polygonbrush = QBrush(QColor(200, 128, 128, 128))

        self.x_translation: float = final_transform[0]
        self.y_translation: float = final_transform[1]
        self.scale: float = final_transform[2]
        self.rotation_angle: float = final_transform[3]

        self.frames = images

        self.set_image(images[0])

        self._polygon_pointer = None

        if polygon_points:
            self.add_polygon(QPolygonF(polygon_points))

        self._current_frame: int = 0
        self._num_frames = len(images)

    def wheelEvent(self, event) -> None:
        mouse = event.angleDelta().y() / 120

        if mouse > 0:
            self.zoomIn()
        else:
            self.zoomOut()
        return

    def contextMenuEvent(self, event) -> None:
        """
        Opens a context menu with options for zooming in and out.

        :param event: The QContextMenuEvent containing information about the context menu event.
        :type event: QContextMenuEvent
        """
        menu = QMenu()
        menu.addAction("Zoom in               MouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out              MouseWheel Down", self.zoomOut)
        menu.exec_(event.globalPos())

    def generate_segmentation_for_frame(self, index: int) -> np.array:
        if not self._polygon_pointer:
            return np.array([-1])

        self.fit_view()

        # Make background black
        black_image = transforms.np_2_QImage(
            np.zeros([self.frames[0].height(), self.frames[0].width(), 3], np.uint8)
        )
        pixmap = QPixmap(black_image)
        self.set_image(QImage(pixmap))

        focusRect = self.scene().addPixmap(pixmap).boundingRect()
        topLeft = self.mapFromScene(focusRect.topLeft()) + QPoint(1, 1)
        bottomRight = self.mapFromScene(focusRect.bottomRight())

        self._polygon_pointer.setPen(QPen(QColor(255, 255, 255, 255)))
        self._polygon_pointer.setBrush(QBrush(QColor(255, 255, 255, 255)))

        self._polygon_pointer.setTransformOriginPoint(
            self._polygon_pointer.boundingRect().center()
        )
        self._polygon_pointer.setZValue(1.0)

        interpolation_factor = index / (self._num_frames - 1)
        lerped_scale = transforms.lerp(1.0, self.scale, interpolation_factor)
        lerped_x_trans = transforms.lerp(0.0, self.x_translation, interpolation_factor)
        lerped_y_trans = transforms.lerp(0.0, self.y_translation, interpolation_factor)
        lerped_rot = transforms.lerp(0.0, self.rotation_angle, interpolation_factor)

        if index == self.marks[-1]:
            arg_smaller = np.where(self.marks < index, self.marks, -10)
            border_frame_bottom = sorted(
                np.intersect1d(arg_smaller, list(self.dict_transform.keys())),
                key=lambda x: int(x),
            )[-1].astype(int)
            border_frame_top = self.marks[-1].astype(int)
        else:
            arg_smaller = np.where(self.marks <= index, self.marks, -10)
            border_frame_bottom = sorted(
                np.intersect1d(arg_smaller, list(self.dict_transform.keys())),
                key=lambda x: int(x),
            )[-1].astype(int)
            arg_bigger = np.where(self.marks > index, self.marks, -10)
            border_frame_top = sorted(
                np.intersect1d(arg_bigger, list(self.dict_transform.keys())),
                key=lambda x: int(x),
            )[0].astype(int)

        interpolation_factor = (index - border_frame_bottom) / (
            border_frame_top - border_frame_bottom
        )

        lerped_x_trans = transforms.lerp(
            self.dict_transform[f"{border_frame_bottom}"][0],
            self.dict_transform[f"{border_frame_top}"][0],
            interpolation_factor,
        )
        lerped_y_trans = transforms.lerp(
            self.dict_transform[f"{border_frame_bottom}"][1],
            self.dict_transform[f"{border_frame_top}"][1],
            interpolation_factor,
        )
        lerped_scale = transforms.lerp(
            self.dict_transform[f"{border_frame_bottom}"][2],
            self.dict_transform[f"{border_frame_top}"][2],
            interpolation_factor,
        )
        lerped_rot = transforms.lerp(
            self.dict_transform[f"{border_frame_bottom}"][3],
            self.dict_transform[f"{border_frame_top}"][3],
            interpolation_factor,
        )

        self._polygon_pointer.setScale(lerped_scale)
        self._polygon_pointer.setRotation(lerped_rot)
        self._polygon_pointer.setPos(lerped_x_trans, lerped_y_trans)

        pixmap = self.grab().copy(QRect(topLeft, bottomRight))
        pixmap = pixmap.scaled(
            self.frames[0].width(), self.frames[0].height(), transformMode=0
        )

        self._polygon_pointer.setPen(self._polygonpen)
        self._polygon_pointer.setBrush(self._polygonbrush)

        return pixmap

    def update_transforms(
        self, x_trans: float, y_trans: float, scale: float, rot: float
    ):
        self.x_translation = x_trans
        self.y_translation = y_trans
        self.scale = scale
        self.rotation_angle = rot
        self.redraw_from_dictionary()

    def redraw(self) -> None:
        self.set_image(self.frames[self._current_frame])

        if not self._polygon_pointer:
            return

        self._polygon_pointer.setZValue(1.0)

        self._polygon_pointer.setTransformOriginPoint(
            self._polygon_pointer.boundingRect().center()
        )

        interpolation_factor = self._current_frame / (self._num_frames - 1)
        lerped_scale = transforms.lerp(1.0, self.scale, interpolation_factor)
        lerped_x_trans = transforms.lerp(0.0, self.x_translation, interpolation_factor)
        lerped_y_trans = transforms.lerp(0.0, self.y_translation, interpolation_factor)
        lerped_rot = transforms.lerp(0.0, self.rotation_angle, interpolation_factor)

        self._polygon_pointer.setScale(lerped_scale)
        self._polygon_pointer.setRotation(lerped_rot)
        self._polygon_pointer.setPos(lerped_x_trans, lerped_y_trans)

    def redraw_from_dictionary(self) -> None:
        self.set_image(self.frames[self._current_frame])

        if not self._polygon_pointer:
            return

        self._polygon_pointer.setZValue(1.0)

        self._polygon_pointer.setTransformOriginPoint(
            self._polygon_pointer.boundingRect().center()
        )

        # calculate upper and lower limit values for interpolation factor
        if self._current_frame == self.marks[-1]:
            # for the last frame
            # find limit values that are smaller than current
            values_smaller = np.where(self.marks < self._current_frame, self.marks, -10)

            # check which values have already initialized interpolation values and choose closest to current
            smaller_values_available = np.intersect1d(
                values_smaller, list(self.dict_transform.keys())
            )
            border_frame_bottom = sorted(
                smaller_values_available,
                key=lambda x: int(x),
            )[-1].astype(int)

            border_frame_top = self.marks[-1].astype(int)
        else:
            # for all other frames
            # find limit values that are smaller than current / same size
            values_smaller = np.where(
                self.marks <= self._current_frame, self.marks, -10
            )

            # check which values have already initialized interpolation values and choose closest to current
            smaller_values_available = np.intersect1d(
                values_smaller, list(self.dict_transform.keys())
            )
            border_frame_bottom = sorted(
                smaller_values_available,
                key=lambda x: int(x),
            )[-1].astype(int)

            # find limit values that are bigger than current
            arg_bigger = np.where(self.marks > self._current_frame, self.marks, -10)

            # check which values have already initialized interpolation factors and choose closest to current
            smaller_values_available = np.intersect1d(
                arg_bigger, list(self.dict_transform.keys())
            )
            border_frame_top = sorted(
                smaller_values_available,
                key=lambda x: int(x),
            )[
                0
            ].astype(int)

        # calculate interpolation factor
        interpolation_factor = (self._current_frame - border_frame_bottom) / (
            border_frame_top - border_frame_bottom
        )

        # calculate interpolated values with interpolation factor
        lerped_x_trans = transforms.lerp(
            self.dict_transform[f"{border_frame_bottom}"][0],
            self.dict_transform[f"{border_frame_top}"][0],
            interpolation_factor,
        )
        lerped_y_trans = transforms.lerp(
            self.dict_transform[f"{border_frame_bottom}"][1],
            self.dict_transform[f"{border_frame_top}"][1],
            interpolation_factor,
        )
        lerped_scale = transforms.lerp(
            self.dict_transform[f"{border_frame_bottom}"][2],
            self.dict_transform[f"{border_frame_top}"][2],
            interpolation_factor,
        )
        lerped_rot = transforms.lerp(
            self.dict_transform[f"{border_frame_bottom}"][3],
            self.dict_transform[f"{border_frame_top}"][3],
            interpolation_factor,
        )

        # set the interpolated values
        self._polygon_pointer.setScale(lerped_scale)
        self._polygon_pointer.setRotation(lerped_rot)
        self._polygon_pointer.setPos(lerped_x_trans, lerped_y_trans)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.toggle_zoom_mode()
            return

        if event.key() == QtCore.Qt.Key_I:
            self.upscale()
        elif event.key() == QtCore.Qt.Key_K:
            self.downscale()
        elif event.key() == QtCore.Qt.Key_L:
            self.rotateClockwise()
        elif event.key() == QtCore.Qt.Key_J:
            self.rotateAntiClockwise()

        elif event.key() == QtCore.Qt.Key_W:
            self.move_up()
        elif event.key() == QtCore.Qt.Key_A:
            self.move_left()
        elif event.key() == QtCore.Qt.Key_S:
            self.move_down()
        elif event.key() == QtCore.Qt.Key_D:
            self.move_right()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_view()

    def add_polygon(self, polygon: QPolygonF) -> None:
        if self._polygon_pointer:
            self.scene().removeItem(self._polygon_pointer)

        self._polygon_pointer = self.scene().addPolygon(
            polygon, self._polygonpen, self._polygonbrush
        )

    def change_frame(self, frame: int) -> None:
        self._current_frame = frame
        self.redraw_from_dictionary()

    def next_frame(self) -> None:
        if self._current_frame == self._num_frames - 1:
            return

        self._current_frame += 1
        self.redraw_from_dictionary()

    def update_signal_dictionary_update(self, dictionary):
        self.dict_transform = dictionary

    def update_signal_current_marks(self, marks):
        self.marks = marks
