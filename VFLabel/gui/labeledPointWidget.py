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

from cotracker.utils.visualizer import Visualizer, read_video_from_path


class LabeledPointWidget(videoViewWidget.VideoViewWidget):
    point_added = pyqtSignal()

    def __init__(
        self,
        video: List[QImage],
        grid_width: int = 18,
        grid_height: int = 18,
        parent=None,
    ):
        super(LabeledPointWidget, self).__init__(video, parent)
        self._visible_pointpen = QPen(QColor(128, 255, 128, 255))
        self._visible_pointbrush = QBrush(QColor(128, 255, 128, 128))

        self._garbage_pointpen = QPen(QColor(255, 128, 128, 255))
        self._garbage_pointbrush = QBrush(QColor(255, 128, 128, 128))

        self._pointsize: int = 5

        self._point_items: List[QGraphicsEllipseItem] = []

        self._image_width = video[0].width()
        self._image_height = video[0].height()

        # Point positions is 4D Numpy array of size
        # CYCLE_LENGTH x GRID_HEIGHT x GRID_WIDTH x 2
        # For each frame, we can have at max grid_height*grid_width indices with 2 positions each.
        # That should make it really easy to assign points to their specific laser index.
        # Everything is indexed as nan at first. Makes it easy to find already set points.
        self.point_positions = (
            np.zeros([len(video), grid_height, grid_width, 2]) * np.nan
        )
        self.point_labels = np.zeros([len(video), grid_height, grid_width]) * np.nan
        self.y_index: int = None
        self.x_index: int = None
        self._current_frame = 0

    def keyPressEvent(self, event) -> None:
        self.change_frame(self._current_frame + 1)

    def mousePressEvent(self, event) -> None:
        global_pos = event.pos()
        pos = self.mapToScene(global_pos)

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
        menu.exec_(event.globalPos())

    def redraw(self) -> None:
        if self.images:
            self.set_image(self.images[self._current_frame])

        for point_item in self._point_items:
            self.scene().removeItem(point_item)
        self._point_items = []

        # Get current frame indices:
        points_at_current_frame = self.point_positions[self._current_frame]
        labels_at_current_frame = self.point_labels[self._current_frame].flatten()

        for point, label in zip(points_at_current_frame, labels_at_current_frame):
            if np.isnan(point).any():
                continue

            pen = self._visible_pointpen if label == 1 else self._garbage_pointpen
            brush = self._visible_pointbrush if label == 1 else self._garbage_pointbrush

            ellipse_item = self.scene().addEllipse(
                point[0] - self._pointsize / 2,
                point[1] - self._pointsize / 2,
                self._pointsize,
                self._pointsize,
                pen,
                brush,
            )
            self._point_items.append(ellipse_item)

    def add_points_and_classes(self, points: np.array, labels: np.array) -> None:
        self.point_positions = points
        self.point_labels = labels
        self.redraw()

    def get_point_indices(self, frame_index: int) -> np.array:
        mask = ~np.isnan(self.point_positions[frame_index]).any(axis=-1)

        # Get x, y indices of valid points
        return np.argwhere(mask)

    def get_point_indices_at_current(self) -> np.array:
        return self.get_point_indices(self._current_frame)
