from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout


from PyQt5 import QtCore
import numpy as np

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QSlider,
    QPushButton,
    QLabel,
    QFileDialog,
    QComboBox,
    QMessageBox,
)

from PyQt5.QtGui import (
    QIcon,
    QPen,
    QBrush,
    QPolygonF,
    QColor,
    QPixmap,
)
import os

import VFLabel.utils.transforms

import VFLabel.gui.videoPlayerWidget
import VFLabel.gui.videoViewWidget
import VFLabel.gui.zoomableViewWidget

import VFLabel.utils.transforms
import VFLabel.io.data
import VFLabel.utils.utils
import VFLabel.utils.defines

import PyQt5.QtCore

import json

############################### ^
#         #         #         # |
#         #         #         # |
#  VIDEO  #  FIRST  # SECOND  # |
#         #  IMAGE  # IMAGE   # |
#         #         #         # |
#         #         #         # |
############################### |
# Sel1 # Sel2 # VPW # SAVE    # |
############################### v


class SelectCycleView(QWidget):
    def __init__(self, video: np.array, project_path: str, parent=None):
        super(SelectCycleView, self).__init__(parent)
        self.project_path = project_path

        self.video = VFLabel.utils.transforms.vid_2_QImage(video)

        self.video_view = VFLabel.gui.videoViewWidget.VideoViewWidget(self.video)
        self.first_cycle_view = VFLabel.gui.zoomableViewWidget.ZoomableViewWidget()
        self.second_cycle_view = VFLabel.gui.zoomableViewWidget.ZoomableViewWidget()

        black_init = VFLabel.utils.transforms.np_2_QImage(video[0].copy() * 0)
        self.first_cycle_view.set_image(black_init)
        self.first_cycle_view.fit_view()
        self.second_cycle_view.set_image(black_init)
        self.second_cycle_view.fit_view()

        self.cycle_start_index = -1
        self.cycle_end_index = -1

        self.video_player = VFLabel.gui.videoPlayerWidget.VideoPlayerWidget(
            len(self.video), 100
        )

        self.button_cycle_start = QPushButton("Set Cycle Start")
        self.button_cycle_end = QPushButton("Set Cycle End")
        self.save_button = QPushButton("Save")

        # Layouting, signals and slots
        vertical_layout = QVBoxLayout()
        horizontal_layout_top = QHBoxLayout()
        top_widget = QWidget()
        horizontal_layout_bot = QHBoxLayout()
        bot_widget = QWidget()

        horizontal_layout_top.addWidget(self.video_view)
        horizontal_layout_top.addWidget(self.first_cycle_view)
        horizontal_layout_top.addWidget(self.second_cycle_view)
        top_widget.setLayout(horizontal_layout_top)

        horizontal_layout_bot.addWidget(self.button_cycle_start)
        horizontal_layout_bot.addWidget(self.button_cycle_end)
        horizontal_layout_bot.addWidget(self.video_player)
        horizontal_layout_bot.addWidget(self.save_button)
        bot_widget.setLayout(horizontal_layout_bot)

        vertical_layout.addWidget(top_widget)
        vertical_layout.addWidget(bot_widget)
        self.setLayout(vertical_layout)

        self.button_cycle_start.clicked.connect(self.set_cycle_start)
        self.button_cycle_end.clicked.connect(self.set_cycle_end)
        self.save_button.clicked.connect(self.save)
        self.video_player.slider.valueChanged.connect(self.change_frame)

    def keyPressEvent(self, event) -> None:
        if event.key() == PyQt5.QtCore.Qt.Key_Right:
            self.video_player.increment_frame(force=True)

        if event.key() == PyQt5.QtCore.Qt.Key_Left:
            self.video_player.decrement_frame(force=True)

    def save(self) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Are you sure?")
        dlg.setText(
            f"You chose {self.cycle_start_index} and {self.cycle_end_index} as start and end frame. Is this ok?"
        )
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        button = dlg.exec()

        if button == QMessageBox.No:
            return

        cycle_dict = {
            "cycle_start": self.cycle_start_index,
            "cycle_end": self.cycle_end_index,
        }
        with open(os.path.join(self.project_path, "cycle_index.json"), "w") as outfile:
            json.dump(cycle_dict, outfile)

    def set_cycle_start(self) -> None:
        self.cycle_start_index = self.video_player.value()
        self.first_cycle_view.set_image(self.video_view.images[self.cycle_start_index])

    def set_cycle_end(self) -> None:
        self.cycle_end_index = self.video_player.value()
        self.second_cycle_view.set_image(self.video_view.images[self.cycle_end_index])

    def change_frame(self) -> None:
        self.video_view.change_frame(self.video_player.slider.value())
