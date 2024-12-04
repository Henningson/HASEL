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


class CropAndSPPWidget(videoViewWidget.VideoViewWidget):
    def __init__(
        self,
        video: List[QImage],
        points: np.array,
        parent=None,
    ):
        super(CropAndSPPWidget, self).__init__(video, parent)

        self._pointpen = QPen(QColor(128, 255, 128, 255))
        self._pointbrush = QBrush(QColor(128, 255, 128, 128))

        self._pointsize: int = 0.3

        self._point_items: List[QGraphicsEllipseItem] = []

        self._image_width = video[0].width()
        self._image_height = video[0].height()

        self.point_positions = points

        # Point visibilities also is a 4D Numpy array of size
        # CYCLE_LENGTH x GRID_HEIGHT x GRID_WIDTH

        self.point_visibilities = None
        self.y_index: int = None
        self.x_index: int = None

    def contextMenuEvent(self, event) -> None:
        """
        Opens a context menu with options for zooming in and out.

        :param event: The QContextMenuEvent containing information about the context menu event.
        :type event: QContextMenuEvent
        """
        menu = QMenu()
        menu.addAction("Zoom in               MouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out              MouseWheel Down", self.zoomOut)
        menu.addAction("Reset View", self.zoomReset)
        menu.addAction("Fit View", self.fit_view)
        menu.exec_(event.globalPos())

    def redraw(self) -> None:
        if self.images:
            self.set_image(self.images[self._current_frame])

        for point_item in self._point_items:
            self.scene().removeItem(point_item)
        self._point_items = []

        # Get current frame indices:
        point = self.point_positions[self._current_frame]

        if (point == np.nan).any():
            return

        ellipse_item = self.scene().addEllipse(
            point[0] - self._pointsize / 2,
            point[1] - self._pointsize / 2,
            self._pointsize,
            self._pointsize,
            self._pointpen,
            self._pointbrush,
        )
        self._point_items.append(ellipse_item)
        self.fit_view()

    def keyPressEvent(self, event) -> None:
        self.change_frame(self._current_frame + 1)
        self.fit_view()
