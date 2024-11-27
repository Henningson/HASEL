import sys
import numpy as np

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

import VFLabel.gui
import VFLabel.gui.glottisSegmentationWidget
import VFLabel.gui.vocalfoldSegmentationView


import VFLabel.io
import VFLabel.utils.utils


class GlottisSegmentationView(QMainWindow):
    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path
        self.init_window()

    def init_window(self):
        self.setWindowTitle("Glottis Segmentation Designer")

        # Create a central widget and a layout
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)

        # Set up the main window^
        self.setCentralWidget(central_widget)
        self.setGeometry(100, 100, 800, 600)

        # Show the window
        self.show()
