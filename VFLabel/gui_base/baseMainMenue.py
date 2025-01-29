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

        button_point_tracking = QPushButton("Point\nLabeling", self)
        button_point_tracking.setToolTip(
            "Here, only a single visible point needs to be selected and they get tracked automatically."
        )
        button_point_tracking.setFont(font)
        button_point_tracking.setFixedSize(200, 100)

        button_point_clicking = QPushButton("Semi-Manual\nPoint Labeling", self)
        button_point_clicking.setToolTip(
            "If some points were lost or inadequate in the previous step, use this to reassess points semi manually."
        )
        button_point_clicking.setFont(font)
        button_point_clicking.setFixedSize(200, 100)

        path_upload_icon = "assets/icons/upload.svg"
        button_load_glottis_segmentation = QPushButton(QIcon(path_upload_icon), "")
        button_load_glottis_segmentation.setIconSize(QSize(50, 50))
        button_load_glottis_segmentation.setStyleSheet("border: 0px solid;")
        button_load_glottis_segmentation.setToolTip("Upload glottis segmentation data")
        button_load_glottis_segmentation.clicked.connect(
            self.upload_glottis_segmentation_data
        )

        horizontal_spacer = QSpacerItem(
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

            self.progress_point_tracking = QTextEdit(
                file["progress_pt_label"], readOnly=True
            )
            self.progress_point_tracking.setFixedSize(200, 30)
            self.progress_point_tracking.setTextColor(QColor(0, 0, 0))
            self.color_progress_state(
                self.progress_point_tracking, file["progress_pt_label"]
            )

            self.progress_point_clicking = QTextEdit(
                file["progress_manual_pt_label"], readOnly=True
            )
            self.progress_point_clicking.setFixedSize(200, 30)
            self.progress_point_clicking.setTextColor(QColor(0, 0, 0))
            self.color_progress_state(
                self.progress_point_clicking, file["progress_manual_pt_label"]
            )

        # centralize text of progress text bars
        self.centralize_text(self.progress_glottis_segmentation)
        self.centralize_text(self.progress_vocalfold_segmentation)
        self.centralize_text(self.progress_point_tracking)
        self.centralize_text(self.progress_point_clicking)

        # create number text bars
        label_glottis_segmentation = QLabel("1.")
        label_glottis_segmentation.setFixedSize(200, 30)
        label_vocalfold_segmentation = QLabel("2.")
        label_vocalfold_segmentation.setFixedSize(200, 30)
        label_point_tracking = QLabel("3.")
        label_point_tracking.setFixedSize(200, 30)
        label_point_clicking = QLabel("4.")
        label_point_clicking.setFixedSize(200, 30)

        # centralize text of progress num bars
        label_glottis_segmentation.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        label_vocalfold_segmentation.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        label_point_tracking.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        label_point_clicking.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # create layout
        horizontal_button_layout = QHBoxLayout()
        horizontal_progress_layout = QHBoxLayout()
        horizontal_close_layout = QHBoxLayout()
        horizontal_index_layout = QHBoxLayout()
        overarching_vertical_layout = QVBoxLayout()

        # insert buttons in window
        horizontal_button_layout.addStretch(1)
        horizontal_button_layout.addWidget(button_glottis_segmentation)
        horizontal_button_layout.addWidget(button_load_glottis_segmentation)
        horizontal_button_layout.addStretch(1)
        horizontal_button_layout.addWidget(button_vocalfold_segmentation)
        horizontal_button_layout.addStretch(1)
        horizontal_button_layout.addWidget(button_point_tracking)
        horizontal_button_layout.addStretch(1)
        horizontal_button_layout.addWidget(button_point_clicking)
        horizontal_button_layout.addStretch(1)

        # insert progress text in window
        horizontal_progress_layout.addStretch(1)
        horizontal_progress_layout.addWidget(self.progress_glottis_segmentation)
        horizontal_progress_layout.addItem(horizontal_spacer)
        horizontal_progress_layout.addStretch(1)
        horizontal_progress_layout.addWidget(self.progress_vocalfold_segmentation)
        horizontal_progress_layout.addStretch(1)
        horizontal_progress_layout.addWidget(self.progress_point_tracking)
        horizontal_progress_layout.addStretch(1)
        horizontal_progress_layout.addWidget(self.progress_point_clicking)
        horizontal_progress_layout.addStretch(1)

        # insert number text in window
        horizontal_index_layout.addStretch(1)
        horizontal_index_layout.addWidget(label_glottis_segmentation)
        horizontal_index_layout.addItem(horizontal_spacer)
        horizontal_index_layout.addStretch(1)
        horizontal_index_layout.addWidget(label_vocalfold_segmentation)
        horizontal_index_layout.addStretch(1)
        horizontal_index_layout.addWidget(label_point_tracking)
        horizontal_index_layout.addStretch(1)
        horizontal_index_layout.addWidget(label_point_clicking)
        horizontal_index_layout.addStretch(1)

        # insert close button in window
        horizontal_close_layout.addStretch(1)
        horizontal_close_layout.addWidget(button_close)

        # combine layouts
        overarching_vertical_layout.setContentsMargins(50, 50, 50, 50)
        overarching_vertical_layout.addStretch(1)
        overarching_vertical_layout.addLayout(horizontal_index_layout)
        overarching_vertical_layout.addLayout(horizontal_button_layout)
        overarching_vertical_layout.addLayout(horizontal_progress_layout)
        overarching_vertical_layout.addStretch(1)
        overarching_vertical_layout.addLayout(horizontal_close_layout)

        # adding functionality to buttons
        button_glottis_segmentation.clicked.connect(self.open_glottis_segmentation)
        button_vocalfold_segmentation.clicked.connect(self.open_vf_segmentation)
        button_point_tracking.clicked.connect(self.open_point_clicking)
        button_point_clicking.clicked.connect(self.open_manual_point_clicking)
        button_close.clicked.connect(self.close_window)

        # set layout
        self.setLayout(overarching_vertical_layout)

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
