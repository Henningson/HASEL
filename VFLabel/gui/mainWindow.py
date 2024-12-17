import os
import json
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QTextEdit,
    QLabel,
)
from PyQt5.QtGui import QFont, QTextCursor, QTextBlockFormat
from PyQt5.QtCore import Qt, QEventLoop

import VFLabel.gui as gui
import VFLabel.gui.glottisSegmentationView as glottisSegmentationView
import VFLabel.gui.pointLabelingView as pointLabelingView
import VFLabel.gui.vocalfoldSegmentationView as vocalfoldSegmentationView


class MainWindow(QWidget):
    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path
        self.progress_state_path = os.path.join(
            self.project_path, "progress_status.json"
        )
        self.init_window()

    def init_window(self) -> None:
        print(self.project_path)

        # general setup of window
        self.setGeometry(100, 100, 1000, 1000)
        self.setWindowTitle("HASEL - Main menu")

        # create layout
        boxh_btn_layout = QHBoxLayout()
        boxh_txt_layout = QHBoxLayout()
        boxh_save_layout = QHBoxLayout()
        boxh_num_layout = QHBoxLayout()
        boxv_layout = QVBoxLayout()

        # create different options buttons
        font = QFont("Arial", 20, QFont.Bold)

        btn_gl_seg = QPushButton("Glotted \nsegmentation", self)
        btn_gl_seg.setToolTip("This <b>button</b> ...")
        btn_gl_seg.setFont(font)
        btn_gl_seg.setFixedSize(200, 100)

        btn_vf_seg = QPushButton("Vocal Fold \n segmentation", self)
        btn_vf_seg.setToolTip("This <b>button</b> ...")
        btn_vf_seg.setFont(font)
        btn_vf_seg.setFixedSize(200, 100)

        btn_pt_label = QPushButton("Point \nLabeling", self)
        btn_pt_label.setToolTip("This <b>button</b> ...")
        btn_pt_label.setFont(font)
        btn_pt_label.setFixedSize(200, 100)

        # create save button
        font = QFont("Arial", 15, QFont.Bold)
        btn_save = QPushButton("Save", self)
        btn_save.setToolTip("This <b>button</b> ...")
        btn_save.setFont(font)
        btn_save.setFixedSize(100, 30)

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
        boxh_btn_layout.addStretch(1)
        boxh_btn_layout.addWidget(btn_vf_seg)
        boxh_btn_layout.addStretch(1)
        boxh_btn_layout.addWidget(btn_pt_label)
        boxh_btn_layout.addStretch(1)

        # insert progress text in window
        boxh_txt_layout.addStretch(1)
        boxh_txt_layout.addWidget(self.progress_gl_seg)
        boxh_txt_layout.addStretch(1)
        boxh_txt_layout.addWidget(self.progress_vf_seg)
        boxh_txt_layout.addStretch(1)
        boxh_txt_layout.addWidget(self.progress_pt_label)
        boxh_txt_layout.addStretch(1)

        # insert number text in window
        boxh_num_layout.addStretch(1)
        boxh_num_layout.addWidget(num_gl_seg)
        boxh_num_layout.addStretch(1)
        boxh_num_layout.addWidget(num_vf_seg)
        boxh_num_layout.addStretch(1)
        boxh_num_layout.addWidget(num_pt_label)
        boxh_num_layout.addStretch(1)

        # insert save button in window
        boxh_save_layout.addStretch(1)
        boxh_save_layout.addWidget(btn_save)

        # combine layouts
        boxv_layout.setContentsMargins(50, 50, 50, 50)
        boxv_layout.addStretch(1)
        boxv_layout.addLayout(boxh_num_layout)
        boxv_layout.addLayout(boxh_btn_layout)
        boxv_layout.addLayout(boxh_txt_layout)
        boxv_layout.addStretch(1)
        boxv_layout.addLayout(boxh_save_layout)

        # adding functionality to buttons
        btn_gl_seg.clicked.connect(self.open_glotted_segmentation)
        btn_vf_seg.clicked.connect(self.open_vf_segmentation)
        btn_pt_label.clicked.connect(self.open_pt_labeling)

        # set layout
        self.setLayout(boxv_layout)
        self.setStyleSheet("background-color: rgb(240, 248, 255);")

        # show window
        self.show()

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

    def save_new_progress_state(self, variable: str, new_state: str) -> None:

        with open(self.progress_state_path, "r+") as prgrss_file:
            file = json.load(prgrss_file)
            file[variable] = new_state
            prgrss_file.seek(0)
            prgrss_file.truncate()
            json.dump(file, prgrss_file, indent=4)

    def open_glotted_segmentation(self) -> None:
        # create and open glottisSegmentation video
        self.glottis_window = glottisSegmentationView.GlottisSegmentationView(
            self.project_path
        )

        # connect progress state signal
        self.glottis_window.progress_signal.connect(self.update_signal_progress_gl_seg)

        # wait for glottis window to be closed
        self.setEnabled(False)
        loop = QEventLoop()
        self.glottis_window.destroyed.connect(loop.quit)
        loop.exec_()
        self.setEnabled(True)

        # save new progress state
        self.save_new_progress_state("progress_gl_seg", self.progress_state_gl_seg)

        # change progress state in window
        self.progress_gl_seg.setText(self.progress_state_gl_seg)
        self.centralize_text(self.progress_gl_seg)
        self.color_progress_state(self.progress_gl_seg, self.progress_state_gl_seg)
        # TODO add background color according to state

    def update_signal_progress_gl_seg(self, progress: str) -> None:
        self.progress_state_gl_seg = progress

    def open_vf_segmentation(self) -> None:
        # create and open glottisSegmentation video
        self.vf_seg_window = vocalfoldSegmentationView.VocalfoldSegmentationView(
            self.project_path
        )

        # connect progress state signal
        self.vf_seg_window.progress_signal.connect(self.update_signal_progress_vf_seg)

        # wait for point_label window to be closed
        loop = QEventLoop()
        self.vf_seg_window.destroyed.connect(loop.quit)
        loop.exec_()

        # save new progress state
        self.save_new_progress_state("progress_vf_seg", self.progress_state_vf_seg)

        # change progress state in window
        self.progress_vf_seg.setText(self.progress_state_vf_seg)
        self.centralize_text(self.progress_vf_seg)
        self.color_progress_state(self.progress_vf_seg, self.progress_state_vf_seg)

    def update_signal_progress_vf_seg(self, progress: str) -> None:
        self.progress_state_vf_seg = progress

    def open_pt_labeling(self) -> None:
        # create and open glottisSegmentation video
        self.point_label_window = pointLabelingView.PointLabelingView(self.project_path)

        # connect progress state signal
        self.point_label_window.progress_signal.connect(
            self.update_signal_progress_pt_labeling
        )

        # wait for point_label window to be closed
        loop = QEventLoop()
        self.point_label_window.destroyed.connect(loop.quit)
        loop.exec_()

        # save new progress state
        self.save_new_progress_state("progress_pt_label", self.progress_state_pt_label)

        # change progress state in window
        self.progress_pt_label.setText(self.progress_state_pt_label)
        self.centralize_text(self.progress_pt_label)
        self.color_progress_state(self.progress_pt_label, self.progress_state_pt_label)

    def update_signal_progress_pt_labeling(self, progress: str) -> None:
        self.progress_state_pt_label = progress

    def centralize_text(self, widget) -> None:
        cursor = widget.textCursor()
        cursor.select(QTextCursor.Document)
        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignCenter)
        cursor.mergeBlockFormat(block_format)

    def closeEvent(self, event):
        self.deleteLater()
