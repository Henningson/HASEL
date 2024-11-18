import VFLabel.gui.zoomableViewWidget as zoomableViewWidget
import VFLabel.utils.enums as enums

from typing import List
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor
from PyQt5.QtWidgets import QGraphicsView, QMenu, QGraphicsEllipseItem, QGraphicsScene
from PyQt5 import QtCore
from PyQt5.QtGui import QImage
import PyQt5.Qt
import numpy as np


class TransformSegmentationWidget(zoomableViewWidget.ZoomableViewWidget):
    def __init__(self, image: QImage, polygon_points: List[QPointF], parent=None):
        super(TransformSegmentationWidget, self).__init__(parent)
        self._polygonpen = QPen(QColor(255, 128, 128, 255))
        self._polygonbrush = QBrush(QColor(200, 128, 128, 128))

        scene = QGraphicsScene(self)
        self.setScene(scene)

        self.set_image(
            image,
        )

        self._polygon_pointer = None
        self.add_polygon(QPolygonF(polygon_points))

        self.scale = 1.0
        self.rotation_angle = 0.0
        self.x_translation = 0.0
        self.y_translation = 0.0

        self._zoom_mode: bool = True

        self.final_transform = {
            "scale": 0.0,
            "translation": [0.0, 0.0],
            "rotation": 0.0,
        }

    def mousePressEvent(self, event) -> None:
        super(TransformSegmentationWidget, self).mousePressEvent(event)
        # Do nothing

    def wheelEvent(self, event) -> None:
        mouse = event.angleDelta().y() / 120

        if self._zoom_mode:
            if mouse > 0:
                self.zoomIn()
            else:
                self.zoomOut()
            return

        if mouse > 0:
            self.rotateClockwise()
        else:
            self.rotateAntiClockwise()

    def contextMenuEvent(self, event) -> None:
        """
        Opens a context menu with options for zooming in and out.

        :param event: The QContextMenuEvent containing information about the context menu event.
        :type event: QContextMenuEvent
        """
        menu = QMenu()
        menu.addAction("Zoom in               MouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out              MouseWheel Down", self.zoomOut)
        menu.addAction("Toggle Zoom-Mode T", self.toggle_zoom_mode)
        menu.addAction("Upscale", self.upscale)
        menu.addAction("Downscale", self.downscale)
        menu.addAction("Rotate Clockwise", self.rotateClockwise)
        menu.addAction("Rotate Anticlockwise", self.rotateAntiClockwise)
        menu.addAction("Move Up", self.move_up)
        menu.addAction("Move Down", self.move_down)
        menu.addAction("Move Left", self.move_left)
        menu.addAction("Move Right", self.move_right)
        menu.exec_(event.globalPos())

    def toggle_zoom_mode(self) -> None:
        self._zoom_mode = not self._zoom_mode
        print(f"Zoom Mode: {self._zoom_mode}")

    def get_transform(self) -> List[float, float, float, float]:
        return self.x_translation, self.y_translation, self.scale, self.rotation_angle

    def downscale(self):
        self.scale -= 0.01
        self.redraw()

    def upscale(self):
        self.scale += 0.01
        self.redraw()

    def rotateClockwise(self):
        self.rotation_angle += 0.1
        self.redraw()

    def rotateAntiClockwise(self):
        self.rotation_angle -= 0.1
        self.redraw()

    def move_right(self):
        self.x_translation += 1.0
        self.redraw()

    def move_left(self):
        self.x_translation -= 1.0
        self.redraw()

    def move_down(self):
        self.y_translation += 1.0
        self.redraw()

    def move_up(self):
        self.y_translation -= 1.0
        self.redraw()

    def reset(self) -> None:
        self.scale = 1.0
        self.rotation_angle = 0.0
        self.x_translation = 0.0
        self.y_translation = 0.0
        self.redraw()

    def redraw(self) -> None:
        self._polygon_pointer.setTransformOriginPoint(
            self._polygon_pointer.boundingRect().center()
        )

        self._polygon_pointer.setScale(self.scale)
        self._polygon_pointer.setRotation(self.rotation_angle)
        self._polygon_pointer.setPos(self.x_translation, self.y_translation)

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
