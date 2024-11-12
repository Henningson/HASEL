import VFLabel.gui.zoomableViewWidget as zoomableViewWidget

from enum import Enum
from typing import List
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor
from PyQt5.QtWidgets import QGraphicsView, QMenu, QGraphicsEllipseItem
import PyQt5.QtCore
import PyQt5.Qt


class DRAW_MODE(Enum):
    OFF = 0
    ON = 1


class DrawSegmentationWidget(zoomableViewWidget.ZoomableViewWidget):

    def __init__(self, parent=None, image_height: int = 512, image_width: int = 256):
        super(DrawSegmentationWidget, self).__init__(parent)
        self._draw_mode = DRAW_MODE.OFF

        self._pointpen = QPen(QColor(128, 255, 128, 255))
        self._pointbrush = QBrush(QColor(128, 255, 128, 128))

        self._polygonpen = QPen(QColor(255, 128, 128, 255))
        self._polygonbrush = QBrush(QColor(200, 128, 128, 128))

        self._pointsize: int = 10

        self._polygon_points: List[QPointF] = []

        self._polygon_items: List[QGraphicsEllipseItem] = []
        self._polygon_pointer: QPolygonF = None

        self._image_height: int = image_height
        self._image_width: int = image_width

    def wheelEvent(self, event) -> None:
        mouse = event.angleDelta().y() / 120

        if mouse > 0:
            self.zoomIn()
        else:
            self.zoomOut()

    def keyPressEvent(self, event) -> None:
        if event.key() == PyQt5.QtCore.Qt.Key_E:
            self.toggle_draw_mode()

        if self._draw_mode == DRAW_MODE.ON:
            if event.key() == PyQt5.QtCore.Qt.Key_R:
                self.remove_last_point()

    def mousePressEvent(self, event) -> None:
        super(DrawSegmentationWidget, self).mousePressEvent(event)

        if self._draw_mode == DRAW_MODE.ON:
            global_pos = event.pos()
            pos = self.mapToScene(global_pos)
            self.add_point(pos)

    def contextMenuEvent(self, event) -> None:
        """
        Opens a context menu with options for zooming in and out.

        :param event: The QContextMenuEvent containing information about the context menu event.
        :type event: QContextMenuEvent
        """
        menu = QMenu()
        menu.addAction("Zoom in               MouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out              MouseWheel Down", self.zoomOut)
        menu.addAction("Toggle Edit Mode      E", self.toggle_draw_mode)
        menu.addAction("Draw Mode ON", self.draw_mode_on)
        menu.addAction("Draw Mode OFF", self.draw_mode_off)
        menu.addAction("Remove Point          R", self.remove_last_point)
        menu.addAction("Reset View", self.zoomReset)
        menu.exec_(event.globalPos())

    def toggle_draw_mode(self) -> None:
        if self._draw_mode == DRAW_MODE.OFF:
            self._draw_mode = DRAW_MODE.ON
        elif self._draw_mode == DRAW_MODE.ON:
            self._draw_mode = DRAW_MODE.OFF
        else:
            raise ValueError()

    def draw_mode_on(self) -> None:
        self._draw_mode = DRAW_MODE.ON

    def draw_mode_off(self) -> None:
        self._draw_mode = DRAW_MODE.OFF

    def get_draw_mode(self) -> DRAW_MODE:
        return self._draw_mode

    def remove_last_point(self) -> None:
        if len(self._polygon_points) == 0:
            return

        self._polygon_points.pop()
        point_pointer = self._polygon_items.pop()
        self.scene().removeItem(point_pointer)

        if len(self._polygon_points) > 2:
            self.add_polygon(QPolygonF(self._polygon_points))
        else:
            self.remove_polygon()

    def remove_polygon(self) -> None:
        if self._polygon_pointer:
            self.scene().removeItem(self._polygon_pointer)

    def add_point(self, point: QPointF) -> None:

        if point.x() < 0 or point.x() >= self._image_width:
            return

        if point.y() < 0 or point.y() >= self._image_height:
            return

        # The actual points
        self._polygon_points.append(point)

        # Transformed point, such that ellipse center is at mouse position
        ellipse_item = self.scene().addEllipse(
            point.x() - self._pointsize / 2,
            point.y() - self._pointsize / 2,
            self._pointsize,
            self._pointsize,
            self._pointpen,
            self._pointbrush,
        )
        self._polygon_items.append(ellipse_item)

        if len(self._polygon_points) > 2:
            self.add_polygon(QPolygonF(self._polygon_points))

    def add_polygon(self, polygon: QPolygonF) -> None:
        if self._polygon_pointer:
            self.scene().removeItem(self._polygon_pointer)

        self._polygon_pointer = self.scene().addPolygon(
            polygon, self._polygonpen, self._polygonbrush
        )
