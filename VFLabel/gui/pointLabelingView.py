import sys
import numpy as np
import json
import os

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from PyQt5.QtCore import pyqtSignal, QEventLoop

import VFLabel.gui
import VFLabel.gui.glottisSegmentationWidget
import VFLabel.gui.progressStateWidget
import VFLabel.gui.vocalfoldSegmentationWidget


import VFLabel.io
import VFLabel.utils.utils


class PointLabelingView(QWidget):

    signal_open_main_menu = pyqtSignal(str)

    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.init_window()

    def init_window(self) -> None:

        # Show the window
        self.show()

    def update_progress(self, progress) -> None:
        self.progress = progress

    def save_current_state(self):
        print("save point labeling")
        # TODO implement

    def update_save_state(self, state) -> None:
        if state:
            self.save_current_state()
        else:
            pass

    def close_window(self) -> None:
        # open window which asks if the data should be saved (again)
        self.save_state_window = VFLabel.gui.saveStateWidget.SaveStateWidget(self)

        # connect signal which updates save state
        self.save_state_window.save_state_signal.connect(self.update_save_state)

        # wait for save_state_window to close
        loop = QEventLoop()
        self.save_state_window.destroyed.connect(loop.quit)
        loop.exec_()

        # open window which asks for current state of this task
        self.progress_window = VFLabel.gui.progressStateWidget.ProgressStateWidget()

        # connect signal which updates progress state
        self.progress_window.progress_signal.connect(self.update_progress)

        # wait for progress_window to close
        loop = QEventLoop()
        self.progress_window.destroyed.connect(loop.quit)
        loop.exec_()

        # save new progress state
        progress_state_path = os.path.join(self.project_path, "progress_status.json")

        with open(progress_state_path, "r+") as prgrss_file:
            file = json.load(prgrss_file)
            file["progress_pt_label"] = self.progress
            prgrss_file.seek(0)
            prgrss_file.truncate()
            json.dump(file, prgrss_file, indent=4)

        # go back to main window
        self.signal_open_main_menu.emit(self.project_path)
