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
import VFLabel.gui_widgets.buttonGrid
import VFLabel.gui_graphics_view.pointClickerCotracker
import VFLabel.gui_graphics_view.segmentationDrawer
import VFLabel.gui_graphics_view.interpolateSegmentation
import VFLabel.gui_graphics_view.labeledPoints
import VFLabel.gui_graphics_view.showPoints
import VFLabel.gui_graphics_view.transformableSegmentation
import VFLabel.gui_graphics_view.segmentationOverlay
import VFLabel.gui_widgets.videoPlayerBar
import VFLabel.gui_graphics_view.zoomableVideo
import VFLabel.gui_graphics_view.zoomable
import VFLabel.io as io
import VFLabel.io.data
import VFLabel.nn.point_tracking
import VFLabel.utils.transforms
import VFLabel.utils.utils

##################### ^
#         #         # |
#         #         # |
#  GRID   #  VIDEO  # |
#         #         # |
#  DRAW   #         # |
#  REMOVE #         # |
##################### |
#  VWP    # SAVE    #


class PointClickerView(QWidget):
    def __init__(
        self,
        grid_height: int,
        grid_width: int,
        cycle_start: int,
        cycle_end: int,
        video: np.array,
        project_path: str,
        parent=None,
        check_for_existing_data=False,
    ):
        super(PointClickerView, self).__init__(parent)

        # Setup paths
        self.path_project: str = project_path
        self.path_clicked_points: str = os.path.join(
            self.path_project, "clicked_laserpoints.json"
        )
        self.path_predicted_points: str = os.path.join(
            self.path_project, "predicted_laserpoints.json"
        )
        self.path_predicted_points_labels: str = os.path.join(
            self.path_project, "label_cycles.json"
        )

        self.path_optimized_points_labels: str = os.path.join(
            self.path_project, "optimized_label_cycles.json"
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

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.cycle_start = cycle_start
        self.cycle_end = cycle_end

        # We assume video is a np.array or List[np.array].
        self.video = video

        qvideo: List[QImage] = VFLabel.utils.transforms.vid_2_QImage(video)
        click_video = qvideo[cycle_start:cycle_end]

        self.point_clicker_widget = (
            VFLabel.gui_graphics_view.pointClickerCotracker.PointClickerCotracker(
                click_video, grid_height=grid_height, grid_width=grid_width
            )
        )

        self.cotracker_widget = VFLabel.gui_graphics_view.labeledPoints.LabeledPoints(
            qvideo, grid_width=grid_width, grid_height=grid_height
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
        self.button_remove = QPushButton("Remove Points")
        self.button_disable_modes = QPushButton("Disable Modes")
        self.button_finished_clicking = QPushButton("Finished Clicking")

        self.button_track_points = QPushButton("Track Points")
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
        self.frame_label_left = QLabel("Click Points - Frame: 0")
        self.frame_label_middle = QLabel(f"Tracked Points - Frame: 0")
        self.frame_label_right = QLabel(f"Optimized Points - Frame: 0")

        help_icon_path = "assets/icons/help.svg"

        help_track_button = QPushButton(QIcon(help_icon_path), "")
        help_track_button.clicked.connect(self.help_track_buttons)

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
        point_clicker_label.addWidget(self.frame_label_left)
        point_clicker_label.addWidget(help_left_frame_button)
        point_clicker_label.addStretch(1)

        help_middle_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_middle_frame_button.clicked.connect(self.help_middle_frame_dialog)

        cotracker_label = QHBoxLayout()
        cotracker_label.addStretch(1)
        cotracker_label.addWidget(self.frame_label_middle)
        cotracker_label.addWidget(help_middle_frame_button)
        cotracker_label.addStretch(1)

        help_right_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_right_frame_button.clicked.connect(self.help_right_frame_dialog)

        optimized_points_label = QHBoxLayout()
        optimized_points_label.addStretch(1)
        optimized_points_label.addWidget(self.frame_label_right)
        optimized_points_label.addWidget(help_right_frame_button)
        optimized_points_label.addStretch(1)

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

        vertical_point_clicker_widget = QWidget()
        vertical_point_clicker = QVBoxLayout()
        vertical_point_clicker.addLayout(point_clicker_label)
        vertical_point_clicker.addWidget(self.point_clicker_widget)
        vertical_point_clicker_widget.setLayout(vertical_point_clicker)

        vertical_cotracker_widget = QWidget()
        vertical_cotracker = QVBoxLayout()
        vertical_cotracker.addLayout(cotracker_label)
        vertical_cotracker.addWidget(self.cotracker_widget)
        vertical_cotracker_widget.setLayout(vertical_cotracker)

        vertical_optimized_points_widget = QWidget()
        vertical_optimized_points = QVBoxLayout()
        vertical_optimized_points.addLayout(optimized_points_label)
        vertical_optimized_points.addWidget(self.optimized_points_widget)
        vertical_optimized_points_widget.setLayout(vertical_optimized_points)

        horizontal_layout_top.addWidget(grid_button_widget)
        horizontal_layout_top.addWidget(vertical_point_clicker_widget)
        horizontal_layout_top.addWidget(vertical_cotracker_widget)
        horizontal_layout_top.addWidget(vertical_optimized_points_widget)
        top_widget.setLayout(horizontal_layout_top)

        horizontal_layout_bot.addWidget(self.video_player)
        horizontal_layout_bot.addWidget(self.button_track_points)
        horizontal_layout_bot.addWidget(help_track_button)
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
        self.button_finished_clicking.clicked.connect(self.save_clicked_points)

        self.button_save.clicked.connect(self.save)
        self.button_grid.buttonSignal.connect(self.point_clicker_widget.set_laser_index)
        self.button_track_points.clicked.connect(self.track_points)
        self.button_optimize_points.clicked.connect(self.optimize_points)

        self.button_disable_modes
        self.video_player.slider.valueChanged.connect(self.change_frame)

        self.point_clicker_widget.point_added.connect(
            self.button_grid.activate_highlighted
        )
        self.point_clicker_widget.point_removed.connect(self.button_grid.reset_button)
        self.point_clicker_widget.point_added.connect(self.trigger_next_laser_point)
        self.cotracker_widget.signal_increment_frame.connect(
            self.video_player.increment_frame
        )
        self.cotracker_widget.signal_decrement_frame.connect(
            self.video_player.decrement_frame
        )
        self.optimized_points_widget.signal_increment_frame.connect(
            self.video_player.increment_frame
        )
        self.optimized_points_widget.signal_decrement_frame.connect(
            self.video_player.decrement_frame
        )

        self.point_clicker_widget.signal_increment_frame.connect(
            self.video_player.increment_frame
        )
        self.point_clicker_widget.signal_decrement_frame.connect(
            self.video_player.decrement_frame
        )

        if check_for_existing_data:
            self.load_existing_data()

    def load_existing_data(self):
        # check if data available

        # click points window and button grid
        clicked_points_path = os.path.join(
            self.path_project, "clicked_laserpoints.json"
        )

        if not os.path.exists(clicked_points_path):
            return

        file_filled = os.stat(clicked_points_path).st_size

        if not file_filled:
            return False
        else:

            with open(clicked_points_path, "r+") as f:
                file = json.load(f)
                for i in range(50):
                    for k in range(len(file[f"Frame{i}"])):
                        element = file[f"Frame{i}"][k]

                        # paint points in button grid
                        self.button_grid.clicked_button(
                            element["x_id"], element["y_id"]
                        )
                        # paint points in left window clicked laserpoints
                        """self.point_clicker_widget.set_laser_index(
                            element["x_id"], element["y_id"]
                        )"""
                        self.point_clicker_widget.add_point(
                            QPointF(element["x_pos"], element["y_pos"])
                        )

        # Tracked points window
        predicted_points_path = os.path.join(
            self.path_project, "predicted_laserpoints.json"
        )
        labels_path = os.path.join(self.path_project, "label_cycles.json")

        if not os.path.exists(clicked_points_path) or not os.path.exists(labels_path):
            return

        file_filled = os.stat(predicted_points_path).st_size
        file_labels_filled = os.stat(labels_path).st_size

        if not file_filled or not file_labels_filled:
            return
        else:

            with open(labels_path, "r+") as f:
                file = json.load(f)
                length = len(file[f"Frame0"])
                labels = np.zeros([len(self.video), length])
                for i in range(len(self.video)):
                    for k in range(len(file[f"Frame{i}"])):
                        labels[i, k] = file[f"Frame{i}"][k]["label"]

            with open(predicted_points_path, "r+") as f:
                file = json.load(f)
                positions_np, ids_np = VFLabel.io.point_dict_to_cotracker(file)

                points_positions = np.zeros([*np.shape(labels), 2])
                points_ids = np.zeros([*np.shape(labels), 2])
                for i in range(len(self.video)):
                    arg = np.argwhere(positions_np[:, 0] == i)
                    points_positions[i] = positions_np[arg, 1:][:, 0, :]

                    arg = np.argwhere(ids_np[:, 0] == i)
                    points_ids[i] = ids_np[arg, 1:][:, 0, :]

            self.cotracker_widget.add_points_labels_and_ids(
                points_positions, labels, points_ids
            )

        # optimized points window
        optimized_points_path = os.path.join(
            self.path_project, "optimized_laserpoints.json"
        )
        optimized_labels_path = os.path.join(
            self.path_project, "optimized_label_cycles.json"
        )

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
                labels = np.zeros([len(self.video), length]) * np.nan
                for i in range(len(self.video)):
                    for k in range(len(file[f"Frame{i}"])):
                        labels[i, k] = file[f"Frame{i}"][k]["label"]

            with open(optimized_points_path, "r+") as f:
                file = json.load(f)
                positions_np, ids_np = VFLabel.io.point_dict_to_cotracker(file)

                points_positions = np.zeros([*np.shape(labels), 2]) * np.nan
                points_ids = np.zeros([*np.shape(labels), 2]) * np.nan
                for i in range(len(self.video)):
                    for k in range(len(file[f"Frame{i}"])):
                        points_positions[i, k] = [
                            file[f"Frame{i}"][k]["x_pos"],
                            file[f"Frame{i}"][k]["y_pos"],
                        ]

                        points_ids[i, k] = [
                            file[f"Frame{i}"][k]["x_id"],
                            file[f"Frame{i}"][k]["y_id"],
                        ]

            self.optimized_points_widget.add_points_labels_and_ids(
                points_positions, labels, points_ids
            )

    def change_frame_label(self, value):
        if value < self.cycle_end:
            self.frame_label_left.setText(f"Click Points - Frame: {value}")

        self.frame_label_middle.setText(f"Tracked Points - Frame: {value}")
        self.frame_label_right.setText(f"Optimized Points - Frame: {value}")

    def show_ok_dialog(self) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Success")
        dlg.setText(f"Clicked Points Saved.")
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.exec()

    def save_clicked_points(self, show_dialog: bool = True) -> None:
        self.disable_modes()

        laserpoints = self.point_clicker_widget.point_positions
        VFLabel.io.write_points_to_json(
            self.path_clicked_points, laserpoints, self.cycle_start
        )

        if show_dialog:
            self.show_ok_dialog()

    def save_tracked_points(self, show_dialog: bool = True) -> None:
        laserpoints = self.cotracker_widget.point_positions
        ids = self.cotracker_widget.point_ids.astype(int)

        numpy_arr = io.cotracker_to_numpy_array(
            laserpoints, ids, self.grid_width, self.grid_height
        )

        VFLabel.io.write_points_to_json(self.path_predicted_points, numpy_arr)
        self.write_visibility_to_json(
            self.path_predicted_points_labels,
            self.cotracker_widget.point_labels,
            numpy_arr,
        )

        if show_dialog:
            self.show_ok_dialog()

    def save_optimized_points(self, show_dialog: bool = True) -> None:
        laserpoints = self.optimized_points_widget.point_positions
        ids = self.optimized_points_widget.point_ids.astype(int)

        numpy_arr = io.cotracker_to_numpy_array(
            laserpoints, ids, self.grid_width, self.grid_height
        )

        VFLabel.io.write_points_to_json(self.path_optimized_points, numpy_arr)
        VFLabel.io.write_visibility_to_json(
            self.path_optimized_points_labels,
            self.optimized_points_widget.point_labels.numpy().tolist(),
            numpy_arr,
        )

        if show_dialog:
            self.show_ok_dialog()

    def track_points(self) -> None:
        dict = io.dict_from_json(
            os.path.join(self.path_project, "clicked_laserpoints.json")
        )
        points, ids = io.point_dict_to_cotracker(dict)

        device = "cuda" if torch.cuda.is_available() else "cpu"
        pred_points, pred_visibility = VFLabel.nn.point_tracking.track_points_windowed(
            self.video, points, device=device
        )
        self.cotracker_widget.add_points_labels_and_ids(
            pred_points, pred_visibility, ids[:, 1:]
        )

        self.save_tracked_points(show_dialog=False)

    def optimize_points(self) -> None:
        dict = io.dict_from_json(
            os.path.join(self.path_project, "predicted_laserpoints.json")
        )
        points, ids = io.point_dict_to_cotracker(dict)

        video = self.video if self.video.shape[-1] == 1 else self.video[:, :, :, :1]

        classifications, crops = pi.classify_points(points, video)

        points_subpix, _ = pi.compute_subpixel_points(
            torch.from_numpy(points),
            classifications,
            torch.from_numpy(video),
            len(dict["Frame0"]),
        )

        points_subpix = pi.smooth_points(points_subpix)
        # points_subpix = pi.fill_nan_border_values(points_subpix)

        # NEED TO TRANSFORM N x 3 OR WHATEVER TO NUM FRAMES x NUM POINTS x WHATEVER
        points = points.reshape(self.video.shape[0], len(dict["Frame0"]), 3)[
            :, :, [1, 2]
        ]
        points_subpix = points_subpix.permute(1, 0, 2).numpy()
        classifications = classifications.reshape(
            self.video.shape[0], len(dict["Frame0"])
        )

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
        self.point_clicker_widget.DRAW_MODE_on()
        self.point_clicker_widget.REMOVE_MODE_off()

    def set_remove_mode(self) -> None:
        self.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        self.point_clicker_widget.REMOVE_MODE_on()
        self.point_clicker_widget.DRAW_MODE_off()

    def disable_modes(self) -> None:
        self.setCursor(QCursor(QtCore.Qt.ArrowCursor))
        self.point_clicker_widget.REMOVE_MODE_off()
        self.point_clicker_widget.DRAW_MODE_off()

    def change_frame(self) -> None:
        self.point_clicker_widget.change_frame(self.video_player.slider.value())
        self.cotracker_widget.change_frame(self.video_player.slider.value())
        self.optimized_points_widget.change_frame(self.video_player.slider.value())
        self.change_frame_label(self.video_player.slider.value())

    def increment_frame(self) -> None:
        self.video_player.increment_frame(force=True)
        self.change_frame()

    def trigger_next_laser_point(self) -> None:
        x_laser = self.point_clicker_widget.x_index
        y_laser = self.point_clicker_widget.y_index

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
            "Tracks, optimize and filters points based on the tracking information coming from the previous step 'Track Points'."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_track_buttons(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Track points")
        dlg.setText(
            "By pressing this button, a neural network is activated tracking the clicked points through the different frames."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()
