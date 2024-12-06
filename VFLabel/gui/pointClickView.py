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

from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor, QPixmap, QImage, QCursor
import os

import VFLabel.io as io

import VFLabel.gui.cotrackerPointClickWidget
import VFLabel.gui.pointViewWidget

import VFLabel.nn.point_tracking

import VFLabel.gui.labeledPointWidget
import VFLabel.utils.transforms

import VFLabel.gui.drawSegmentationWidget
import VFLabel.gui.transformSegmentationWidget
import VFLabel.gui.interpolateSegmentationWidget
import VFLabel.gui.videoPlayerWidget
import VFLabel.gui.videoViewWidget
import VFLabel.gui.zoomableViewWidget
import VFLabel.gui.videoOverlayWidget
import VFLabel.gui.buttonGridWidget

import VFLabel.utils.transforms
import VFLabel.io.data
import VFLabel.utils.utils

import VFLabel.cv.point_interpolation as pi
import VFLabel.cv.segmentation
import json
import cv2


import torch

from VFLabel.utils.defines import COLOR

from typing import List

##################### ^
#         #         # |
#         #         # |
#  GRID   #  VIDEO  # |
#         #         # |
#  DRAW   #         # |
#  REMOVE #         # |
##################### |
#  VWP    # SAVE    #


class PointClickView(QWidget):
    def __init__(
        self,
        grid_height: int,
        grid_width: int,
        cycle_start: int,
        cycle_end: int,
        video: np.array,
        project_path: str,
        parent=None,
    ):
        super(PointClickView, self).__init__(parent)

        # Setup paths
        self.path_project: str = project_path
        self.path_clicked_points: str = os.path.join(
            self.path_project, "clicked_laserpoints.json"
        )
        self.path_predicted_points: str = os.path.join(
            self.path_project, "predicted_laserpoints.json"
        )
        self.path_optimized_points: str = os.path.join(
            self.path_project, "optimized_laserpoints.json"
        )

        self.path_vf_segmentations: str = os.path.join(
            self.path_project, "vocalfold_segmentation"
        )
        self.path_glottis_segmentations: str = os.path.join(
            self.path_project, "glottis_segmentation"
        )

        self.cycle_start = cycle_start
        self.cycle_end = cycle_end

        # We assume video is a np.array or List[np.array].
        self.video = video

        qvideo: List[QImage] = VFLabel.utils.transforms.vid_2_QImage(video)
        click_video = qvideo[cycle_start:cycle_end]

        self.point_clicker_widget = (
            VFLabel.gui.cotrackerPointClickWidget.CotrackerPointClickWidget(
                click_video, grid_height=grid_height, grid_width=grid_width
            )
        )

        self.cotracker_widget = VFLabel.gui.labeledPointWidget.LabeledPointWidget(
            qvideo, grid_width=grid_width, grid_height=grid_height
        )

        self.optimized_points_widget = (
            VFLabel.gui.labeledPointWidget.LabeledPointWidget(
                qvideo, grid_width=18, grid_height=18
            )
        )

        self.video_player = VFLabel.gui.videoPlayerWidget.VideoPlayerWidget(
            len(qvideo), 100
        )

        self.button_grid = VFLabel.gui.buttonGridWidget.ButtonGrid(
            grid_height=grid_height, grid_width=grid_width
        )
        self.button_draw = QPushButton("Add Points")
        self.button_remove = QPushButton("Remove Points")
        self.button_disable_modes = QPushButton("Disable Modes")

        self.button_generate_predictions = QPushButton("Track Points")
        self.button_optimize_points = QPushButton("Optimize Points")

        # Layouting, signals etc
        vertical_layout = QVBoxLayout()
        horizontal_layout_top = QHBoxLayout()
        top_widget = QWidget()
        horizontal_layout_bot = QHBoxLayout()
        bot_widget = QWidget()

        grid_button_widget = QWidget()
        grid_button_layout = QVBoxLayout()
        grid_button_layout.addWidget(self.button_grid)
        grid_button_layout.addWidget(self.button_draw)
        grid_button_layout.addWidget(self.button_remove)
        grid_button_layout.addWidget(self.button_disable_modes)
        grid_button_widget.setLayout(grid_button_layout)

        horizontal_layout_top.addWidget(grid_button_widget)
        horizontal_layout_top.addWidget(self.point_clicker_view)
        top_widget.setLayout(horizontal_layout_top)

        horizontal_layout_bot.addWidget(self.video_player)
        horizontal_layout_bot.addWidget(self.save_button)
        bot_widget.setLayout(horizontal_layout_bot)

        vertical_layout.addWidget(top_widget)
        vertical_layout.addWidget(bot_widget)
        self.setLayout(vertical_layout)

        self.button_draw.clicked.connect(self.set_draw_mode)
        self.button_remove.clicked.connect(self.set_remove_mode)
        self.button_disable_modes.clicked.connect(self.disable_modes)
        self.save_button.clicked.connect(self.save)
        self.point_clicker_view.point_added.connect(self.increment_frame)
        self.button_grid.buttonSignal.connect(self.point_clicker_view.set_laser_index)
        self.video_player.slider.valueChanged.connect(self.change_frame)

    def save(self) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Save everything?")
        dlg.setText(f"Are you sure?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        button = dlg.exec()

        if button == QMessageBox.No:
            return

        self.save_clicked_points(show_dialog=False)
        self.save_tracked_points(show_dialog=False)
        self.save_optimized_points(show_dialog=False)

    def show_ok_dialog(self) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Success")
        dlg.setText(f"Clicked Points Saved.")
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.exec()

    # TODO: Refactor save functionality!
    def save_clicked_points(self, show_dialog: bool = True) -> None:
        laserpoints = self.point_clicker_view.point_positions
        VFLabel.io.write_points_to_json(
            self.path_clicked_points, laserpoints, self.cycle_start
        )

        if show_dialog:
            self.show_ok_dialog()

    def save_tracked_points(self, show_dialog: bool = True) -> None:
        laserpoints = self.point_clicker_view.point_positions
        VFLabel.io.write_points_to_json(self.path_predicted_points, laserpoints)

        if show_dialog:
            self.show_ok_dialog()

    def save_optimized_points(self, show_dialog: bool = True) -> None:
        laserpoints = self.point_clicker_view.point_positions
        VFLabel.io.write_points_to_json(self.path_optimized_points, laserpoints)

        if show_dialog:
            self.show_ok_dialog()

    def track_points(self) -> None:
        dict = io.dict_from_json("projects/test_project/clicked_laserpoints.json")
        points, ids = io.point_dict_to_cotracker(dict)

        pred_points, pred_visibility = VFLabel.nn.point_tracking.track_points_windowed(
            self.video, points
        )
        self.cotracker_widget.add_points_and_classes()

    def optimize_points(self) -> None:
        dict = io.dict_from_json("projects/test_project/predicted_laserpoints.json")
        points, ids = io.point_dict_to_cotracker(dict)

        classifications, crops = pi.classify_points(points, self.video)

        points_subpix, _ = pi.compute_subpixel_points(
            torch.from_numpy(points),
            classifications,
            torch.from_numpy(self.video),
            len(dict["Frame0"]),
        )

        points_subpix = pi.smooth_points(points_subpix)
        points_subpix = pi.fill_nan_border_values(points_subpix)

        # NEED TO TRANSFORM N x 3 OR WHATEVER TO NUM FRAMES x NUM POINTS x WHATEVER
        points = points.reshape(video.shape[0], len(dict["Frame0"]), 3)[:, :, [1, 2]]
        points_subpix = points_subpix.permute(1, 0, 2).numpy()
        classifications = classifications.reshape(video.shape[0], len(dict["Frame0"]))

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

    def save(self) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Are you sure?")
        dlg.setText(f"Are you sure?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        button = dlg.exec()

        if button == QMessageBox.No:
            return

        path = os.path.join(self.project_path, "laserpoint_segmentations")
        json_path = os.path.join(self.project_path, "clicked_laserpoints.json")

        laserpoints = self.point_clicker_view.point_positions

        video_dict = {}
        for frame_index, per_frame_points in enumerate(laserpoints):
            point_list = []
            point_coordinates = VFLabel.cv.get_points_from_tensor(per_frame_points)
            point_ids = VFLabel.cv.get_point_indices_from_tensor(per_frame_points)

            for point, id in zip(point_coordinates, point_ids):
                point_dict = {
                    "x_pos": point[0].item(),
                    "y_pos": point[1].item(),
                    "x_id": id[1].item(),
                    "y_id": id[0].item(),
                }
                point_list.append(point_dict)

            video_dict[f"Frame{self.cycle_start + frame_index}"] = point_list

        with open(json_path, "w") as outfile:
            json.dump(video_dict, outfile)

        segmentations = VFLabel.cv.generate_laserpoint_segmentations(
            self.point_clicker_view.point_positions,
            self.point_clicker_view._image_height,
            self.point_clicker_view._image_width,
        )

        for frame_index, segmentation in enumerate(segmentations):
            cv2.imwrite(
                os.path.join(path, f"{self.cycle_start + frame_index:05d}.png"),
                segmentation,
            )

    def set_draw_mode(self) -> None:
        self.setCursor(QCursor(QtCore.Qt.CrossCursor))
        self.point_clicker_view.DRAW_MODE_on()
        self.point_clicker_view.REMOVE_MODE_off()

    def set_remove_mode(self) -> None:
        self.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        self.point_clicker_view.REMOVE_MODE_on()
        self.point_clicker_view.DRAW_MODE_off()

    def disable_modes(self) -> None:
        self.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        self.point_clicker_view.REMOVE_MODE_off()
        self.point_clicker_view.DRAW_MODE_off()

    def change_frame(self) -> None:
        self.point_clicker_view.change_frame(self.video_player.slider.value())

    def increment_frame(self) -> None:
        self.video_player.increment_frame(force=True)
        self.point_clicker_view.change_frame(self.video_player.slider.value())
