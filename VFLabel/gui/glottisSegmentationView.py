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
import VFLabel.gui.videoViewWidget
import VFLabel.gui.zoomableViewWidget
import VFLabel.gui.videoOverlayWidget

import VFLabel.utils.transforms
import VFLabel.io.data
import VFLabel.utils.utils

from VFLabel.utils.defines import COLOR

############################### ^
#         #         #         # |
#         #         #         # |
#  VIDEO  #  SEGMEN # VID     # |
#         #         # + SEG   # |
#         #         #         # |
#         #         #         # |
############################### |
#  VIDPLAYE # DROP  # GENERATE# |
############################### v


class GlottisSegmentationView(QWidget):
    def __init__(self, video: np.array, parent=None):
        super(GlottisSegmentationView, self).__init__(parent)
        vertical_layout = QVBoxLayout()
        horizontal_layout_top = QHBoxLayout()
        top_widget = QWidget()
        horizontal_layout_bot = QHBoxLayout()
        bot_widget = QWidget()

        qvideo = VFLabel.utils.transforms.vid_2_QImage(video)
        self.video_view = VFLabel.gui.videoViewWidget.VideoViewWidget(qvideo)
        self.segmentation_view = VFLabel.gui.videoViewWidget.VideoViewWidget()
        self.overlay_view = VFLabel.gui.videoOverlayWidget.VideoOverlayWidget(
            qvideo, None
        )

        self.video_player = VFLabel.gui.videoPlayerWidget.VideoPlayerWidget(
            len(qvideo), 100
        )

        self.model_label = QLabel("Segmentation Model")
        self.model_dropdown = QComboBox(self)
        self.model_dropdown.addItem("Model A")
        self.model_dropdown.addItem("Model B")
        self.model_dropdown.addItem("Model C")

        self.opacity_label = QLabel("Opacity:")
        self.alpha_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(0, 100)

        self.generate_button = QPushButton("Generate")

        self.save_button = QPushButton("Save")

        horizontal_layout_top.addWidget(self.video_view)
        horizontal_layout_top.addWidget(self.segmentation_view)
        horizontal_layout_top.addWidget(self.overlay_view)
        top_widget.setLayout(horizontal_layout_top)

        horizontal_layout_bot.addWidget(self.model_label)
        horizontal_layout_bot.addWidget(self.model_dropdown)
        horizontal_layout_bot.addWidget(self.generate_button)
        horizontal_layout_bot.addWidget(self.video_player)
        horizontal_layout_bot.addWidget(self.save_button)
        horizontal_layout_bot.addWidget(self.opacity_label)
        horizontal_layout_bot.addWidget(self.alpha_slider)
        bot_widget.setLayout(horizontal_layout_bot)

        vertical_layout.addWidget(top_widget)
        vertical_layout.addWidget(bot_widget)
        self.setLayout(vertical_layout)

        self.save_button.clicked.connect(self.save)
        self.generate_button.clicked.connect(self.generate_segmentations)
        self.alpha_slider.valueChanged.connect(self.change_opacity)
        self.video_player.slider.valueChanged.connect(self.change_frame)

    def generate_segmentations(self) -> None:
        # Load model from dropdown

        # Generate segmentations with given model.

        # Set the segmentation images
        images = VFLabel.io.data.read_images_from_folder(
            "assets/test_data/CF/glottal_mask", is_gray=1
        )
        normalized = [image // 255 for image in images]
        colored = [
            VFLabel.utils.utils.class_to_color_np(
                image, [COLOR.BACKGROUND, COLOR.GLOTTIS]
            ).astype(np.uint8)
            for image in normalized
        ]
        colored = np.array(colored)

        colored = VFLabel.utils.transforms.vid_2_QImage(colored)
        self.segmentation_view.add_video(colored)
        self.overlay_view.add_overlay(colored)

        self.segmentation_view.redraw()
        self.overlay_view.redraw()

    def save(self) -> None:
        save_folder = QFileDialog.getExistingDirectory(
            self, "Save Frames to", "", QFileDialog.ShowDirsOnly
        )

        for i in range(self.video_player.get_video_length()):
            pixmap = self.interpolate_view.generate_segmentation_for_frame(i)
            path = os.path.join(save_folder, f"{i:05d}.png")
            pixmap.save(path)

    def change_opacity(self) -> None:
        self.overlay_view.set_opacity(self.alpha_slider.value() / 100)

    def change_frame(self) -> None:
        self.video_view.change_frame(self.video_player.slider.value())
        self.segmentation_view.change_frame(self.video_player.slider.value())
        self.overlay_view.change_frame(self.video_player.slider.value())
