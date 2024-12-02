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
from VFLabel.utils.defines import COLOR
from VFLabel.utils.defines import TEST_PROJECT_PATH

if __name__ == "__main__":

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Vocalfold Segmentation Designer")

            # Create a central widget and a layout
            central_widget = QWidget(self)
            layout = QVBoxLayout(central_widget)

            videodata = VFLabel.io.data.read_video("assets/test_data/test_video_2.avi")

            # Set up the zoomable view
            view = VFLabel.gui.GlottisSegmentationWidget(TEST_PROJECT_PATH, videodata)
            layout.addWidget(view)

            # Set up the main window^
            self.setCentralWidget(central_widget)
            self.setGeometry(100, 100, 800, 600)

            # Show the window
            self.show()

    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()

    # Run the application
    sys.exit(app.exec_())
