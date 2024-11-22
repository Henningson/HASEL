import VFLabel.gui.videoViewWidget as videoViewWidget
import VFLabel.utils.enums as enums
import numpy as np

from typing import List
from PyQt5.QtCore import QPointF, pyqtSignal
from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor, QImage
from PyQt5.QtWidgets import QGraphicsView, QMenu, QGraphicsEllipseItem, QMessageBox
import PyQt5.QtCore
import PyQt5.Qt
from typing import List


class PointClickWidget(videoViewWidget.VideoViewWidget):
    point_added = pyqtSignal()

    def __init__(
        self,
        video: List[QImage],
        grid_width: int = 18,
        grid_height: int = 18,
        parent=None,
    ):
        super(PointClickWidget, self).__init__(video, parent)
        self._draw_mode = enums.DRAW_MODE.OFF
        self._remove_mode = enums.DRAW_MODE.OFF

        self._pointpen = QPen(QColor(128, 255, 128, 255))
        self._pointbrush = QBrush(QColor(128, 255, 128, 128))

        self._pointsize: int = 10

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
        self.y_index: int = None
        self.x_index: int = None

    def keyPressEvent(self, event) -> None:
        if event.key() == PyQt5.QtCore.Qt.Key_E:
            self.toggle_draw_mode()

    def mousePressEvent(self, event) -> None:
        super(PointClickWidget, self).mousePressEvent(event)
        global_pos = event.pos()
        pos = self.mapToScene(global_pos)

        if self._draw_mode == enums.DRAW_MODE.ON:
            self.add_point(pos)
            return

        if self._remove_mode == enums.REMOVE_MODE.ON:
            self.remove_point(pos)
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
        menu.addAction("Toggle Edit Mode      E", self.toggle_draw_mode)
        menu.addAction("Draw Mode ON", self.draw_mode_on)
        menu.addAction("Draw Mode OFF", self.draw_mode_off)
        menu.addAction("Remove Point          R", self.remove_last_point)
        menu.addAction("Reset View", self.zoomReset)
        menu.exec_(event.globalPos())

    def toggle_remove_mode(self) -> None:
        self._draw_mode = enums.DRAW_MODE.OFF

        if self._remove_mode == enums.REMOVE_MODE.OFF:
            self._remove_mode = enums.REMOVE_MODE.ON
        elif self._remove_mode == enums.REMOVE_MODE.ON:
            self._remove_mode = enums.REMOVE_MODE.OFF
        else:
            raise ValueError()

    def toggle_draw_mode(self) -> None:
        self._remove_mode = enums.REMOVE_MODE.OFF

        if self._draw_mode == enums.DRAW_MODE.OFF:
            self._draw_mode = enums.DRAW_MODE.ON
        elif self._draw_mode == enums.DRAW_MODE.ON:
            self._draw_mode = enums.DRAW_MODE.OFF
        else:
            raise ValueError()

    def DRAW_MODE_on(self) -> None:
        self.setDragMode(QGraphicsView.NoDrag)
        self._draw_mode = enums.DRAW_MODE.ON

    def DRAW_MODE_off(self) -> None:
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._draw_mode = enums.DRAW_MODE.OFF

    def REMOVE_MODE_on(self) -> None:
        self.setDragMode(QGraphicsView.NoDrag)
        self._remove_mode = enums.REMOVE_MODE.ON

    def REMOVE_MODE_off(self) -> None:
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._remove_mode = enums.REMOVE_MODE.OFF

    def get_draw_mode(self) -> enums.DRAW_MODE:
        return self._draw_mode

    def get_remove_mode(self) -> enums.REMOVE_MODE:
        return self._remove_mode

    def remove_point(self, point: QPointF) -> None:
        clicked_item = self.scene().itemAt(point, self.transform())

        if clicked_item in self._point_items:
            self.scene().removeItem(clicked_item)
            self._point_items.remove(clicked_item)

    def add_point(self, point: QPointF) -> None:
        if not self.y_index or not self.x_index:
            msgWarning = QMessageBox()
            msgWarning.setText(
                "Please select a laser beam that corresponds to the laser point you want to label from the grid."
            )
            msgWarning.setIcon(QMessageBox.Warning)
            msgWarning.setWindowTitle("Caution")
            msgWarning.exec()
            return

        if point.x() < 0 or point.x() >= self._image_width:
            return

        if point.y() < 0 or point.y() >= self._image_height:
            return

        self.point_positions[self._current_frame, self.y_index, self.x_index] = [
            point.x(),
            point.y(),
        ]

        # Transformed point, such that ellipse center is at mouse position
        ellipse_item = self.scene().addEllipse(
            point.x() - self._pointsize / 2,
            point.y() - self._pointsize / 2,
            self._pointsize,
            self._pointsize,
            self._pointpen,
            self._pointbrush,
        )
        self._point_items.append(ellipse_item)
        self.point_added.emit()

    def set_laser_index(self, x: int, y: int) -> None:
        self.y_index = y
        self.x_index = x

    def redraw(self) -> None:
        if self.images:
            self.set_image(self.images[self._current_frame])

        for point_item in self._point_items:
            self.scene().removeItem(point_item)
        self._point_items = []

        # Get current frame indices:
        points_at_current_frame = self.point_positions[self._current_frame]
        points_at_current_frame = points_at_current_frame.reshape(-1, 2)
        filtered_points = points_at_current_frame[
            ~np.isnan(points_at_current_frame).any(axis=1)
        ]
        for point in filtered_points:
            ellipse_item = self.scene().addEllipse(
                point[0] - self._pointsize / 2,
                point[1] - self._pointsize / 2,
                self._pointsize,
                self._pointsize,
                self._pointpen,
                self._pointbrush,
            )
            self._point_items.append(ellipse_item)

    def get_point_indices(self, frame_index: int) -> np.array:
        mask = ~np.isnan(self.point_positions[frame_index]).any(axis=-1)

        # Get x, y indices of valid points
        return np.argwhere(mask)

    def get_point_indices_at_current(self) -> np.array:
        return self.get_ok_point_indices(self._current_frame)
