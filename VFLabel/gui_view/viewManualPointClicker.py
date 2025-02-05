import json
import os
from typing import List

import cv2
import numpy as np
import torch
from PyQt5 import QtCore
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QCursor, QIcon, QImage
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import VFLabel.cv.point_interpolation as pi
import VFLabel.cv.segmentation
import VFLabel.gui_graphics_view.interpolateSegmentation
import VFLabel.gui_graphics_view.labeledPoints
import VFLabel.gui_graphics_view.manualPointClicker
import VFLabel.gui_graphics_view.segmentationDrawer
import VFLabel.gui_graphics_view.segmentationOverlay
import VFLabel.gui_graphics_view.showPoints
import VFLabel.gui_graphics_view.transformableSegmentation
import VFLabel.gui_graphics_view.zoomable
import VFLabel.gui_graphics_view.zoomableVideo
import VFLabel.gui_widgets.buttonGrid
import VFLabel.gui_widgets.videoPlayerBar
import VFLabel.io as io
import VFLabel.io.data
import VFLabel.nn.point_tracking
import VFLabel.utils.transforms
import VFLabel.utils.utils


class ManualPointClickerView(QWidget):
    def __init__(
        self,
        grid_height: int,
        grid_width: int,
        video: np.array,
        project_path: str,
        parent=None,
        check_for_existing_data=False,
    ):
        super(ManualPointClickerView, self).__init__(parent)

        # Setup paths
        self.path_project: str = project_path

        self.path_tracked_points: str = os.path.join(
            self.path_project, "predicted_laserpoints.json"
        )

        self.path_repaired_points: str = os.path.join(
            self.path_project, "repaired_laserpoints.json"
        )

        self.path_final_optimized_points: str = os.path.join(
            self.path_project, "final_optimized_laserpoints.json"
        )

        self.path_final_optimized_points_labels: str = os.path.join(
            self.path_project, "final_optimized_laserpoints_labels.json"
        )

        self.path_vf_segmentations: str = os.path.join(
            self.path_project, "vocalfold_segmentation"
        )
        self.path_glottis_segmentations: str = os.path.join(
            self.path_project, "glottis_segmentation"
        )

        self.grid_width = grid_width
        self.grid_height = grid_height

        # We assume video is a np.array or List[np.array].
        self.video = video

        qvideo: List[QImage] = VFLabel.utils.transforms.vid_2_QImage(video)

        self.point_repair_widget = (
            VFLabel.gui_graphics_view.manualPointClicker.ManualPointClicker(
                qvideo, grid_height=grid_height, grid_width=grid_width
            )
        )

        self.optimized_points_widget = (
            VFLabel.gui_graphics_view.labeledPoints.LabeledPoints(
                qvideo, grid_width=18, grid_height=18
            )
        )

        self.video_player = VFLabel.gui_widgets.videoPlayerBar.VideoPlayerBarWidget(
            len(qvideo), 100
        )

        self.button_grid = VFLabel.gui_widgets.buttonGrid.ButtonGrid(
            grid_height=grid_height, grid_width=grid_width
        )
        self.button_draw = QPushButton("Add Points")
        self.button_remove = QPushButton("Remove Laserpoints")
        self.button_disable_modes = QPushButton("Disable Modes")
        self.button_finished_clicking = QPushButton("Finished Clicking")
        self.button_optimize_points = QPushButton("Optimize Points")
        self.button_save = QPushButton("Save")

        # Layouting, signals etc
        vertical_layout = QVBoxLayout()
        horizontal_layout_top = QHBoxLayout()
        top_widget = QWidget()
        horizontal_layout_bot = QHBoxLayout()
        bot_widget = QWidget()
        frame_label_widget = QWidget()

        # create number text bars
        self.semi_manual_label = QLabel("Select Points - Frame: 0")
        self.optimized_points_label = QLabel(f"Optimized Points - Frame: 0")

        help_icon_path = "assets/icons/help.svg"

        help_optimize_button = QPushButton(QIcon(help_icon_path), "")
        help_optimize_button.clicked.connect(self.help_optimize_buttons)

        help_grid_btn_button = QPushButton(QIcon(help_icon_path), "")
        help_grid_btn_button.clicked.connect(self.help_grid_buttons)

        help_btn_button = QPushButton(QIcon(help_icon_path), "")
        help_btn_button.clicked.connect(self.help_different_buttons)

        help_left_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_left_frame_button.clicked.connect(self.help_left_frame_dialog)

        point_clicker_label = QHBoxLayout()
        point_clicker_label.addStretch(1)
        point_clicker_label.addWidget(self.semi_manual_label)
        point_clicker_label.addWidget(help_left_frame_button)
        point_clicker_label.addStretch(1)

        help_middle_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_middle_frame_button.clicked.connect(self.help_middle_frame_dialog)

        cotracker_label = QHBoxLayout()
        cotracker_label.addStretch(1)
        cotracker_label.addWidget(help_middle_frame_button)
        cotracker_label.addStretch(1)

        grid_button_widget = QWidget()
        grid_button_layout = QVBoxLayout()
        grid_button_layout.addStretch(1)
        grid_button_layout.addWidget(help_grid_btn_button)
        grid_button_layout.addWidget(self.button_grid)
        grid_button_layout.addStretch(1)
        grid_button_layout.addWidget(help_btn_button)
        grid_button_layout.addWidget(self.button_draw)
        grid_button_layout.addWidget(self.button_remove)
        grid_button_layout.addWidget(self.button_disable_modes)
        grid_button_layout.addWidget(self.button_finished_clicking)
        grid_button_widget.setLayout(grid_button_layout)

        vertical_point_repair_widget = QWidget()
        vertical_point_clicker = QVBoxLayout()
        vertical_point_clicker.addLayout(point_clicker_label)
        vertical_point_clicker.addWidget(self.point_repair_widget)
        vertical_point_repair_widget.setLayout(vertical_point_clicker)

        vertical_optimized_points_widget = QWidget()
        vertical_optimized_points = QVBoxLayout()
        vertical_optimized_points.addWidget(self.optimized_points_label)
        vertical_optimized_points.addWidget(self.optimized_points_widget)
        vertical_optimized_points_widget.setLayout(vertical_optimized_points)

        horizontal_layout_top.addWidget(grid_button_widget)
        horizontal_layout_top.addWidget(vertical_point_repair_widget)
        horizontal_layout_top.addWidget(vertical_optimized_points_widget)
        top_widget.setLayout(horizontal_layout_top)
        horizontal_layout_bot.addWidget(self.video_player)
        horizontal_layout_bot.addWidget(self.button_optimize_points)
        horizontal_layout_bot.addWidget(help_optimize_button)
        horizontal_layout_bot.addWidget(self.button_save)
        bot_widget.setLayout(horizontal_layout_bot)

        vertical_layout.addWidget(frame_label_widget)
        vertical_layout.addWidget(top_widget)
        vertical_layout.addWidget(bot_widget)
        self.setLayout(vertical_layout)

        self.button_draw.clicked.connect(self.set_draw_mode)
        self.button_remove.clicked.connect(self.set_remove_mode)
        self.button_disable_modes.clicked.connect(self.disable_modes)
        self.button_finished_clicking.clicked.connect(self.save_repaired_points)

        self.button_save.clicked.connect(self.save)
        self.button_grid.buttonSignal.connect(self.point_repair_widget.set_laser_index)
        self.button_optimize_points.clicked.connect(self.optimize_points)

        self.button_disable_modes
        self.video_player.slider.valueChanged.connect(self.change_frame)

        self.point_repair_widget.point_added.connect(
            self.button_grid.activate_highlighted
        )
        self.point_repair_widget.point_removed.connect(self.button_grid.reset_button)
        self.point_repair_widget.point_added.connect(self.increment_frame)
        self.optimized_points_widget.signal_increment_frame.connect(
            self.video_player.increment_frame
        )
        self.optimized_points_widget.signal_decrement_frame.connect(
            self.video_player.decrement_frame
        )

        self.point_repair_widget.signal_increment_frame.connect(
            self.video_player.increment_frame
        )
        self.point_repair_widget.signal_decrement_frame.connect(
            self.video_player.decrement_frame
        )

        if check_for_existing_data:
            self.load_points_to_optimize()
            self.load_optimized_points()
            self.point_repair_widget.redraw()
            self.optimized_points_widget.redraw()

    def load_points_to_optimize(self) -> None:
        # Tracked points window
        if not os.path.exists(self.path_tracked_points) and not os.path.exists(
            self.path_repaired_points
        ):
            return

        load_from_path = None
        if os.path.exists(self.path_tracked_points):
            load_from_path = self.path_tracked_points

        if os.path.exists(self.path_repaired_points):
            load_from_path = self.path_repaired_points

        # Clicked repaired points take precedenced over the tracked points with cotracker.
        # But if we generated points with cotracker before, load those.

        # Check if file is not empty
        if not os.stat(load_from_path).st_size:
            return

        # First load tracked or already repaired points.
        with open(load_from_path, "r+") as f:
            dict = json.load(f)
            array_points = VFLabel.io.point_dict_to_numpy(
                dict,
                self.grid_width,
                self.grid_height,
                self.video_player.get_video_length(),
            )

            self.point_repair_widget.point_positions = array_points

            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    point_per_frame = array_points[:, y, x]
                    contains_value = np.any(~np.isnan(point_per_frame))

                    if contains_value:
                        button = self.button_grid.getButton(x, y)
                        button.setActivated()

    def load_optimized_points(self) -> None:
        optimized_points_path = self.path_final_optimized_points
        optimized_labels_path = self.path_final_optimized_points_labels

        if not os.path.exists(optimized_points_path) or not os.path.exists(
            optimized_labels_path
        ):
            return

        if not os.path.isfile(optimized_labels_path):
            with open(optimized_labels_path, "w") as f:
                pass

        file_filled = os.stat(optimized_points_path).st_size
        file_labels_filled = os.stat(optimized_labels_path).st_size

        if not file_filled or not file_labels_filled:
            return
        else:

            with open(optimized_labels_path, "r+") as f:
                file = json.load(f)
                labels = []
                for i in range(len(self.video)):
                    num_labels_in_frame = len(file[f"Frame{i}"])

                    if num_labels_in_frame == 0:
                        labels.append(np.array([np.nan]))

                    per_frame_labels = np.ones(num_labels_in_frame) * np.nan
                    for k in range(num_labels_in_frame):
                        per_frame_labels[k] = file[f"Frame{i}"][k]["label"]

                    labels.append(per_frame_labels)

            with open(optimized_points_path, "r+") as f:
                file = json.load(f)
                positions_np, ids_np = VFLabel.io.point_dict_to_cotracker(file)

                points_positions = []
                points_ids = []
                for i in range(len(self.video)):
                    num_points_in_frame = len(file[f"Frame{i}"])
                    if num_points_in_frame == 0:
                        points_positions.append(np.array([np.nan]))
                        points_ids.append(np.array([np.nan]))

                    point_pos_per_frame = np.ones([num_points_in_frame, 2]) * np.nan
                    point_ids_per_frame = (
                        np.ones([num_points_in_frame, 2], dtype=int) * np.nan
                    )
                    for k in range(num_points_in_frame):
                        point_pos_per_frame[k] = [
                            file[f"Frame{i}"][k]["x_pos"],
                            file[f"Frame{i}"][k]["y_pos"],
                        ]

                        point_ids_per_frame[k] = [
                            file[f"Frame{i}"][k]["x_id"],
                            file[f"Frame{i}"][k]["y_id"],
                        ]

                        points_positions.append(point_pos_per_frame)
                        points_ids.append(point_ids_per_frame)

            self.optimized_points_widget.add_points_labels_and_ids(
                points_positions, labels, points_ids
            )

    def change_frame_label(self, value):
        self.semi_manual_label.setText(f"Select Points - Frame: {value}")
        self.optimized_points_label.setText(f"Optimized Points - Frame: {value}")

    def show_ok_dialog(self) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Success")
        dlg.setText(f"Clicked Points Saved.")
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.exec()

    def save_repaired_points(self, show_dialog: bool = True) -> None:
        self.disable_modes()

        laserpoints = self.point_repair_widget.point_positions
        VFLabel.io.write_points_to_json(self.path_repaired_points, laserpoints, 0)

        if show_dialog:
            self.show_ok_dialog()

    def save_optimized_points(self, show_dialog: bool = True) -> None:
        laserpoints = self.optimized_points_widget.point_positions
        ids = self.optimized_points_widget.point_ids.astype(int)

        numpy_arr = io.cotracker_to_numpy_array(
            laserpoints, ids, self.grid_width, self.grid_height
        )

        VFLabel.io.write_points_to_json(self.path_final_optimized_points, numpy_arr)
        VFLabel.io.write_visibility_to_json(
            self.path_final_optimized_points_labels,
            self.optimized_points_widget.point_labels.numpy().tolist(),
            numpy_arr,
        )

        if show_dialog:
            self.show_ok_dialog()

    def optimize_points(self) -> None:
        if not os.path.exists(self.path_repaired_points):
            print("Please press Finished Clicking after you're done.")
            return

        dict = io.dict_from_json(self.path_repaired_points)
        points = io.point_dict_to_numpy(
            dict,
            self.grid_width,
            self.grid_height,
            self.video_player.get_video_length(),
        )

        video = self.video if self.video.shape[-1] == 1 else self.video[:, :, :, :1]

        # classifications, crops = pi.classify_points(points, video)

        points = torch.from_numpy(points)
        points = pi.fill_nan_border_values_2d(points)
        points = pi.interpolate_nans_2d(points)

        # We're just interested in the dictionary, no need to save it.
        point_dict = io.write_points_to_json("", points.numpy(), 0, False)

        cotracker_styled_points, ids = io.point_dict_to_cotracker(point_dict)

        classifications, crops = pi.classify_points(cotracker_styled_points, video)

        points_subpix, _ = pi.compute_subpixel_points(
            torch.from_numpy(cotracker_styled_points),
            classifications,
            torch.from_numpy(video),
            num_points_per_frame=cotracker_styled_points.shape[0] // len(video),
        )

        points_subpix = pi.smooth_points(points_subpix)

        classifications = classifications.reshape(
            self.video.shape[0], len(dict["Frame0"])
        )
        # points_subpix = pi.fill_nan_border_values(points_subpix)

        # NEED TO TRANSFORM N x 3 OR WHATEVER TO NUM FRAMES x NUM POINTS x WHATEVER
        points_subpix = points_subpix.permute(1, 0, 2).numpy()

        vocalfold_segmentations = np.array(
            io.read_images_from_folder(self.path_vf_segmentations, is_gray=True)
        )
        glottis_segmentations = np.array(
            io.read_images_from_folder(self.path_glottis_segmentations, is_gray=True)
        )
        filtered_points = pi.filter_points_not_on_vocalfold(
            points_subpix, vocalfold_segmentations
        )
        filtered_points = pi.filter_points_on_glottis(
            filtered_points, glottis_segmentations
        )

        self.optimized_points_widget.add_points_labels_and_ids(
            filtered_points, classifications, ids[:, 1:]
        )

        self.save_optimized_points(show_dialog=False)

    def save(self) -> None:
        self.save_optimized_points()

    def set_draw_mode(self) -> None:
        self.setCursor(QCursor(QtCore.Qt.CrossCursor))
        self.point_repair_widget.DRAW_MODE_on()
        self.point_repair_widget.REMOVE_MODE_off()

    def set_remove_mode(self) -> None:
        self.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        self.point_repair_widget.REMOVE_MODE_on()
        self.point_repair_widget.DRAW_MODE_off()

    def disable_modes(self) -> None:
        self.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        self.point_repair_widget.REMOVE_MODE_off()
        self.point_repair_widget.DRAW_MODE_off()

    def change_frame(self) -> None:
        self.point_repair_widget.change_frame(self.video_player.slider.value())
        self.optimized_points_widget.change_frame(self.video_player.slider.value())
        self.change_frame_label(self.video_player.slider.value())

    def increment_frame(self) -> None:
        self.video_player.increment_frame(force=True)
        self.change_frame()

    def trigger_next_laser_point(self) -> None:
        x_laser = self.point_repair_widget.x_index
        y_laser = self.point_repair_widget.y_index

        if y_laser + 1 >= len(self.button_grid.buttons):
            return

        self.button_grid.getButton(x_laser, y_laser + 1).on_clicked(True)

    def help_left_frame_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Point Clicking")
        dlg.setText(
            "This view shows the first 50 frames of the input video. Use this view to generate initial point candidates for each laserpoint. It is only necessary to select one visible candidate for each laserpoint inside this cycle. You can add points by starting the 'Add Point' mode with the button on the left hand side. To select a point, first click its corresponding position inside the grid on the left, and then select the point inside the image. A point can be selected with the Left Mousebutton.  Selecting a point will automatically advance the selected box inside the gid, allowing for fast selecting of suitable point candidates. Removing points is possible by using the 'Remove points' button on the left. If all suitable point-candidates were selected, save your selection using the 'Finished clicking' button."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_middle_frame_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Tracked Points")
        dlg.setText(
            "This window shows the results of 'Track points' that were tracked using metas cotracker3."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_right_frame_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Right frame")
        dlg.setText("This window shows the results of 'Optimize points'.")
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_grid_buttons(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Button grid")
        dlg.setText(
            "Click the corresponding point that you want to click in the left window. \n"
            "Green: This point already has a chosen point in the left window. \n"
            "Red: Activated point for which a point in the left window is chosen."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_different_buttons(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Buttons")
        dlg.setText(
            "These buttons help with the marking of the laser points.\n"
            "Add points: add one point in the left window.\n"
            "Remove points: remove one point in the left window.\n"
            "Disable Modes: Disable add/remove mode.\n"
            "Finished Clicking: Save the points.\n"
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_optimize_buttons(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Optimize points")
        dlg.setText(
            "Tracks, optimize and filters points based on the tracking information coming from the previously localized points."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()
