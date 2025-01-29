import json
import os
from typing import List

import albumentations as A
import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch
from albumentations.pytorch import ToTensorV2
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

import VFLabel.cv.analysis
import VFLabel.cv.segmentation
import VFLabel.gui.drawSegmentationWidget
import VFLabel.gui.interpolateSegmentationWidget
import VFLabel.gui.transformSegmentationWidget
import VFLabel.gui.videoOverlayWithGMWidget
import VFLabel.gui.videoPlayerWidget
import VFLabel.gui.videoViewWidget
import VFLabel.gui.zoomableViewWidget
import VFLabel.io.data
import VFLabel.nn.segmentation
import VFLabel.utils.transforms
import VFLabel.utils.utils
from VFLabel.gui.progressDialog import ProgressDialog
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
        self.segmentation_view = VFLabel.gui.GlottisSegmentationMaskView(
            qvideo_segmentations if self.segmentations else None,
            project_path,
            self,
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
        self.alpha_slider.setValue(80)

        self.generate_button = QPushButton("Generate")

        self.save_button = QPushButton("Save")

        self.edit_mask_button = QCheckBox("Edit Mask")
        self.reload_overlay_button = QPushButton("Recompute Midline")

        self.frame_label_left = QLabel("Input Video - Frame: 0")
        self.frame_label_middle = QLabel(f"Segmentation - Frame: 0")
        self.frame_label_right = QLabel(f"Segmentation Overlay - Frame: 0")

        help_icon_path = "assets/icons/help.svg"

        help_opacity_button = QPushButton(QIcon(help_icon_path), "")
        help_opacity_button.clicked.connect(self.help_opacity_dialog)

        help_model_button = QPushButton(QIcon(help_icon_path), "")
        help_model_button.clicked.connect(self.help_model_dialog)

        help_left_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_left_frame_button.clicked.connect(self.help_left_frame_dialog)

        video_view_label = QHBoxLayout()
        video_view_label.addStretch(1)
        video_view_label.addWidget(self.frame_label_left)
        video_view_label.addWidget(help_left_frame_button)
        video_view_label.addStretch(1)

        help_right_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_right_frame_button.clicked.connect(self.help_right_frame_dialog)

        overlay_view_label = QHBoxLayout()
        overlay_view_label.addStretch(1)
        overlay_view_label.addWidget(self.frame_label_right)
        overlay_view_label.addWidget(help_right_frame_button)
        overlay_view_label.addStretch(1)

        help_middle_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_middle_frame_button.clicked.connect(self.help_middle_frame_dialog)

        segmentation_view_label = QHBoxLayout()
        segmentation_view_label.addStretch(1)
        segmentation_view_label.addWidget(self.frame_label_middle)
        segmentation_view_label.addWidget(help_middle_frame_button)
        segmentation_view_label.addStretch(1)

        vertical_video_view_widget = QWidget()
        vertical_video_view = QVBoxLayout()
        vertical_video_view.addLayout(video_view_label)
        vertical_video_view.addWidget(self.video_view)
        vertical_video_view_widget.setLayout(vertical_video_view)

        vertical_segmentation_view_widget = QWidget()
        vertical_segmentation_view = QVBoxLayout()
        vertical_segmentation_view.addLayout(segmentation_view_label)
        vertical_segmentation_view.addWidget(self.segmentation_view)
        vertical_segmentation_view_widget.setLayout(vertical_segmentation_view)

        vertical_overlay_view_widget = QWidget()
        vertical_overlay_view = QVBoxLayout()
        vertical_overlay_view.addLayout(overlay_view_label)
        vertical_overlay_view.addWidget(self.overlay_view)
        vertical_overlay_view_widget.setLayout(vertical_overlay_view)

        horizontal_layout_top.addWidget(vertical_video_view_widget)
        horizontal_layout_top.addWidget(vertical_segmentation_view_widget)
        horizontal_layout_top.addWidget(vertical_overlay_view_widget)
        top_widget.setLayout(horizontal_layout_top)

        horizontal_layout_bot.addWidget(self.model_label)
        horizontal_layout_bot.addWidget(help_model_button)
        horizontal_layout_bot.addWidget(self.model_dropdown)
        horizontal_layout_bot.addWidget(self.generate_button)
        horizontal_layout_bot.addWidget(self.video_player)
        horizontal_layout_bot.addWidget(self.save_button)
        horizontal_layout_bot.addWidget(self.edit_mask_button)
        horizontal_layout_bot.addWidget(self.reload_overlay_button)
        horizontal_layout_bot.addWidget(self.opacity_label)
        horizontal_layout_bot.addWidget(help_opacity_button)
        horizontal_layout_bot.addWidget(self.alpha_slider)
        bot_widget.setLayout(horizontal_layout_bot)

        vertical_layout.addWidget(top_widget)
        vertical_layout.addWidget(bot_widget)
        self.setLayout(vertical_layout)

        self.save_button.clicked.connect(self.save)
        self.edit_mask_button.clicked.connect(self.segmentation_view.toggle_draw_state)
        self.reload_overlay_button.clicked.connect(self.reload_overlay)
        self.generate_button.clicked.connect(self.generate_segmentations)
        self.alpha_slider.valueChanged.connect(self.change_opacity)
        self.video_player.slider.valueChanged.connect(self.change_frame)
        self.overlay_view.signal_opacity_slider.connect(self.update_alpha_slider)
        self.video_view.signal_decrement_frame.connect(
            self.video_player.decrement_frame
        )
        self.video_view.signal_increment_frame.connect(
            self.video_player.increment_frame
        )

        self.segmentation_view.signal_decrement_frame.connect(
            self.video_player.decrement_frame
        )
        self.segmentation_view.signal_increment_frame.connect(
            self.video_player.increment_frame
        )

        self.overlay_view.signal_decrement_frame.connect(
            self.video_player.decrement_frame
        )
        self.overlay_view.signal_increment_frame.connect(
            self.video_player.increment_frame
        )

    def change_frame_label(self, value):
        self.frame_label_left.setText(f"Input Video - Frame: {value}")
        self.frame_label_middle.setText(f"Segmentation - Frame: {value}")
        self.frame_label_right.setText(f"Segmentation Overlay - Frame: {value}")

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
        encoder = self.model_dropdown.currentText()
        model_path = os.path.join("assets", "models", f"glottis_{encoder}.pth.tar")

        DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

        model = smp.Unet(
            encoder_name=encoder,  # choose encoder, e.g. mobilenet_v2 or efficientnet-b7
            encoder_weights="imagenet",  # use `imagenet` pre-trained weights for encoder initialization
            in_channels=3,  # model input channels (1 for gray-scale images, 3 for RGB, etc.)
            classes=1,
        ).to(DEVICE)
        state_dict = torch.load(
            model_path, map_location=torch.device(DEVICE), weights_only=True
        )

        if "optimizer" in state_dict:
            del state_dict["optimizer"]

        model.load_state_dict(state_dict)

        transform = A.Compose(
            [
                A.Normalize(),
                ToTensorV2(),
            ]
        )

        self.segmentations = []

        for image in ProgressDialog(self.video, "Segmenting"):
            augmentations = transform(image=image)
            image = augmentations["image"]

            image = image.to(device=DEVICE).unsqueeze(0)

            pred_seg = model(image).squeeze()
            sigmoid = pred_seg.sigmoid()
            segmentation = (sigmoid > 0.5) * 255
            self.segmentations.append(segmentation.detach().cpu().numpy())

        self.glottal_midlines = [
            VFLabel.cv.analysis.glottal_midline(image)
            for image in ProgressDialog(self.segmentations, "Glottal Midline")
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

        glottal_midline_dict = {}
        for frame_index, midline_points in enumerate(self.glottal_midlines):
            upper = midline_points[0]
            lower = midline_points[1]

            glottal_midline_dict[f"Frame{frame_index}"] = {
                "Upper": upper.tolist() if upper is not None else [-1, -1],
                "Lower": lower.tolist() if lower is not None else [-1, -1],
            }
        self.overlay_view.set_glottal_midlines_array(glottal_midline_dict)
        self.overlay_view.redraw()

    def save(self) -> None:
        self.segmentation_view.save_segmentation_mask()
        images_list = self.segmentation_view.qImage_list_2_black_white_np_list(
            self.segmentation_view.images
        )

        glottal_midlines_path = os.path.join(self.project_path, "glottal_midlines.json")

        self.glottal_midlines = [
            self.calculate_glottis_midline_one_frame(image)
            for image in ProgressDialog(images_list, "Glottal Midline")
        ]

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

    def calculate_glottis_midline_one_frame(self, image: np.array):
        if image.shape[-1] == 4:
            midline = VFLabel.cv.analysis.glottal_midline(image[:, :, 0:3])
        elif image.shape[-1] == 3:
            midline = VFLabel.cv.analysis.glottal_midline(image)
        else:
            midline = None

        return midline

    def reload_overlay(self):
        last_mode = self.segmentation_view.draw_mode
        self.segmentation_view.draw_mode = VFLabel.utils.enums.DRAW_MODE.OFF
        self.segmentation_view.redraw()

        images = self.segmentation_view.generate_new_segmentations()

        images_bw = self.segmentation_view.qImage_list_2_black_white_np_list(images)
        images_colored = [
            VFLabel.utils.transforms.qImage_2_np(image) for image in images
        ]

        # glottis segmentation
        # for idx, img in enumerate(images):
        #    images[idx][np.sum(img, axis=-1) > 0] = COLOR.GLOTTIS

        segmentations_with_alpha = [
            VFLabel.utils.utils.add_alpha_to_segmentations(seg)
            for seg in images_colored
        ]

        overlays = VFLabel.utils.transforms.vid_2_QImage(segmentations_with_alpha)
        self.overlay_view.add_overlay(overlays)

        # glottal midline
        self.glottal_midlines = [
            self.calculate_glottis_midline_one_frame(image)
            for image in ProgressDialog(images_bw, "Glottal Midline")
        ]

        glottal_midline_dict = {}
        for frame_index, midline_points in enumerate(self.glottal_midlines):
            upper = midline_points[0]
            lower = midline_points[1]

            glottal_midline_dict[f"Frame{frame_index}"] = {
                "Upper": upper.tolist() if upper is not None else [-1, -1],
                "Lower": lower.tolist() if lower is not None else [-1, -1],
            }
        self.overlay_view.set_glottal_midlines_array(glottal_midline_dict)

        self.segmentation_view.draw_mode = last_mode
        self.overlay_view.redraw()

    def change_opacity(self) -> None:
        self.overlay_view.set_opacity(self.alpha_slider.value() / 100)

    def update_alpha_slider(self, alpha):
        self.alpha_slider.setValue(alpha)

    def change_frame(self) -> None:
        self.video_view.change_frame(self.video_player.slider.value())
        self.segmentation_view.change_frame(self.video_player.slider.value())
        self.overlay_view.change_frame(self.video_player.slider.value())
        self.change_frame_label(self.video_player.slider.value())

    def help_left_frame_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Input Video")
        dlg.setText("This view shows the input video.")
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_middle_frame_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Segmentation View")
        dlg.setText(
            "This window shows the segmentation mask for each frame. To generate the mask click 'Generate'. After generation, the mask can be manually adjusted (false green areas can be removed)."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_right_frame_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Segmentation Overlay")
        dlg.setText(
            "This window shows an overlay of the video frames and the segmentation mask."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_opacity_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Opacity slider")
        dlg.setText(
            "This slider adjusts the opacity of the segmentation mask in the Segmentation Overlay."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def help_model_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Model")
        dlg.setText(
            "Choose a model from the dropdown list and press 'Generate' in order to generate a segmentation mask of the glottis."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()
