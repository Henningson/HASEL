from typing import List

import numpy as np
from PyQt5.QtGui import QColor, QImage, QPen, QKeySequence
from PyQt5.QtWidgets import QMenu

import VFLabel.gui.videoOverlayWidget as videoOverlayWidget


class VideoOverlayGlottalMidlineWidget(videoOverlayWidget.VideoOverlayWidget):
    def __init__(
        self,
        images: List[QImage],
        overlay_images: List[QImage] = None,
        glottal_midlines: List[np.array] = None,
        opacity: float = 0.8,
        parent=None,
    ):
        super(VideoOverlayGlottalMidlineWidget, self).__init__(
            images, overlay_images, opacity, parent
        )

        self.glottal_midlines = glottal_midlines
        self._glottal_midline_pointer = None

        if self.glottal_midlines:
            self.set_glottal_midline(self.glottal_midlines["Frame0"])

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
        menu.addAction("Reset Zoom", self.zoomReset)
        menu.exec_(event.globalPos())

    def keyPressEvent(self, event) -> None:
        if event.key() == QKeySequence("+"):
            self.increaseOpacity()

        if event.key() == QKeySequence("-"):
            self.decreaseOpacity()

    def redraw(self) -> None:
        if self.images:
            self.set_image(self.images[self._current_frame])

        if self.overlay_images:
            self.set_overlay(self.overlay_images[self._current_frame])

        if self.glottal_midlines:
            self.set_glottal_midline(
                self.glottal_midlines["Frame" + str(self._current_frame)]
            )

    def set_glottal_midline(self, glottal_midline) -> None:
        """
        Updates the overlay image.
        """

        if self.scene().items() and self._glottal_midline_pointer:
            self.scene().removeItem(self._glottal_midline_pointer)

        upper_point = glottal_midline["Upper"]
        lower_point = glottal_midline["Lower"]

        pen = QPen(QColor(255, 255, 255, 255))
        self._glottal_midline_pointer = self.scene().addLine(
            upper_point[0], upper_point[1], lower_point[0], lower_point[1], pen
        )
        self._glottal_midline_pointer.setOpacity(self._opacity)

    def set_glottal_midlines_array(self, glottal_midline_array) -> None:
        self.glottal_midlines = glottal_midline_array
