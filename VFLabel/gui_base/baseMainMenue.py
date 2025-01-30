import json
import os

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QTextBlockFormat, QTextCursor
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
)

import VFLabel.gui_base.baseWindow as baseWindow


class BaseMainMenue(baseWindow.BaseWindow):
    signal_open_vf_segm_window = pyqtSignal(str)
    signal_close_main_menu_window = pyqtSignal()
    signal_open_glottis_segm_window = pyqtSignal(str)
    signal_open_pt_label_window = pyqtSignal(str)
    signal_open_manual_point_clicking_window = pyqtSignal(str)
    signal_upload_glottis_segmentation = pyqtSignal(bool)

    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.progress_state_path = os.path.join(
            self.project_path, "progress_status.json"
        )

        # create different options buttons
        font = QFont("Arial", 20, QFont.Bold)

        button_glottis_segmentation = QPushButton("Glottis\nSegmentation", self)
        button_glottis_segmentation.setToolTip(
            "In this step of the pipeline, the glottis is segmented and the midline of the glottis is determined. We supply different neural network architectures."
        )
        button_glottis_segmentation.setFont(font)
        button_glottis_segmentation.setFixedSize(200, 100)

        button_vocalfold_segmentation = QPushButton("Vocal Fold\nSegmentation", self)
        button_vocalfold_segmentation.setToolTip(
            "In this step of the pipeline the vocalfold is segmented. This is done by creating a mask of the vocal fold in the first frame. In the last frame, the vocal fold mask is transformed to match the vocal fold in this view. The other frames are interpolated."
        )
        button_vocalfold_segmentation.setFont(font)
        button_vocalfold_segmentation.setFixedSize(200, 100)

        button_track_points = QPushButton("Point\nLabeling", self)
        button_track_points.setToolTip(
            "Here, only a single visible point needs to be selected and they get tracked automatically."
        )
        button_track_points.setFont(font)
        button_track_points.setFixedSize(200, 100)

        button_click_points = QPushButton("Semi-Manual\nPoint Labeling", self)
        button_click_points.setToolTip(
            "If some points were lost or inadequate in the previous step, use this to reassess points semi manually."
        )
        button_click_points.setFont(font)
        button_click_points.setFixedSize(200, 100)

        path_upload_icon = "assets/icons/upload.svg"

        button_load_glottis = QPushButton(QIcon(path_upload_icon), "")
        button_load_glottis.setIconSize(QSize(50, 50))
        button_load_glottis.setStyleSheet("border: 0px solid;")
        button_load_glottis.setToolTip("Upload glottis segmentation data")
        button_load_glottis.clicked.connect(self.upload_glottis_segmentation_data)

        # Using one spacer twice will crash qt. Cringe.
        # See: https://stackoverflow.com/questions/39833793/qspaceritem-crashes-pyqt-when-instantiated-twice
        horizontal_spacer = QSpacerItem(
            60, 20, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        horizontal_spacer_2 = QSpacerItem(
            60, 20, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        # create close button
        font = QFont("Arial", 15, QFont.Bold)
        button_close = QPushButton("Close", self)
        button_close.setToolTip("This <b>button</b> closes this project")
        button_close.setFont(font)
        button_close.setFixedSize(100, 30)

        # create progress text bars
        with open(self.progress_state_path, "r+") as prgrss_file:
            file = json.load(prgrss_file)
            self.progress_glottis_segmentation = QTextEdit(
                file["progress_gl_seg"], readOnly=True
            )
            self.progress_glottis_segmentation.setFixedSize(200, 30)
            self.progress_glottis_segmentation.setTextColor(QColor(0, 0, 0))
            self.color_progress_state(
                self.progress_glottis_segmentation, file["progress_gl_seg"]
            )

            self.progress_vocalfold_segmentation = QTextEdit(
                file["progress_vf_seg"], readOnly=True
            )
            self.progress_vocalfold_segmentation.setFixedSize(200, 30)
            self.progress_vocalfold_segmentation.setTextColor(QColor(0, 0, 0))
            self.color_progress_state(
                self.progress_vocalfold_segmentation, file["progress_vf_seg"]
            )

            self.progress_track_points = QTextEdit(
                file["progress_pt_label"], readOnly=True
            )
            self.progress_track_points.setFixedSize(200, 30)
            self.progress_track_points.setTextColor(QColor(0, 0, 0))
            self.color_progress_state(
                self.progress_track_points, file["progress_pt_label"]
            )

            self.progress_click_points = QTextEdit(
                file["progress_manual_pt_label"], readOnly=True
            )
            self.progress_click_points.setFixedSize(200, 30)
            self.progress_click_points.setTextColor(QColor(0, 0, 0))
            self.color_progress_state(
                self.progress_click_points, file["progress_manual_pt_label"]
            )

        # centralize text of progress text bars
        self.centralize_text(self.progress_glottis_segmentation)
        self.centralize_text(self.progress_vocalfold_segmentation)
        self.centralize_text(self.progress_track_points)
        self.centralize_text(self.progress_click_points)

        # create number text bars
        label_glottis_segmentation = QLabel("1.")
        label_glottis_segmentation.setFixedSize(200, 30)
        label_vocalfold_segmentation = QLabel("2.")
        label_vocalfold_segmentation.setFixedSize(200, 30)
        label_track_points = QLabel("3.")
        label_track_points.setFixedSize(200, 30)
        label_click_points = QLabel("4.")
        label_click_points.setFixedSize(200, 30)

        # centralize text of progress num bars
        label_glottis_segmentation.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        label_vocalfold_segmentation.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        label_track_points.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        label_click_points.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # create layout
        layout_horizontal_button = QHBoxLayout()
        layout_horizontal_progress = QHBoxLayout()
        layout_horizontal_close = QHBoxLayout()
        layout_horizontal_label = QHBoxLayout()
        vertical_layout = QVBoxLayout()

        # insert buttons in window
        layout_horizontal_button.addStretch(1)
        layout_horizontal_button.addWidget(button_glottis_segmentation)
        layout_horizontal_button.addWidget(button_load_glottis)
        layout_horizontal_button.addStretch(1)
        layout_horizontal_button.addWidget(button_vocalfold_segmentation)
        layout_horizontal_button.addStretch(1)
        layout_horizontal_button.addWidget(button_track_points)
        layout_horizontal_button.addStretch(1)
        layout_horizontal_button.addWidget(button_click_points)
        layout_horizontal_button.addStretch(1)

        # insert progress text in window
        layout_horizontal_progress.addStretch(1)
        layout_horizontal_progress.addWidget(self.progress_glottis_segmentation)
        layout_horizontal_progress.addItem(horizontal_spacer)
        layout_horizontal_progress.addStretch(1)
        layout_horizontal_progress.addWidget(self.progress_vocalfold_segmentation)
        layout_horizontal_progress.addStretch(1)
        layout_horizontal_progress.addWidget(self.progress_track_points)
        layout_horizontal_progress.addStretch(1)
        layout_horizontal_progress.addWidget(self.progress_click_points)
        layout_horizontal_progress.addStretch(1)

        # insert number text in window
        layout_horizontal_label.addStretch(1)
        layout_horizontal_label.addWidget(label_glottis_segmentation)
        layout_horizontal_label.addItem(horizontal_spacer_2)
        layout_horizontal_label.addStretch(1)
        layout_horizontal_label.addWidget(label_vocalfold_segmentation)
        layout_horizontal_label.addStretch(1)
        layout_horizontal_label.addWidget(label_track_points)
        layout_horizontal_label.addStretch(1)
        layout_horizontal_label.addWidget(label_click_points)
        layout_horizontal_label.addStretch(1)

        # insert close button in window
        layout_horizontal_close.addStretch(1)
        layout_horizontal_close.addWidget(button_close)

        # combine layouts
        vertical_layout.setContentsMargins(50, 50, 50, 50)
        vertical_layout.addStretch(1)
        vertical_layout.addLayout(layout_horizontal_label)
        vertical_layout.addLayout(layout_horizontal_button)
        vertical_layout.addLayout(layout_horizontal_progress)
        vertical_layout.addStretch(1)
        vertical_layout.addLayout(layout_horizontal_close)

        # adding functionality to buttons
        button_glottis_segmentation.clicked.connect(self.open_glottis_segmentation)
        button_vocalfold_segmentation.clicked.connect(self.open_vf_segmentation)
        button_track_points.clicked.connect(self.open_point_clicking)
        button_click_points.clicked.connect(self.open_manual_point_clicking)
        button_close.clicked.connect(self.close_window)

        # set layout
        self.setLayout(vertical_layout)

        # show window
        self.show()

    def upload_glottis_segmentation_data(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Upload glottis Segmentation")
        dlg.setText("Do you want to upload the glottis segmentation ?")
        button_video = dlg.addButton("Upload as video", QMessageBox.YesRole)
        button_folder = dlg.addButton(
            "Upload as folder with images", QMessageBox.NoRole
        )
        dlg.addButton("Cancel", QMessageBox.RejectRole)
        # dlg.setStandardButtons(QMessageBox.Cancel)
        dlg.adjustSize()
        dlg.exec()

        if dlg.clickedButton() == button_video:
            as_video = True
        elif dlg.clickedButton() == button_folder:
            as_video = False
        else:
            return

        self.signal_upload_glottis_segmentation.emit(as_video)

    def open_glottis_segmentation(self) -> None:
        self.signal_open_glottis_segm_window.emit(self.project_path)

    def open_vf_segmentation(self) -> None:
        self.signal_open_vf_segm_window.emit(self.project_path)

    def open_point_clicking(self) -> None:
        self.signal_open_pt_label_window.emit(self.project_path)

    def open_manual_point_clicking(self) -> None:
        self.signal_open_manual_point_clicking_window.emit(self.project_path)

    def color_progress_state(self, state_variable, state: str):
        if state == "finished":
            state_variable.setStyleSheet(
                "background-color: rgb(144, 238, 144); color: black;"
            )
        elif state == "in progress":
            state_variable.setStyleSheet(
                "background-color: rgb(173, 216, 230); color: black;"
            )
        elif state == "not started":
            state_variable.setStyleSheet(
                "background-color: rgb(211, 211, 211); color: black;"
            )
        else:
            pass

    def centralize_text(self, widget) -> None:
        cursor = widget.textCursor()
        cursor.select(QTextCursor.Document)
        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignCenter)
        cursor.mergeBlockFormat(block_format)

    def help(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Main Menu")
        dlg.setText(
            "This is the main menu. There are three tasks that need to be completed: \n"
            "- glottis segmentation \n"
            "- vocalfold segmentation \n"
            "- point labeling \n"
            " All three tasks need to be marked as completed."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.adjustSize()
        dlg.exec()

    def close_window(self):
        self.signal_close_main_menu_window.emit()
