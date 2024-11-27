import os
import json
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QTextEdit,
)
from PyQt5.QtGui import QFont, QTextCursor, QTextBlockFormat
from PyQt5.QtCore import Qt

import VFLabel.gui as gui


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

        btn_auto_pt_label = QPushButton("Auto Point \n Labeling", self)
        btn_auto_pt_label.setToolTip("This <b>button</b> ...")
        btn_auto_pt_label.setFont(font)
        btn_auto_pt_label.setFixedSize(200, 100)

        # create save button
        font = QFont("Arial", 15, QFont.Bold)
        btn_save = QPushButton("Save", self)
        btn_save.setToolTip("This <b>button</b> ...")
        btn_save.setFont(font)
        btn_save.setFixedSize(100, 30)

        # create progress text bars
        self.read_write_progress_state()
        # TODO: wenn geöffnet wird, text anders initialisieren

        # centralize text of progress text bars
        self.centralize_text(self.progress_gl_seg)
        self.centralize_text(self.progress_vf_seg)
        self.centralize_text(self.progress_pt_label)
        self.centralize_text(self.progress_auto_pt_label)

        # create number text bars
        num_gl_seg = QTextEdit("1.", readOnly=True)
        num_gl_seg.setFixedSize(200, 30)
        num_vf_seg = QTextEdit("2.", readOnly=True)
        num_vf_seg.setFixedSize(200, 30)
        num_pt_label = QTextEdit("3.", readOnly=True)
        num_pt_label.setFixedSize(200, 30)
        num_auto_pt_label = QTextEdit("4.", readOnly=True)
        num_auto_pt_label.setFixedSize(200, 30)

        # centralize text of progress text bars
        self.centralize_text(num_gl_seg)
        self.centralize_text(num_vf_seg)
        self.centralize_text(num_pt_label)
        self.centralize_text(num_auto_pt_label)

        # insert buttons in window
        boxh_btn_layout.addStretch(1)
        boxh_btn_layout.addWidget(btn_gl_seg)
        boxh_btn_layout.addStretch(1)
        boxh_btn_layout.addWidget(btn_vf_seg)
        boxh_btn_layout.addStretch(1)
        boxh_btn_layout.addWidget(btn_pt_label)
        boxh_btn_layout.addStretch(1)
        boxh_btn_layout.addWidget(btn_auto_pt_label)
        boxh_btn_layout.addStretch(1)

        # insert progress text in window
        boxh_txt_layout.addStretch(1)
        boxh_txt_layout.addWidget(self.progress_gl_seg)
        boxh_txt_layout.addStretch(1)
        boxh_txt_layout.addWidget(self.progress_vf_seg)
        boxh_txt_layout.addStretch(1)
        boxh_txt_layout.addWidget(self.progress_pt_label)
        boxh_txt_layout.addStretch(1)
        boxh_txt_layout.addWidget(self.progress_auto_pt_label)
        boxh_txt_layout.addStretch(1)

        # insert number text in window
        boxh_num_layout.addStretch(1)
        boxh_num_layout.addWidget(num_gl_seg)
        boxh_num_layout.addStretch(1)
        boxh_num_layout.addWidget(num_vf_seg)
        boxh_num_layout.addStretch(1)
        boxh_num_layout.addWidget(num_pt_label)
        boxh_num_layout.addStretch(1)
        boxh_num_layout.addWidget(num_auto_pt_label)
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
        btn_auto_pt_label.clicked.connect(self.open_auto_pt_labeling)

        # set layout
        self.setLayout(boxv_layout)
        # print(self.path)

        # show window
        self.show()

    def read_write_progress_state(self):
        with open(self.progress_state_path, "r+") as prgrss_file:
            file = json.load(prgrss_file)
            self.progress_gl_seg = QTextEdit(file["progress_gl_seg"], readOnly=True)
            self.progress_gl_seg.setFixedSize(200, 30)
            self.progress_vf_seg = QTextEdit(file["progress_vf_seg"], readOnly=True)
            self.progress_vf_seg.setFixedSize(200, 30)
            self.progress_pt_label = QTextEdit(file["progress_pt_label"], readOnly=True)
            self.progress_pt_label.setFixedSize(200, 30)
            self.progress_auto_pt_label = QTextEdit(
                file["progress_auto_pt_label"], readOnly=True
            )
            self.progress_auto_pt_label.setFixedSize(200, 30)

    def save_new_progress_state(self, variable, new_state):
        with open(self.progress_state_path, "r+") as prgrss_file:
            file = json.load(prgrss_file)
            file[variable] = new_state
            prgrss_file.seek(0)
            json.dump(file, prgrss_file, indent=4)

    def open_glotted_segmentation(self) -> None:
        new_state = "in progress"
        self.progress_gl_seg.setText(new_state)
        self.save_new_progress_state("progress_gl_seg", new_state)
        # TODO add background color according to state
        self.centralize_text(self.progress_gl_seg)
        pass
        # TODO open glotted segmentation window

    def open_vf_segmentation(self) -> None:
        pass
        # TODO open vocal fold segmentation window

    def open_pt_labeling(self) -> None:
        pass
        # TODO open point labeling window

    def open_auto_pt_labeling(self) -> None:
        # TODO: in betweenWindow : DO you have already finished point labeling? If not, please finish it first ...
        pass
        # TODO open point labeling window

    def centralize_text(self, widget) -> None:
        cursor = widget.textCursor()
        cursor.select(QTextCursor.Document)
        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignCenter)
        cursor.mergeBlockFormat(block_format)
