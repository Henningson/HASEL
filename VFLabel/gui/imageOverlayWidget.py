import VFLabel.gui.zoomableViewWidget as zoomableViewWidget
import VFLabel.gui.videoViewWidget as videoViewWidget
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


class ImageOverlayWidget(videoViewWidget.VideoViewWidget):
    def __init__(
        self,
        images: List[QImage],
        overlay_images: List[QImage],
        opacity: float = 0.8,
        parent=None,
    ):
        super(ImageOverlayWidget, self).__init__(images, parent)

        self.overlay_images = overlay_images
        self._overlay_pointer = None

        self._opacity = opacity
        self._opacity_delta = 0.05

        if self.overlay_images:
            self.set_overlay(self.overlay_images[0])

    def contextMenuEvent(self, event) -> None:
        """
        Opens a context menu with options for zooming in and out.

        :param event: The QContextMenuEvent containing information about the context menu event.
        :type event: QContextMenuEvent
        """
        menu = QMenu()
        menu.addAction("Zoom in               MouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out              MouseWheel Down", self.zoomOut)
        menu.addAction("Increase Opacity      +", self.increaseOpacity)
        menu.addAction("Decrease Opactiy      -", self.decreaseOpacity)
        menu.exec_(event.globalPos())

    def increaseOpacity(self) -> None:
        self._opacity += self._opacity_delta

        if self._opactiy > 1.0:
            self._opactiy = 1.0

    def decreaseOpacity(self) -> None:
        self._opacity -= self._opacity_delta

        if self._opactiy < 0.0:
            self._opactiy = 0.0

    def redraw(self) -> None:
        self.set_image(self.images[self._current_frame])

        if self.overlay_images:
            self.set_overlay(self.overlay_images[self._current_frame])

    def change_frame(self, frame: int) -> None:
        self._current_frame = frame
        self.redraw()

    def set_opacity(self, opacity: float) -> None:
        self._opacity = opacity
        self.redraw()

    def set_overlay(self, overlay_image: QImage) -> None:
        """
        Updates the overlay image.
        """

        if self.scene().items() and self._overlay_pointer:
            self.scene().removeItem(self._overlay_pointer)

        pixmap = QPixmap(overlay_image)
        self._overlay_pointer = self.scene().addPixmap(pixmap)
        self._overlay_pointer.setOpacity(self._opacity)
