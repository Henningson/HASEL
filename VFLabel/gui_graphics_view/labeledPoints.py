from typing import List

import numpy as np
import PyQt5
from PyQt5.QtGui import QBrush, QColor, QImage, QPen
from PyQt5.QtWidgets import QGraphicsEllipseItem, QMenu
from PyQt5.QtCore import pyqtSignal

import VFLabel.gui_graphics_view.zoomableVideo as zoomableVideo


class LabeledPoints(zoomableVideo.ZoomableVideo):

    signal_increment_frame = pyqtSignal(bool)
    signal_decrement_frame = pyqtSignal(bool)

    def __init__(
        self,
        video: List[QImage],
        grid_width: int = 18,
        grid_height: int = 18,
        parent=None,
    ):
        super(LabeledPoints, self).__init__(video, parent)
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
        if event.key() == PyQt5.QtCore.Qt.Key_Right:
            self.frame_forward()
        elif event.key() == PyQt5.QtCore.Qt.Key_Left:
            self.frame_backward()

    def contextMenuEvent(self, event) -> None:
        """
        Opens a context menu with options for zooming in and out.

        :param event: The QContextMenuEvent containing information about the context menu event.
        :type event: QContextMenuEvent
        """
        menu = QMenu()
        menu.addAction("Zoom in\tMouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out\tMouseWheel Down", self.zoomOut)
        menu.addAction("Frame forward\tRight Arrow", self.frame_forward)
        menu.addAction("Frame backward\tLeft Arrow", self.frame_backward)
        menu.addAction("Reset View", self.zoomReset)
        menu.exec_(event.globalPos())

    def frame_forward(self):
        self.change_frame(self._current_frame + 1)
        self.signal_increment_frame.emit(True)

    def frame_backward(self):
        self.change_frame(self._current_frame - 1)
        self.signal_decrement_frame.emit(True)

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

    def add_points_labels_and_ids(
        self, points: np.array, labels: np.array, ids: np.array
    ) -> None:
        self.point_positions = points
        self.point_labels = labels
        self.point_ids = ids
        self.redraw()

    def get_point_indices(self, frame_index: int) -> np.array:
        mask = ~np.isnan(self.point_positions[frame_index]).any(axis=-1)

        # Get x, y indices of valid points
        return np.argwhere(mask)

    def get_point_indices_at_current(self) -> np.array:
        return self.get_point_indices(self._current_frame)
