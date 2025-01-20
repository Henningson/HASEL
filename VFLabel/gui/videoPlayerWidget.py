from PyQt5 import QtCore
from PyQt5.QtCore import QRect, QTimer
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QSlider, QWidget


class VideoPlayerWidget(QWidget):

    signal_current_frame = QtCore.pyqtSignal(int)

    def __init__(self, video_length: int = 0, timer_interval: int = 25, parent=None):
        super(VideoPlayerWidget, self).__init__(parent)

        self._play: bool = False
        self._video_length: int = video_length
        self._current_frame: int = 0
        self._replay: bool = False

        self.timer = QTimer()
        self._timer_interval: int = timer_interval
        # Button definitions
        self.slider = QSlider()
        self.slider.setMinimum(0)
        self.slider.setMaximum(video_length - 1)
        self.slider.setValue(0)
        self.slider.setGeometry(QRect(190, 100, 160, 16))
        self.slider.setOrientation(QtCore.Qt.Horizontal)

        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")

        self.play_button.clicked.connect(self.play)
        self.pause_button.clicked.connect(self.pause)
        self.stop_button.clicked.connect(self.stop)
        self.slider.sliderPressed.connect(self.pause)
        self.slider.sliderReleased.connect(self.update_current_from_slider)
        self.timer.timeout.connect(self.increment_frame)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.slider)
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)
        self.setLayout(button_layout)

    def play(self) -> None:
        self._play = True
        self.timer.start(self._timer_interval)

    def pause(self) -> None:
        self._play = False
        self.timer.stop()

    def stop(self) -> None:
        self._play = False
        self.timer.stop()
        self._current_frame = 0
        self.update_slider()

    def value(self) -> int:
        return self.slider.value()

    def decrement_frame(self, force: bool = False) -> None:
        if not force and not self._play:
            return

        if self._current_frame == 0:
            return

        self._current_frame += 1
        self.update_slider()

    def increment_frame(self, force: bool = False) -> None:
        if not force and not self._play:
            return

        if self._current_frame == self._video_length - 1:
            if self._replay:
                self._current_frame = 0
                self.update_slider()
            else:
                self.pause()
                return

        self._current_frame += 1
        self.update_slider()

    def update_slider(self):
        self.slider.setValue(self._current_frame)
        self.signal_current_frame.emit(self._current_frame)

    def update_current_from_slider(self):
        self._current_frame = self.slider.value()
        self.signal_current_frame.emit(self._current_frame)

    def get_video_length(self) -> int:
        return self._video_length
