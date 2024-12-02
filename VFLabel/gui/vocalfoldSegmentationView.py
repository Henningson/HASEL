import sys
import numpy as np

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


class VocalfoldSegmentationView(QMainWindow):

    progress_signal = pyqtSignal(str)

    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path
        self.init_window()

    def init_window(self) -> None:
        # Create a central widget and a layout
        central_widget = QWidget(self)

        # Set up the main window
        self.setCentralWidget(central_widget)
        self.setWindowTitle("Vocalfold Segmentation Designer")
        self.setGeometry(100, 100, 800, 600)

        # Show the window
        self.show()

    def update_progress(self, progress) -> None:
        self.progress = progress

    def closeEvent(self, event) -> None:
        # opens window which asks for current state of this task
        self.progress_window = VFLabel.gui.progressStateWidget.ProgressStateWidget()

        # connect signal which updates progress state
        self.progress_window.progress_signal.connect(self.update_progress)

        # waits for progress_window to close
        loop = QEventLoop()
        self.progress_window.destroyed.connect(loop.quit)
        loop.exec_()

        # sends signal
        self.progress_signal.emit(self.progress)

        # closes this window
        self.deleteLater()
