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
    def __init__(self, video: np.array, parent=None):
        super(VocalfoldSegmentationWidget, self).__init__(parent)

        vertical_layout = QVBoxLayout()
        horizontal_layout_top = QHBoxLayout()
        top_widget = QWidget()
        horizontal_layout_bot = QHBoxLayout()
        bot_widget = QWidget()

        qvideo = VFLabel.utils.transforms.vid_2_QImage(video)
        video_height = video.shape[1]
        video_width = video.shape[2]

        self.draw_view = VFLabel.gui.drawSegmentationWidget.DrawSegmentationWidget(
            image_height=video_height, image_width=video_width
        )
        self.draw_view.set_image(qvideo[0])

        self.move_view = (
            VFLabel.gui.transformSegmentationWidget.TransformSegmentationWidget(
                qvideo[-1], None
            )
        )

        self.interpolate_view = (
            VFLabel.gui.interpolateSegmentationWidget.InterpolateSegmentationWidget(
                qvideo, None, [0.0, 0.0, 1.0, 0.0]
            )
        )

        self.video_player = VFLabel.gui.videoPlayerWidget.VideoPlayerWidget(
            len(qvideo), 100
        )

        self.save_button = QPushButton("Save")

        self.save_button.clicked.connect(self.save)

        horizontal_layout_top.addWidget(self.draw_view)
        horizontal_layout_top.addWidget(self.move_view)
        horizontal_layout_top.addWidget(self.interpolate_view)
        top_widget.setLayout(horizontal_layout_top)

        horizontal_layout_bot.addWidget(self.video_player)
        horizontal_layout_bot.addWidget(self.save_button)
        bot_widget.setLayout(horizontal_layout_bot)

        vertical_layout.addWidget(top_widget)
        vertical_layout.addWidget(bot_widget)
        self.setLayout(vertical_layout)

        self.draw_view.segmentation_updated.connect(self.add_polygon_to_transform_view)
        self.video_player.slider.valueChanged.connect(self.change_frame)
        self.move_view.transform_updated.connect(
            self.add_transform_to_interpolation_view
        )

    def save(self) -> None:
        save_folder = QFileDialog.getExistingDirectory(
            self, "Save Frames to", "", QFileDialog.ShowDirsOnly
        )

        for i in range(self.video_player.get_video_length()):
            pixmap = self.interpolate_view.generate_segmentation_for_frame(i)
            path = os.path.join(save_folder, f"{i:05d}.png")
            pixmap.save(path)

    def add_polygon_to_transform_view(self) -> None:
        polygon = QPolygonF(self.draw_view.getPolygonPoints())
        self.move_view.add_polygon(polygon)
        self.interpolate_view.add_polygon(polygon)

    def add_transform_to_interpolation_view(self) -> None:
        self.interpolate_view.update_transforms(*self.move_view.get_transform())

    def change_frame(self) -> None:
        self.interpolate_view.change_frame(self.video_player.slider.value())
