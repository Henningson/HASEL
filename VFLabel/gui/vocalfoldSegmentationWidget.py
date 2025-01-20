import json
import os
from typing import List

import numpy as np
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QPolygonF
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import VFLabel.gui.drawSegmentationWidget
import VFLabel.gui.interpolateSegmentationWidget
import VFLabel.gui.transformSegmentationWidget
import VFLabel.gui.videoPlayerWidget
import VFLabel.gui.vocalfoldSegmentationSliderWidget
import VFLabel.utils.transforms

############################### ^
#         #         #         # |
#         #         #         # |
#  DRAW   #  MOVE   # INTERP  # | Vertical Layout
#  SEG    #  SEG    # VIDEO   # | Frames are Horizontal Layout
#         #         #         # |
#         #         #         # |
############################### |
# INTERP #  VIDPLAYERWIDG     # |
############################### v


class VocalfoldSegmentationWidget(QWidget):

    signal_new_mark = QtCore.pyqtSignal(int)
    signal_remove_mark = QtCore.pyqtSignal(int)
    signal_move_window_frame_number = QtCore.pyqtSignal(int)
    signal_dictionary = QtCore.pyqtSignal(object)
    signal_marks_to_interpolate = QtCore.pyqtSignal(object)

    def __init__(self, project_path: str, video: np.array, parent=None):
        super(VocalfoldSegmentationWidget, self).__init__(parent)
        self.project_path = project_path

        # find data for this task if they already exist
        file_filled = self.download_data_from_project_folder()

        # layout initialization
        self.setStyleSheet("background-color:white")
        vertical_layout = QVBoxLayout()
        horizontal_layout_top = QHBoxLayout()
        top_widget = QWidget()
        horizontal_layout_bot = QHBoxLayout()
        bot_widget = QWidget()
        segment_widget = QWidget()

        # transform video and save properties
        self.qvideo = VFLabel.utils.transforms.vid_2_QImage(video)
        video_height = video.shape[1]
        video_width = video.shape[2]

        if not file_filled:
            # if no previous data available
            # dictionary containing transformations of polygon
            self.dict_transform = {}
            self.dict_transform["0"] = [0, 0, 1, 0]
            self.dict_transform[f"{len(self.qvideo) - 1}"] = [0, 0, 1, 0]
            # list of marks(limitation values for interpolation)
            self.marks_list = np.array([0, len(self.qvideo) - 1])

        # define subwindow widgets

        # left window (draw polygon window)
        self.draw_view = VFLabel.gui.drawSegmentationWidget.DrawSegmentationWidget(
            image_height=video_height, image_width=video_width
        )
        self.draw_view.set_image(self.qvideo[0])
        if file_filled:
            # set existing polygon in draw view
            for i in self.polygon_points:
                self.draw_view.add_point(i)

        # middle window (move polygon to right position window)
        self.move_view = (
            VFLabel.gui.transformSegmentationWidget.TransformSegmentationWidget(
                self.qvideo[-1], None
            )
        )

        # right window (current frame and interpolation window)
        self.interpolate_view = (
            VFLabel.gui.interpolateSegmentationWidget.InterpolateSegmentationWidget(
                self.qvideo, None, [0.0, 0.0, 1.0, 0.0]
            )
        )

        # slider to scroll through images
        self.video_player = VFLabel.gui.videoPlayerWidget.VideoPlayerWidget(
            len(self.qvideo), 100
        )

        # segment slider - marking the different segments for the interpolation
        self.segment_slider = VFLabel.gui.vocalfoldSegmentationSliderWidget.VocalfoldSegmentationSliderWidget(
            len(self.qvideo), self.marks_list
        )

        # labels for the 3 windows
        frame_label_widget = self.initialization_frame_label(
            len(self.qvideo), video_width
        )

        # definition of buttons
        add_btn = QPushButton("add mark")
        remove_btn = QPushButton("remove mark")
        # self.save_button = QPushButton("Save")

        # adding functionality to buttons
        add_btn.clicked.connect(self.add_mark)
        remove_btn.clicked.connect(self.remove_mark)

        help_icon_path = "assets/icons/help-icon.svg"

        help_segment_slider_button = QPushButton(QIcon(help_icon_path), "")
        help_segment_slider_button.setStyleSheet("border: 0px solid #FFF")
        help_segment_slider_button.clicked.connect(self.help_segment_dialog)

        help_slider_button = QPushButton(QIcon(help_icon_path), "")
        help_slider_button.setStyleSheet("border: 0px solid #FFF")
        help_slider_button.clicked.connect(self.help_slider_dialog)
        # self.save_button.clicked.connect(self.save)

        # defining layout and layout positions
        seg_slider_layout = QHBoxLayout()
        seg_slider_layout.addWidget(self.segment_slider)
        seg_slider_layout.setSpacing(1)
        seg_slider_layout.addWidget(add_btn)
        seg_slider_layout.addWidget(remove_btn)
        seg_slider_layout.addWidget(help_segment_slider_button)
        segment_widget.setLayout(seg_slider_layout)

        horizontal_layout_top.addWidget(self.draw_view)
        horizontal_layout_top.addWidget(self.move_view)
        horizontal_layout_top.addWidget(self.interpolate_view)
        top_widget.setLayout(horizontal_layout_top)

        horizontal_layout_bot.addWidget(self.video_player)
        horizontal_layout_bot.addWidget(help_slider_button)
        # horizontal_layout_bot.addWidget(self.save_button)
        bot_widget.setLayout(horizontal_layout_bot)

        vertical_layout.addWidget(frame_label_widget)
        vertical_layout.addWidget(top_widget)
        vertical_layout.addWidget(bot_widget)
        vertical_layout.addWidget(segment_widget)
        self.vertical_layout = vertical_layout
        self.setLayout(vertical_layout)

        # connect signals
        # connection to draw view
        self.draw_view.segmentation_updated.connect(self.add_polygon_to_transform_view)

        # connection to video player
        self.video_player.slider.valueChanged.connect(self.change_frame)

        self.video_player.signal_current_frame.connect(
            self.update_signal_label_current_frame
        )

        # connection to move_view
        self.move_view.transform_updated.connect(
            self.add_transform_to_interpolation_view
        )
        self.move_view.signal_current_image.connect(
            self.update_signal_current_move_frame
        )
        self.signal_move_window_frame_number.connect(
            self.move_view.update_signal_current_move_window_frame_number
        )

        # connection to interpolation view
        self.signal_dictionary.connect(
            self.interpolate_view.update_signal_dictionary_update
        )

        self.signal_marks_to_interpolate.connect(
            self.interpolate_view.update_signal_current_marks
        )

        # connection to segment_slider
        self.signal_new_mark.connect(self.segment_slider.update_new_mark_signal)
        self.signal_remove_mark.connect(self.segment_slider.update_remove_mark_signal)
        self.segment_slider.signal_btn_pressed_position.connect(
            self.update_signal_btn_pressed_position
        )
        self.segment_slider.signal_begin_segment.connect(
            self.update_signal_begin_btn_pressed
        )
        self.segment_slider.signal_end_segment.connect(
            self.update_signal_end_btn_pressed
        )
        self.segment_slider.signal_marks.connect(
            self.update_signal_current_marks_updating
        )

        # emit initialized values
        self.signal_move_window_frame_number.emit(len(self.qvideo) - 1)
        self.signal_marks_to_interpolate.emit(self.marks_list)
        self.signal_dictionary.emit(self.dict_transform)

        if file_filled:
            # draw current marks on segment slider
            self.segment_slider.set_marks(self.marks_list)

            # set move window to last frame
            x, y, s, r = self.dict_transform[f"{len(self.qvideo) - 1}"]
            self.move_view.set_transform(x, y, s, r)
            if not self.draw_view.getPolygonPoints() is None:
                # if polygon available -> draw polygon in move and interpolation window
                self.interpolate_view.add_polygon(self.polygon)
                self.move_view.add_polygon(self.polygon)
                self.move_view.redraw()
                self.interpolate_view.redraw_from_dictionary()

    def save(self) -> None:
        self.setEnabled(False)
        QApplication.processEvents()
        save_folder = os.path.join(self.project_path, "vocalfold_segmentation")
        os.makedirs(save_folder, exist_ok=True)
        if (
            not self.draw_view.getPolygonPoints()
            or len(self.draw_view.getPolygonPoints()) < 3
        ):
            print("Not enough points to complete saving. At least 3 are necessary.")
            self.setEnabled(True)
            return

        for i in range(self.video_player.get_video_length()):
            pixmap = self.interpolate_view.generate_segmentation_for_frame(i)

            if pixmap == np.array([-1]):
                print("A polygon of at least 3 points is needed to save")
                self.setEnabled(True)
                return

            path = os.path.join(save_folder, f"{i:05d}.png")
            pixmap.save(path)

        self.upload_existing_data()
        self.interpolate_view.change_frame(self.video_player.slider.value())
        self.setEnabled(True)

    def upload_existing_data(self):
        vf_path = os.path.join(self.project_path, "vocalfold_points.json")

        with open(vf_path, "w") as f:
            file = {}
            file["dict_transform"] = self.dict_transform
            file["marks_list"] = self.marks_list.tolist()
            polygon_points = self.draw_view.getPolygonPoints()

            polygon = np.ndarray([len(polygon_points), 2])
            for l in range(len(polygon_points)):
                polygon[l, 0] = polygon_points[l].x()
                polygon[l, 1] = polygon_points[l].y()

            file["polygon"] = polygon.tolist()
            f.seek(0)
            json.dump(file, f, indent=4)

    def add_polygon_to_transform_view(self) -> None:
        polygon = QPolygonF(self.draw_view.getPolygonPoints())
        self.move_view.add_polygon(polygon)
        self.interpolate_view.add_polygon(polygon)
        self.polygon = polygon
        self.signal_dictionary.emit(self.dict_transform)

    def add_transform_to_interpolation_view(self) -> None:
        self.interpolate_view.update_transforms(*self.move_view.get_transform())

    def change_frame(self) -> None:
        self.interpolate_view.change_frame(self.video_player.slider.value())

    def add_mark(self):
        # add mark (marks a limit value for interpolation)
        value = self.video_player.slider.value()
        self.signal_new_mark.emit(value)

    def remove_mark(self):
        # remove mark (marks a limit value for interpolation)
        value = self.video_player.slider.value()
        self.signal_remove_mark.emit(value)
        if (
            str(value) in self.dict_transform.keys()
            and value != 0
            and value != len(self.qvideo) - 1
        ):
            # not first or last frame
            self.dict_transform.pop(str(value))
            self.signal_dictionary.emit(self.dict_transform)

    def update_signal_btn_pressed_position(self, position):
        self.video_player.slider.setValue(position)
        self.video_player.update_current_from_slider()
        if position != 0:
            self.update_signal_end_btn_pressed(position)

    def update_signal_begin_btn_pressed(self, position):
        self.video_player.slider.setValue(position)
        self.begin_segment = position
        self.video_player.update_current_from_slider()

    def update_signal_end_btn_pressed(self, position):
        self.end_segment = position

        # set new frame for move view
        self.signal_move_window_frame_number.emit(position)
        if not f"{position}" in self.dict_transform.keys():
            # initialize transformations for polygon in move view
            self.dict_transform[f"{position}"] = [0, 0, 1, 0]
            self.dict_transform = {
                key: self.dict_transform[key]
                for key in sorted(self.dict_transform.keys(), key=lambda x: int(x))
            }

        x, y, s, r = self.dict_transform[f"{position}"]
        self.move_view.set_transform(x, y, s, r)
        if self.draw_view.getPolygonPoints():
            # if a polygon already exists --> draw polygon in move view
            self.move_view.add_polygon(self.polygon)
            self.move_view.redraw()
        self.frame_end_no.setText(f"Transform View - Last Frame: {position}")

    def update_signal_current_move_frame(self, frame_number):
        self.dict_transform[f"{frame_number}"] = self.move_view.get_transform()
        self.signal_dictionary.emit(self.dict_transform)

    def update_signal_label_current_frame(self, frame):
        self.frame_current_no.setText(f"Interpolated Polygon - Current Frame: {frame}")

    def update_signal_current_marks_updating(self, marks_list):
        self.marks_list = marks_list
        self.signal_marks_to_interpolate.emit(marks_list)

    def initialization_frame_label(self, length_video, video_width) -> QWidget:
        frame_label_widget = QWidget()

        # create number text bars
        self.frame_start_no = QLabel("Click Vocalfold Polygon - First frame: 0")
        self.frame_end_no = QLabel(f"Transform View - Last Frame: {length_video - 1}")
        self.frame_current_no = QLabel(
            f"Interpolated Polygon - Current Frame: {self.video_player._current_frame}"
        )

        help_icon_path = "assets/icons/help-icon.svg"

        help_first_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_first_frame_button.setStyleSheet("border: 0px solid #FFF")
        help_first_frame_button.clicked.connect(self.help_first_frame_dialog)

        help_last_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_last_frame_button.setStyleSheet("border: 0px solid #FFF")
        help_last_frame_button.clicked.connect(self.help_last_frame_dialog)

        help_current_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_current_frame_button.setStyleSheet("border: 0px solid #FFF")
        help_current_frame_button.clicked.connect(self.help_current_frame_dialog)

        # insert number text in window
        boxh_frame_no_layout = QHBoxLayout()
        boxh_frame_no_layout.addStretch(1)
        boxh_frame_no_layout.addWidget(self.frame_start_no)
        boxh_frame_no_layout.addWidget(help_first_frame_button)
        boxh_frame_no_layout.addStretch(1)
        boxh_frame_no_layout.addWidget(self.frame_end_no)
        boxh_frame_no_layout.addWidget(help_last_frame_button)
        boxh_frame_no_layout.addStretch(1)
        boxh_frame_no_layout.addWidget(self.frame_current_no)
        boxh_frame_no_layout.addWidget(help_current_frame_button)
        boxh_frame_no_layout.addStretch(1)
        frame_label_widget.setLayout(boxh_frame_no_layout)

        return frame_label_widget

    def help_first_frame_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - first frame")
        dlg.setText(
            "Use this window to generate an initial segmentation of the vocal folds. You can start adding points by pressing E. This will toggle the 'point add'-mode. Add points with the left mouse button. To remove the last point, press R."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_last_frame_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - last frame")
        dlg.setText(
            "Generate a transformation in this view, such that the previously generated segmentation follows the movement of the vocal folds in the video. To move the segmentation UP, LEFT, DOWN or RIGHT use W, A, S or D respectively. Rotate anti-clockwise with J, clockwise with L, scale the vocalfolds up with I and scale the vocalfolds down using K. You can add multiple transforms (for example in the case where the physician moves forwards and backwards in a single recording) using the 'Add Mark' at the currently selected frame."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_current_frame_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - current frame")
        dlg.setText("This view shows interpolated segmentation for the given frame.")
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def download_data_from_project_folder(self):
        vf_path = os.path.join(self.project_path, "vocalfold_points.json")

        file_filled = os.stat(vf_path).st_size

        if not file_filled:
            return False
        else:
            with open(vf_path, "r+") as f:
                file = json.load(f)
                self.dict_transform = file["dict_transform"]
                self.marks_list = np.array(file["marks_list"])
                polygon = file["polygon"]
                self.polygon_points: List[QtCore.QPointF] = []
                for i in range(len(polygon)):
                    self.polygon_points.append(
                        QtCore.QPointF(polygon[i][0], polygon[i][1])
                    )
                    self.polygon = QPolygonF(self.polygon_points)

        return True

    def help_segment_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - segment slider")
        dlg.setText(
            "Generate a new transformation for the current frame. You can switch between the transformations by clicking inbetween the newly created boxes."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_slider_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - slider")
        dlg.setText(
            "Use this slider to choose a frame that you want to generate a transformation for, should multiple transformations be necessary to adequately follow the vocal folds in the video."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()
