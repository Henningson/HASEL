import VFLabel.gui.videoViewWidget as videoViewWidget
import VFLabel.utils.enums as enums
import VFLabel.gui.ellipseWithID as ellipseWithID
import numpy as np

from typing import List
from PyQt5.QtCore import QPointF, pyqtSignal
from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor, QImage, QCursor
from PyQt5.QtWidgets import QGraphicsView, QMenu, QGraphicsEllipseItem, QMessageBox
import PyQt5.QtCore
import PyQt5.Qt
from typing import List


class PointViewWidget(videoViewWidget.VideoViewWidget):
    point_added = pyqtSignal()

    def __init__(
        self,
        video: List[QImage],
        parent=None,
    ):
        super(PointViewWidget, self).__init__(video, parent)
        self._draw_mode = enums.DRAW_MODE.OFF
        self._remove_mode = enums.DRAW_MODE.OFF

        self._pointpen = QPen(QColor(128, 255, 128, 255))
        self._pointbrush = QBrush(QColor(128, 255, 128, 128))

        self._pointsize: int = 5

        self._point_items: List[QGraphicsEllipseItem] = []

        self._image_width = video[0].width()
        self._image_height = video[0].height()

        # Point positions is 4D Numpy array of size
        # CYCLE_LENGTH x GRID_HEIGHT x GRID_WIDTH x 2
        # For each frame, we can have at max grid_height*grid_width indices with 2 positions each.
        # That should make it really easy to assign points to their specific laser index.
        # Everything is indexed as nan at first. Makes it easy to find already set points.
        self.point_positions = None

        # Point visibilities also is a 4D Numpy array of size
        # CYCLE_LENGTH x GRID_HEIGHT x GRID_WIDTH

        self.point_visibilities = None
        self.y_index: int = None
        self.x_index: int = None

        self._draw_mode = enums.DRAW_MODE.OFF
        self._remove_mode = enums.REMOVE_MODE.OFF

    def add_points(self, points_per_frame: np.array) -> None:
        self.point_positions = points_per_frame
        self.redraw()

    def add_point_visibilities(self, visibility_per_point: np.array) -> None:
        self.point_visibilities = visibility_per_point

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

    def enterEvent(self, event):
        super(PointViewWidget, self).enterEvent(event)
        self.setCursor(QCursor(PyQt5.QtCore.Qt.CrossCursor))

    def mouseReleaseEvent(self, event):
        super(PointViewWidget, self).mouseReleaseEvent(event)
        self.setCursor(QCursor(PyQt5.QtCore.Qt.CrossCursor))

    def redraw(self) -> None:
        if self.images:
            self.set_image(self.images[self._current_frame])

        for point_item in self._point_items:
            self.scene().removeItem(point_item)
        self._point_items = []

        # Get current frame indices:
        points_at_current_frame = self.point_positions[self._current_frame]
        # visibilities_at_current_frame = self.point_positions[self._current_frame]
        for point in points_at_current_frame:
            ellipse_item = self.scene().addEllipse(
                point[0] - self._pointsize / 2,
                point[1] - self._pointsize / 2,
                self._pointsize,
                self._pointsize,
                self._pointpen,
                self._pointbrush,
            )
            self._point_items.append(ellipse_item)
