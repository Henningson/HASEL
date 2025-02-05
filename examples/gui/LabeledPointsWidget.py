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

import VFLabel.gui_graphics_view.labeledPoints
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
            self.setWindowTitle("Optimized and Labeled Points")

            # Create a central widget and a layout
            central_widget = QWidget(self)
            layout = QHBoxLayout(central_widget)

            project_path = VFLabel.utils.defines.TEST_PROJECT_PATH
            video_path = os.path.join(project_path, "video")
            vf_segmentation_path = os.path.join(project_path, "vocalfold_segmentation")
            glottis_segmentation_path = os.path.join(
                project_path, "glottis_segmentation"
            )

            video = np.array(io.read_images_from_folder(video_path, is_gray=True))[:175]
            dict = io.dict_from_json("projects/test_project/predicted_laserpoints.json")
            points, ids = io.point_dict_to_cotracker(dict)

            classifications, crops = pi.classify_points(points, video)

            points_subpix, _ = pi.compute_subpixel_points(
                torch.from_numpy(points),
                classifications,
                torch.from_numpy(video),
                len(dict["Frame0"]),
            )

            points_subpix = pi.smooth_points(points_subpix)
            points_subpix = pi.fill_nan_border_values(points_subpix)

            # NEED TO TRANSFORM N x 3 OR WHATEVER TO NUM FRAMES x NUM POINTS x WHATEVER
            points = points.reshape(video.shape[0], len(dict["Frame0"]), 3)[
                :, :, [1, 2]
            ]
            points_subpix = points_subpix.permute(1, 0, 2).numpy()
            classifications = classifications.reshape(
                video.shape[0], len(dict["Frame0"])
            )

            vocalfold_segmentations = np.array(
                io.read_images_from_folder(vf_segmentation_path, is_gray=True)
            )[:175]
            glottis_segmentations = np.array(
                io.read_images_from_folder(glottis_segmentation_path, is_gray=True)
            )[:175]
            filtered_points = pi.filter_points_not_on_vocalfold(
                points_subpix, vocalfold_segmentations
            )
            filtered_points = pi.filter_points_on_glottis(
                points_subpix, glottis_segmentations
            )

            video_rgb = np.array(io.read_images_from_folder(video_path))[:175]
            qvideo: List[QImage] = VFLabel.utils.transforms.vid_2_QImage(video_rgb)
            # Set up the zoomable view
            self.view_1 = VFLabel.gui_graphics_view.labeledPoints.LabeledPoints(qvideo)
            self.view_1.add_points_and_classes(points, classifications)
            layout.addWidget(self.view_1)

            self.view_2 = VFLabel.gui_graphics_view.labeledPoints.LabeledPoints(qvideo)
            self.view_2.add_points_and_classes(filtered_points, classifications)
            layout.addWidget(self.view_2)

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
