import sys

from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QMainWindow,
    QVBoxLayout,
    QWidget,  #
    QMessageBox,
)
from typing import List
from PyQt5.QtGui import QImage
import PyQt5.QtCore

import VFLabel.gui.pointViewWidget
import VFLabel.utils.defines
import VFLabel.nn.point_tracking
import numpy as np

if __name__ == "__main__":

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.current_frame = 0
            self.setWindowTitle("Generate Some Points for a Video")

            # Create a central widget and a layout
            central_widget = QWidget(self)
            layout = QVBoxLayout(central_widget)

            videodata = VFLabel.io.data.read_video("assets/test_data/test_video_1.avi")

            qvideo: List[QImage] = VFLabel.utils.transforms.vid_2_QImage(videodata)
            # Set up the zoomable view
            self.view = VFLabel.gui.pointViewWidget.PointViewWidget(qvideo)
            layout.addWidget(self.view)

            video = VFLabel.io.data.read_video("assets/test_data/test_video_1.avi")
            pred_points, pred_visibility = (
                VFLabel.nn.point_tracking.track_points_windowed(
                    video, np.array([[0.0, 128.0, 256.0], [0.0, 138.0, 295.0]])
                )
            )

            self.view.add_points(pred_points)

            # Set up the main window^
            self.setCentralWidget(central_widget)
            self.setGeometry(100, 100, 800, 600)

            # Show the window
            self.show()

        def keyPressEvent(self, event) -> None:
            self.current_frame += 1
            self.view.change_frame(self.current_frame)

    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()

    # Run the application
    sys.exit(app.exec_())
