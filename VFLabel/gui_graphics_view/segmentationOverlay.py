from typing import List

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import pyqtSignal

import VFLabel.gui_graphics_view.zoomableVideo as zoomableVideo


class SegmentationOverlay(zoomableVideo.ZoomableVideo):

    signal_opacity_slider = pyqtSignal(int)

    def __init__(
        self,
        images: List[QImage],
        overlay_images: List[QImage] = None,
        opacity: float = 0.8,
        parent=None,
    ):
        super(SegmentationOverlay, self).__init__(images, parent)

        self.overlay_images = overlay_images
        self._overlay_pointer = None

        self._opacity = opacity
        self._opacity_delta = 0.05

        if self.overlay_images:
            self.set_overlay(self.overlay_images[0])
            self.change_opacity_slider()

    def contextMenuEvent(self, event) -> None:
        """
        Opens a context menu with options for zooming in and out.

        :param event: The QContextMenuEvent containing information about the context menu event.
        :type event: QContextMenuEvent
        """
        menu = QMenu()
        menu.addAction("Zoom in\tMouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out\tMouseWheel Down", self.zoomOut)
        menu.addAction("Increase Opacity\t+", self.increaseOpacity)
        menu.addAction("Decrease Opactiy\t-", self.decreaseOpacity)
        menu.exec_(event.globalPos())

    def increaseOpacity(self) -> None:
        self._opacity += self._opacity_delta

        if self._opacity > 1.0:
            self._opacity = 1.0

        self.change_opacity_slider()

    def decreaseOpacity(self) -> None:
        self._opacity -= self._opacity_delta

        if self._opacity < 0.0:
            self._opacity = 0.0

        self.change_opacity_slider()

    def change_opacity_slider(self):
        value = round(self._opacity * 100)
        self.signal_opacity_slider.emit(value)

    def redraw(self) -> None:
        if self.images:
            self.set_image(self.images[self._current_frame])

        if self.overlay_images:
            self.set_overlay(self.overlay_images[self._current_frame])
            self.change_opacity_slider()

    def change_frame(self, frame: int) -> None:
        self._current_frame = frame
        self.redraw()

    def set_opacity(self, opacity: float) -> None:
        self._opacity = opacity
        self.redraw()

    def add_overlay(self, video: List[QImage]) -> None:
        self.overlay_images = video

    def set_overlay(self, overlay_image: QImage) -> None:
        """
        Updates the overlay image.
        """

        if self.scene().items() and self._overlay_pointer:
            self.scene().removeItem(self._overlay_pointer)

        pixmap = QPixmap(overlay_image)
        self._overlay_pointer = self.scene().addPixmap(pixmap)
        self._overlay_pointer.setOpacity(self._opacity)
