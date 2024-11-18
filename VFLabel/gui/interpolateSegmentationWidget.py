import VFLabel.gui.zoomableViewWidget as zoomableViewWidget
import VFLabel.utils.enums as enums
import VFLabel.utils.transforms as transforms

from typing import List
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor
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

        scene = QGraphicsScene(self)
        self.setScene(scene)

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

    def generate_segmentations(self) -> List[np.array]:
        # TODO: Implement me
        return np.zeros(3)

    def redraw(self, frame_num: int) -> None:
        if frame_num < 0 or frame_num > self._num_frames - 1:
            return

        self.set_image(self.frames[self._current_frame])

        if not self._polygon_pointer:
            return

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

    def add_polygon(self, polygon: QPolygonF) -> None:
        if self._polygon_pointer:
            self.scene().removeItem(self._polygon_pointer)

        self._polygon_pointer = self.scene().addPolygon(
            polygon, self._polygonpen, self._polygonbrush
        )

    def next_frame(self) -> None:
        if self._current_frame == self._num_frames - 1:
            return

        self._current_frame += 1
        self.redraw(self._current_frame)
