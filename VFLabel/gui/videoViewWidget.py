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


class VideoViewWidget(zoomableViewWidget.ZoomableViewWidget):
    def __init__(
        self,
        images: List[QImage] = None,
        parent=None,
    ):
        super(VideoViewWidget, self).__init__(parent)
        self.images = images

        if self.images:
            self.set_image(self.images[0])

        self._current_frame: int = 0
        self._num_frames = len(self.images) if self.images else 0

    def redraw(self) -> None:
        if self.images:
            self.set_image(self.images[self._current_frame])

    def change_frame(self, frame: int) -> None:
        self._current_frame = frame
        self.redraw()

    def add_video(self, video: List[QImage]) -> None:
        self.images = video
        self._num_frames = len(self.images)
