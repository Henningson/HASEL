from typing import List

from PyQt5 import QtCore
from PyQt5.QtCore import QPointF, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QImage, QPen, QPolygonF
from PyQt5.QtWidgets import QMenu

import VFLabel.gui_graphics_view.zoomable as zoomableViewWidget


class TransformableSegmentation(zoomableViewWidget.Zoomable):
    transform_updated = pyqtSignal()
    signal_current_image = pyqtSignal(int)

    def __init__(self, image: QImage, polygon_points: List[QPointF], parent=None):
        super(TransformableSegmentation, self).__init__(parent)
        self._polygonpen = QPen(QColor(255, 128, 128, 255))
        self._polygonbrush = QBrush(QColor(200, 128, 128, 128))

        self.set_image(
            image,
        )

        self._polygon_pointer = None
        if polygon_points:
            self.add_polygon(QPolygonF(polygon_points))

        self.scale = 1.0
        self.rotation_angle = 0.0
        self.x_translation = 0.0
        self.y_translation = 0.0

        self._zoom_mode: bool = True

    def mousePressEvent(self, event) -> None:
        super(TransformableSegmentation, self).mousePressEvent(event)
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
        menu.addAction("Zoom in\tMouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out\tMouseWheel Down", self.zoomOut)
        menu.addAction("Toggle Zoom-Mode\tt", self.toggle_zoom_mode)
        menu.addAction("Upscale\ti", self.upscale)
        menu.addAction("Downscale\tk", self.downscale)
        menu.addAction("Rotate Clockwise\tl", self.rotateClockwise)
        menu.addAction("Rotate Anticlockwise\tj", self.rotateAntiClockwise)
        menu.addAction("Move Up\tw", self.move_up)
        menu.addAction("Move Down\ts", self.move_down)
        menu.addAction("Move Left\ta", self.move_left)
        menu.addAction("Move Right\td", self.move_right)
        menu.addAction("Reset Zoom", self.zoomReset)
        menu.exec_(event.globalPos())

    def toggle_zoom_mode(self) -> None:
        self._zoom_mode = not self._zoom_mode

    def get_transform(self) -> List[float]:
        return self.x_translation, self.y_translation, self.scale, self.rotation_angle

    def set_transform(
        self, x_translation: int, y_translation: int, scale: int, rotation_angle: int
    ):
        self.x_translation = x_translation
        self.y_translation = y_translation
        self.scale = scale
        self.rotation_angle = rotation_angle

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

        self.transform_updated.emit()
        self.signal_current_image.emit(self.current_image_number)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.toggle_zoom_mode()
            return
        # TODO: in context menu mit shortcut T, zusätzlich?

        if event.key() == QtCore.Qt.Key_T:
            self.toggle_zoom_mode()
        elif event.key() == QtCore.Qt.Key_I:
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

    def update_signal_current_move_window_frame_number(self, current_frame):
        self.current_image_number = current_frame
