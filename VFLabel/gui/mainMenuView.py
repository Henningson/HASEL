import os
import json
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QTextEdit,
    QLabel,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.QtGui import QFont, QTextCursor, QTextBlockFormat, QIcon
from PyQt5.QtCore import Qt, QEventLoop, pyqtSignal, QSize

import VFLabel.gui as gui
import VFLabel.gui.glottisSegmentationView as glottisSegmentationView
import VFLabel.gui.pointLabelingView as pointLabelingView
import VFLabel.gui.vocalfoldSegmentationView as vocalfoldSegmentationView
import VFLabel.gui.baseWindowWidget as baseWindowWidget


class MainMenuView(baseWindowWidget.BaseWindowWidget):

    signal_open_vf_segm_window = pyqtSignal(str)
    signal_close_main_menu_window = pyqtSignal()
    signal_open_glottis_segm_window = pyqtSignal(str)
    signal_open_pt_label_window = pyqtSignal(str)

    signal_upload_glottis_segmentation = pyqtSignal(bool)

    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.progress_state_path = os.path.join(
            self.project_path, "progress_status.json"
        )
        self.init_window()

    def init_window(self) -> None:

        # create layout
        boxh_btn_layout = QHBoxLayout()
        boxh_txt_layout = QHBoxLayout()
        boxh_close_layout = QHBoxLayout()
        boxh_num_layout = QHBoxLayout()
        boxv_layout = QVBoxLayout()

        # create different options buttons
        font = QFont("Arial", 20, QFont.Bold)

        btn_gl_seg = QPushButton("Glottis \nsegmentation", self)
        btn_gl_seg.setToolTip("This <b>button</b> ...")
        btn_gl_seg.setFont(font)
        btn_gl_seg.setFixedSize(200, 100)

        btn_vf_seg = QPushButton("Vocal Fold \nsegmentation", self)
        btn_vf_seg.setToolTip("This <b>button</b> ...")
        btn_vf_seg.setFont(font)
        btn_vf_seg.setFixedSize(200, 100)

        btn_pt_label = QPushButton("Point \nLabeling", self)
        btn_pt_label.setToolTip("This <b>button</b> ...")
        btn_pt_label.setFont(font)
        btn_pt_label.setFixedSize(200, 100)

        path_upload_icon = "assets/icons/file-download-import.svg"

        btn_upload_glottis_segm = QPushButton(QIcon(path_upload_icon), "")
        btn_upload_glottis_segm.setIconSize(QSize(50, 50))
        btn_upload_glottis_segm.setStyleSheet("border: 0px solid;")
        btn_upload_glottis_segm.setToolTip("Upload glottis segmentation data")
        btn_upload_glottis_segm.clicked.connect(self.upload_glottis_segmentation_data)

        horizontal_spacer = QSpacerItem(
            60, 20, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        horizontal_spacer_2 = QSpacerItem(
            60, 20, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        # create close button
        font = QFont("Arial", 15, QFont.Bold)
        btn_close = QPushButton("Close", self)
        btn_close.setToolTip("This <b>button</b> ...")
        btn_close.setFont(font)
        btn_close.setFixedSize(100, 30)

        # create progress text bars
        self.read_write_progress_state()

        # centralize text of progress text bars
        self.centralize_text(self.progress_gl_seg)
        self.centralize_text(self.progress_vf_seg)
        self.centralize_text(self.progress_pt_label)

        # create number text bars
        num_gl_seg = QLabel("1.")
        num_gl_seg.setFixedSize(200, 30)
        num_vf_seg = QLabel("2.")
        num_vf_seg.setFixedSize(200, 30)
        num_pt_label = QLabel("3.")
        num_pt_label.setFixedSize(200, 30)

        # centralize text of progress num bars
        num_gl_seg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        num_vf_seg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        num_pt_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # insert buttons in window
        boxh_btn_layout.addStretch(1)
        boxh_btn_layout.addWidget(btn_gl_seg)
        boxh_btn_layout.addWidget(btn_upload_glottis_segm)
        boxh_btn_layout.addStretch(1)
        boxh_btn_layout.addWidget(btn_vf_seg)
        boxh_btn_layout.addStretch(1)
        boxh_btn_layout.addWidget(btn_pt_label)
        boxh_btn_layout.addStretch(1)

        # insert progress text in window
        boxh_txt_layout.addStretch(1)
        boxh_txt_layout.addWidget(self.progress_gl_seg)
        boxh_txt_layout.addItem(horizontal_spacer)
        boxh_txt_layout.addStretch(1)
        boxh_txt_layout.addWidget(self.progress_vf_seg)
        boxh_txt_layout.addStretch(1)
        boxh_txt_layout.addWidget(self.progress_pt_label)
        boxh_txt_layout.addStretch(1)

        # insert number text in window
        boxh_num_layout.addStretch(1)
        boxh_num_layout.addWidget(num_gl_seg)
        boxh_num_layout.addItem(horizontal_spacer_2)
        boxh_num_layout.addStretch(1)
        boxh_num_layout.addWidget(num_vf_seg)
        boxh_num_layout.addStretch(1)
        boxh_num_layout.addWidget(num_pt_label)
        boxh_num_layout.addStretch(1)

        # insert close button in window
        boxh_close_layout.addStretch(1)
        boxh_close_layout.addWidget(btn_close)

        # combine layouts
        boxv_layout.setContentsMargins(50, 50, 50, 50)
        boxv_layout.addStretch(1)
        boxv_layout.addLayout(boxh_num_layout)
        boxv_layout.addLayout(boxh_btn_layout)
        boxv_layout.addLayout(boxh_txt_layout)
        boxv_layout.addStretch(1)
        boxv_layout.addLayout(boxh_close_layout)

        # adding functionality to buttons
        btn_gl_seg.clicked.connect(self.open_glottis_segmentation)
        btn_vf_seg.clicked.connect(self.open_vf_segmentation)
        btn_pt_label.clicked.connect(self.open_pt_labeling)
        btn_close.clicked.connect(self.close_window)

        # set layout
        self.setLayout(boxv_layout)

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

    def open_pt_labeling(self) -> None:
        self.signal_open_pt_label_window.emit(self.project_path)

    def read_write_progress_state(self):
        with open(self.progress_state_path, "r+") as prgrss_file:
            file = json.load(prgrss_file)
            self.progress_gl_seg = QTextEdit(file["progress_gl_seg"], readOnly=True)
            self.progress_gl_seg.setFixedSize(200, 30)
            self.color_progress_state(self.progress_gl_seg, file["progress_gl_seg"])
            self.progress_vf_seg = QTextEdit(file["progress_vf_seg"], readOnly=True)
            self.progress_vf_seg.setFixedSize(200, 30)
            self.color_progress_state(self.progress_vf_seg, file["progress_vf_seg"])
            self.progress_pt_label = QTextEdit(file["progress_pt_label"], readOnly=True)
            self.progress_pt_label.setFixedSize(200, 30)
            self.color_progress_state(self.progress_pt_label, file["progress_pt_label"])

    def color_progress_state(self, state_variable, state: str):
        if state == "finished":
            state_variable.setStyleSheet("background-color: rgb(144, 238, 144);")
        elif state == "in progress":
            state_variable.setStyleSheet("background-color: rgb(173, 216, 230);")
        elif state == "not started":
            state_variable.setStyleSheet("background-color: rgb(211, 211, 211);")
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
