from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout


from PyQt5 import QtCore
import numpy as np
import json

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

from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor, QPixmap, QImage
import os

import VFLabel.utils.transforms

import VFLabel.gui.drawSegmentationWidget
import VFLabel.gui.transformSegmentationWidget
import VFLabel.gui.interpolateSegmentationWidget
import VFLabel.gui.videoPlayerWidget
import VFLabel.gui.videoViewWidget
import VFLabel.gui.zoomableViewWidget
import VFLabel.gui.videoOverlayWithGMWidget

import VFLabel.utils.transforms
import VFLabel.io.data
import VFLabel.utils.utils
import VFLabel.cv.segmentation
import VFLabel.cv.analysis
import VFLabel.nn.segmentation
import cv2

from VFLabel.utils.defines import COLOR
from typing import List

from tqdm import tqdm

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


class GlottisSegmentationWidget(QWidget):
    def __init__(self, project_path: str, video: np.array, parent=None):
        super(GlottisSegmentationWidget, self).__init__(parent)
        vertical_layout = QVBoxLayout()
        horizontal_layout_top = QHBoxLayout()
        top_widget = QWidget()
        horizontal_layout_bot = QHBoxLayout()
        bot_widget = QWidget()
        self.project_path = project_path
        self.glottis_path = os.path.join(project_path, "glottis_segmentation")

        self.video = video
        qvideo = VFLabel.utils.transforms.vid_2_QImage(video)

        self.segmentations: List[np.array] = []
        self.glottal_midlines: List[np.array] = []

        qvideo_segmentations = None
        segmentations_with_alpha = None
        glottal_midlines = None
        if os.listdir(self.glottis_path):
            self.segmentations = self.load_segmentations_from_folder(self.glottis_path)
            qvideo_segmentations = VFLabel.utils.transforms.vid_2_QImage(
                self.segmentations
            )
            segmentations_with_alpha = [
                VFLabel.utils.utils.add_alpha_to_segmentations(seg)
                for seg in self.segmentations
            ]
            segmentations_with_alpha = VFLabel.utils.transforms.vid_2_QImage(
                segmentations_with_alpha
            )

            glottal_midlines = VFLabel.io.dict_from_json(
                os.path.join(self.project_path, "glottal_midlines.json")
            )

        self.video_view = VFLabel.gui.videoViewWidget.VideoViewWidget(qvideo)
        self.segmentation_view = VFLabel.gui.videoViewWidget.VideoViewWidget(
            qvideo_segmentations if self.segmentations else None
        )
        self.overlay_view = (
            VFLabel.gui.videoOverlayWithGMWidget.VideoOverlayGlottalMidlineWidget(
                qvideo, segmentations_with_alpha, glottal_midlines
            )
        )

        self.video_player = VFLabel.gui.videoPlayerWidget.VideoPlayerWidget(
            len(qvideo), 100
        )

        self.model_label = QLabel("Segmentation Model")
        self.model_dropdown = QComboBox(self)

        model_path = "assets/models/"
        models = os.listdir(model_path)
        models = [
            model for model in models if "glottis" in model and ".pth.tar" in model
        ]
        models = [
            model.replace("glottis_", "").replace(".pth.tar", "") for model in models
        ]
        self.model_dropdown.addItems(models)

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

    def load_segmentations_from_folder(self, path) -> List[np.array]:
        segmentations = []
        for file in sorted(os.listdir(path)):
            file_path = os.path.join(path, file)
            image = cv2.imread(file_path, 0) // 255
            colored = VFLabel.utils.utils.class_to_color_np(
                image, [COLOR.BACKGROUND, COLOR.GLOTTIS]
            ).astype(np.uint8)
            segmentations.append(np.array(colored))
        return segmentations

    def generate_segmentations(self) -> None:
        # Load model from dropdown
        encoder = self.model_dropdown.currentText()

        self.segmentations = VFLabel.nn.segmentation.segment_glottis(
            encoder, self.video
        )

        self.glottal_midlines = [
            VFLabel.cv.analysis.glottal_midline(image) for image in tqdm(self.video)
        ]

        normalized = [image // 255 for image in self.segmentations]
        colored = [
            VFLabel.utils.utils.class_to_color_np(
                image, [COLOR.BACKGROUND, COLOR.GLOTTIS]
            ).astype(np.uint8)
            for image in normalized
        ]
        colored = np.array(colored)
        segmentations_with_alpha = [
            VFLabel.utils.utils.add_alpha_to_segmentations(seg) for seg in colored
        ]

        colored = VFLabel.utils.transforms.vid_2_QImage(colored)
        overlays = VFLabel.utils.transforms.vid_2_QImage(segmentations_with_alpha)
        self.segmentation_view.add_video(colored)
        self.overlay_view.add_overlay(overlays)

        self.segmentation_view.redraw()
        self.overlay_view.redraw()

    def save(self) -> None:
        segmentation_path = os.path.join(self.project_path, "glottis_segmentation")
        glottal_midlines_path = os.path.join(self.project_path, "glottal_midlines.json")

        glottal_midline_dict = {}
        for frame_index, midline_points in enumerate(self.glottal_midlines):
            upper = midline_points[0]
            lower = midline_points[1]

            glottal_midline_dict[f"Frame{frame_index}"] = {
                "Upper": upper.tolist() if upper is not None else [-1, -1],
                "Lower": lower.tolist() if lower is not None else [-1, -1],
            }

        with open(glottal_midlines_path, "w+") as outfile:
            json.dump(glottal_midline_dict, outfile)

        for frame_index, seg in enumerate(self.segmentations):
            image_save_path = os.path.join(segmentation_path, f"{frame_index:05d}.png")
            cv2.imwrite(image_save_path, seg)

    def change_opacity(self) -> None:
        self.overlay_view.set_opacity(self.alpha_slider.value() / 100)

    def change_frame(self) -> None:
        self.video_view.change_frame(self.video_player.slider.value())
        self.segmentation_view.change_frame(self.video_player.slider.value())
        self.overlay_view.change_frame(self.video_player.slider.value())
