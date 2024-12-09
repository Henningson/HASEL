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
)

from PyQt5.QtGui import (
    QIcon,
    QPen,
    QBrush,
    QPolygonF,
    QColor,
    QPixmap,
)
import os

import VFLabel.utils.transforms

import VFLabel.gui.drawSegmentationWidget
import VFLabel.gui.transformSegmentationWidget
import VFLabel.gui.interpolateSegmentationWidget
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

    def __init__(self, project_path: str, video: np.array, parent=None):
        super(VocalfoldSegmentationWidget, self).__init__(parent)
        self.project_path = project_path

        self.setStyleSheet("background-color:white")

        vertical_layout = QVBoxLayout()
        horizontal_layout_top = QHBoxLayout()
        top_widget = QWidget()
        horizontal_layout_bot = QHBoxLayout()
        bot_widget = QWidget()
        segment_widget = QWidget()

        self.qvideo = VFLabel.utils.transforms.vid_2_QImage(video)
        video_height = video.shape[1]
        video_width = video.shape[2]

        self.draw_view = VFLabel.gui.drawSegmentationWidget.DrawSegmentationWidget(
            image_height=video_height, image_width=video_width
        )
        self.draw_view.set_image(self.qvideo[0])

        self.move_view = (
            VFLabel.gui.transformSegmentationWidget.TransformSegmentationWidget(
                self.qvideo[-1], None
            )
        )

        self.interpolate_view = (
            VFLabel.gui.interpolateSegmentationWidget.InterpolateSegmentationWidget(
                self.qvideo, None, [0.0, 0.0, 1.0, 0.0]
            )
        )

        self.video_player = VFLabel.gui.videoPlayerWidget.VideoPlayerWidget(
            len(self.qvideo), 100
        )

        frame_label_widget = self.initialization_frame_label(
            len(self.qvideo), video_width
        )
        self.video_player.signal_current_frame.connect(
            self.update_signal_label_current_frame
        )

        self.segment_slider = VFLabel.gui.vocalfoldSegmentationSliderWidget.VocalfoldSegmentationSliderWidget(
            len(self.qvideo)
        )

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

        add_btn = QPushButton("add mark")
        remove_btn = QPushButton("remove mark")

        add_btn.clicked.connect(self.add_mark)
        remove_btn.clicked.connect(self.remove_mark)

        seg_slider_layout = QHBoxLayout()
        seg_slider_layout.addWidget(self.segment_slider)
        seg_slider_layout.setSpacing(1)
        seg_slider_layout.addWidget(add_btn)
        seg_slider_layout.addWidget(remove_btn)
        segment_widget.setLayout(seg_slider_layout)

        self.save_button = QPushButton("Save")

        self.save_button.clicked.connect(self.save)

        horizontal_layout_top.addWidget(self.draw_view)
        horizontal_layout_top.addWidget(self.move_view)
        horizontal_layout_top.addWidget(self.interpolate_view)
        top_widget.setLayout(horizontal_layout_top)

        horizontal_layout_bot.addWidget(self.video_player)
        horizontal_layout_bot.addWidget(self.save_button)
        bot_widget.setLayout(horizontal_layout_bot)

        vertical_layout.addWidget(frame_label_widget)
        vertical_layout.addWidget(top_widget)
        vertical_layout.addWidget(bot_widget)
        vertical_layout.addWidget(segment_widget)
        self.setLayout(vertical_layout)

        self.draw_view.segmentation_updated.connect(self.add_polygon_to_transform_view)
        self.video_player.slider.valueChanged.connect(self.change_frame)
        self.move_view.transform_updated.connect(
            self.add_transform_to_interpolation_view
        )

    def save(self) -> None:
        save_folder = os.path.join(self.project_path, "vocalfold_segmentation")
        os.makedirs(save_folder, exist_ok=True)

        for i in range(self.video_player.get_video_length()):
            pixmap = self.interpolate_view.generate_segmentation_for_frame(i)
            path = os.path.join(save_folder, f"{i:05d}.png")
            pixmap.save(path)

        self.close()

    def add_polygon_to_transform_view(self) -> None:
        polygon = QPolygonF(self.draw_view.getPolygonPoints())
        self.move_view.add_polygon(polygon)
        self.interpolate_view.add_polygon(polygon)

    def add_transform_to_interpolation_view(self) -> None:
        self.interpolate_view.update_transforms(*self.move_view.get_transform())

    def change_frame(self) -> None:
        self.interpolate_view.change_frame(self.video_player.slider.value())

    def add_mark(self):
        value = self.video_player.slider.value()
        self.signal_new_mark.emit(value)

    def remove_mark(self):
        value = self.video_player.slider.value()
        self.signal_remove_mark.emit(value)

    def update_signal_btn_pressed_position(self, position):
        self.video_player.slider.setValue(position)
        self.video_player.update_current_from_slider()

    def update_signal_begin_btn_pressed(self, position):
        self.video_player.slider.setValue(position)
        self.begin_segment = position
        self.video_player.update_current_from_slider()
        # set first frame
        self.draw_view.set_image(self.qvideo[self.begin_segment])
        self.frame_start_no.setText(f"First frame {self.begin_segment}")

    def update_signal_end_btn_pressed(self, position):
        self.end_segment = position
        # set last frame
        self.move_view.set_image(self.qvideo[self.end_segment])
        self.frame_end_no.setText(f"Last frame {position}")

    def update_signal_label_current_frame(self, frame):
        self.frame_current_no.setText(f"Current frame {frame}")

    def initialization_frame_label(self, length_video, video_width) -> QWidget:
        frame_label_widget = QWidget()

        # create number text bars
        self.frame_start_no = QLabel("First frame 0")
        self.frame_start_no.setFixedSize(110, 30)
        self.frame_end_no = QLabel(f"Last frame {length_video - 1}")
        self.frame_end_no.setFixedSize(110, 30)
        self.frame_current_no = QLabel(
            f"Current frame {self.video_player._current_frame}"
        )
        self.frame_current_no.setFixedSize(110, 30)

        # insert number text in window
        boxh_frame_no_layout = QHBoxLayout()
        boxh_frame_no_layout.addStretch(1)
        boxh_frame_no_layout.addWidget(self.frame_start_no)
        boxh_frame_no_layout.addStretch(1)
        boxh_frame_no_layout.addWidget(self.frame_end_no)
        boxh_frame_no_layout.addStretch(1)
        boxh_frame_no_layout.addWidget(self.frame_current_no)
        boxh_frame_no_layout.addStretch(1)
        frame_label_widget.setLayout(boxh_frame_no_layout)

        return frame_label_widget
