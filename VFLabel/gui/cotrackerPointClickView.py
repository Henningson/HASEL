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

from PyQt5.QtCore import pyqtSignal

from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor, QPixmap, QImage, QCursor
import os

import VFLabel.gui.cotrackerPointClickWidget
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

import VFLabel.cv.segmentation
import json
import cv2

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


class CotrackerPointClickView(QWidget):
    points_tracked = pyqtSignal()

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
        super(CotrackerPointClickView, self).__init__(parent)
        self.project_path: str = project_path

        self.cycle_start = cycle_start
        self.cycle_end = cycle_end

        qvideo: List[QImage] = VFLabel.utils.transforms.vid_2_QImage(video)
        # TODO: REMOVE IN THE FINAL FRAMEWORK
        qvideo = qvideo[self.cycle_start : self.cycle_end]

        self.point_clicker_view = (
            VFLabel.gui.cotrackerPointClickWidget.CotrackerPointClickWidget(
                qvideo, grid_height=grid_height, grid_width=grid_width
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

        self.save_button = QPushButton("Save")

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
        self.button_grid.buttonSignal.connect(self.point_clicker_view.set_laser_index)
        self.video_player.slider.valueChanged.connect(self.change_frame)

        self.point_clicker_view.point_added.connect(
            self.button_grid.activate_highlighted
        )
        self.point_clicker_view.point_removed.connect(self.button_grid.reset_button)
        self.point_clicker_view.point_added.connect(self.trigger_next_laser_point)

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

        with open(json_path, "w+") as outfile:
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

    def trigger_next_laser_point(self) -> None:
        x_laser = self.point_clicker_view.x_index
        y_laser = self.point_clicker_view.y_index

        if y_laser + 1 >= len(self.button_grid.buttons):
            return

        self.button_grid.getButton(x_laser, y_laser + 1).on_clicked(True)
