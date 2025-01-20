from typing import List

from PyQt5.QtGui import QImage

import VFLabel.gui.zoomableViewWidget as zoomableViewWidget


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
        self._num_frames: int = len(self.images) if self.images else 0

    def redraw(self) -> None:
        if self.images:
            self.set_image(self.images[self._current_frame])

    def change_frame(self, frame: int) -> None:
        if frame < 0 or frame >= self._num_frames:
            return

        self._current_frame = frame
        self.redraw()

    def add_video(self, video: List[QImage]) -> None:
        self.images = video
        self._num_frames = len(self.images)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_view()
