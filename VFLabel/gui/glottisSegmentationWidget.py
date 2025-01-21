import json
import os
from typing import List

from tqdm import tqdm

import cv2
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QPushButton,
    QLabel,
    QComboBox,
    QMessageBox,
    QDialog,
)

from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QSize, Qt
import os

import VFLabel.utils.transforms
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


class WorkerSegmentation(QObject):
    signal_segmentation = pyqtSignal(list, list)
    finished = pyqtSignal()

    def __init__(self, model_dropdown, video):
        super().__init__()
        self.model_dropdown = model_dropdown
        self.video = video

    def segmentation(self) -> None:

        # Load model from dropdown
        encoder = self.model_dropdown.currentText()

        self.segmentations = VFLabel.nn.segmentation.segment_glottis(
            encoder, self.video
        )

        self.glottal_midlines = [
            VFLabel.cv.analysis.glottal_midline(image) for image in tqdm(self.video)
        ]

        self.signal_segmentation.emit(self.segmentations, self.glottal_midlines)
        self.finished.emit()


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

        self.frame_label_left = QLabel("Input Video - Frame: 0")
        self.frame_label_middle = QLabel(f"Segmentation - Frame: 0")
        self.frame_label_right = QLabel(f"Segmentation Overlay - Frame: 0")

        help_icon_path = "assets/icons/help-icon.svg"

        help_opacity_button = QPushButton(QIcon(help_icon_path), "")
        help_opacity_button.setStyleSheet("border: 0px solid #FFF")
        help_opacity_button.clicked.connect(self.help_opacity_dialog)

        help_model_button = QPushButton(QIcon(help_icon_path), "")
        help_model_button.setStyleSheet("border: 0px solid #FFF")
        help_model_button.clicked.connect(self.help_model_dialog)

        help_left_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_left_frame_button.setStyleSheet("border: 0px solid #FFF")
        help_left_frame_button.clicked.connect(self.help_left_frame_dialog)

        video_view_label = QHBoxLayout()
        video_view_label.addStretch(1)
        video_view_label.addWidget(self.frame_label_left)
        video_view_label.addWidget(help_left_frame_button)
        video_view_label.addStretch(1)

        help_right_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_right_frame_button.setStyleSheet("border: 0px solid #FFF")
        help_right_frame_button.clicked.connect(self.help_right_frame_dialog)

        overlay_view_label = QHBoxLayout()
        overlay_view_label.addStretch(1)
        overlay_view_label.addWidget(self.frame_label_right)
        overlay_view_label.addWidget(help_right_frame_button)
        overlay_view_label.addStretch(1)

        help_middle_frame_button = QPushButton(QIcon(help_icon_path), "")
        help_middle_frame_button.setStyleSheet("border: 0px solid #FFF")
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
        horizontal_layout_bot.addWidget(self.opacity_label)
        horizontal_layout_bot.addWidget(help_opacity_button)
        horizontal_layout_bot.addWidget(self.alpha_slider)
        bot_widget.setLayout(horizontal_layout_bot)

        vertical_layout.addWidget(top_widget)
        vertical_layout.addWidget(bot_widget)
        self.setLayout(vertical_layout)

        self.save_button.clicked.connect(self.save)
        self.generate_button.clicked.connect(self.generate_segmentations)
        self.alpha_slider.valueChanged.connect(self.change_opacity)
        self.video_player.slider.valueChanged.connect(self.change_frame)

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

        # side thread

        # create side thread and worker function
        self.thread = QThread()

        self.worker = WorkerSegmentation(self.model_dropdown, self.video)
        self.worker.moveToThread(self.thread)

        # connect signal
        self.thread.started.connect(self.worker.segmentation)
        self.worker.signal_segmentation.connect(self.generate_segmentations_continued)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        # Main Thread

        text = QLabel("Please wait ...")
        text.setAlignment(Qt.AlignCenter)

        # create waiting animation
        gifFile = "assets/loading_symbol.gif"
        self.movie = QMovie(gifFile)
        self.movie.setScaledSize(QSize(50, 50))
        self.movie_label = QLabel(self)
        self.movie_label.setMovie(self.movie)
        self.movie_label.setAlignment(Qt.AlignCenter)
        self.movie.start()

        layout = QVBoxLayout()
        layout.addWidget(text)
        layout.addWidget(self.movie_label)

        # waiting window
        self.dlg_wait = QDialog(self)
        self.dlg_wait.setWindowTitle("Data is processed")
        self.dlg_wait.setLayout(layout)
        self.dlg_wait.setStyleSheet("background-color: white;")
        self.dlg_wait.resize(QSize(400, 200))
        self.dlg_wait.exec()

    def generate_segmentations_continued(self, segmentation, midlines) -> None:

        self.dlg_wait.accept()

        self.segmentations = segmentation
        self.glottal_midlines = midlines

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
            "This window shows the segmentation mask for each frame. To generate the mask click 'Generate'"
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
