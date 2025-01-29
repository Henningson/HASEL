import sys

from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QMainWindow,
    QHBoxLayout,
    QWidget,  #
    QMessageBox,
)
from typing import List
from PyQt5.QtGui import QImage
import PyQt5.QtCore

import VFLabel.gui_graphics_view.cropAndSubpixelPoints
import VFLabel.utils.defines
import VFLabel.nn.point_tracking
import VFLabel.cv.point_interpolation as pi
import VFLabel.io
import numpy as np

import VFLabel.io.data as io
import VFLabel.utils.defines
import json
import os
import torch


if __name__ == "__main__":

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Look at subpixel accuracy")

            # Create a central widget and a layout
            central_widget = QWidget(self)
            layout = QHBoxLayout(central_widget)

            project_path = VFLabel.utils.defines.TEST_PROJECT_PATH
            video_path = os.path.join(project_path, "video")

            video = np.array(io.read_images_from_folder(video_path, is_gray=True))[:175]
            dict = io.dict_from_json("projects/test_project/predicted_laserpoints.json")
            points, ids = io.point_dict_to_cotracker(dict)

            classifications, crops = pi.classify_points(points, video)

            points_subpix, subpix_points_on_crops = pi.compute_subpixel_points(
                torch.from_numpy(points),
                classifications,
                torch.from_numpy(video),
                len(dict["Frame0"]),
            )
            crops = crops.numpy()
            subpix_points_on_crops = (
                subpix_points_on_crops.permute(1, 0, 2).reshape(-1, 2).numpy()
            )
            qvideo: List[QImage] = VFLabel.utils.transforms.vid_2_QImage(
                np.repeat(crops[:, :, :, None], 3, 3)
            )
            # Set up the zoomable view
            self.view_1 = (
                VFLabel.gui_graphics_view.cropAndSubpixelPoints.CropAndSubpixelPoints(
                    qvideo, subpix_points_on_crops
                )
            )
            layout.addWidget(self.view_1)

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
