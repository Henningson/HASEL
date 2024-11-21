import sys
import numpy as np

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

import VFLabel.gui
import VFLabel.gui.glottisSegmentationView
import VFLabel.gui.vocalfoldSegmentationView


import VFLabel.io
import VFLabel.utils.utils
from VFLabel.utils.defines import COLOR

if __name__ == "__main__":
    video = VFLabel.io.data.read_images_from_folder(
        "assets/test_data/CF/glottal_mask", is_gray=True
    )
    videodata = np.array(video) // 255
    for image in videodata:
        colored = VFLabel.utils.utils.class_to_color_np(
            image, [COLOR.BACKGROUND, COLOR.GLOTTIS]
        )

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Vocalfold Segmentation Designer")

            # Create a central widget and a layout
            central_widget = QWidget(self)
            layout = QVBoxLayout(central_widget)

            videodata = VFLabel.io.data.read_images_from_folder(
                "assets/test_data/CF/png"
            )
            videodata = np.array(videodata)

            # Set up the zoomable view
            view = VFLabel.gui.GlottisSegmentationView(videodata)
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
