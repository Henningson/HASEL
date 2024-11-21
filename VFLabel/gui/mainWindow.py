import os

from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QInputDialog,
    QLineEdit,
)
from PyQt5.QtGui import QPixmap, QPainter, QFont

import gui


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_window()

    def init_window(self):
        # general setup of window
        self.setGeometry(100, 100, 1000, 1000)
        self.setWindowTitle("HASEL - Main menu")

        # create layout
        box_layout = QHBoxLayout()

        # create buttons
        font = QFont("Arial", 20, QFont.Bold)
        btn_new = QPushButton("New Project", self)
        btn_new.setToolTip("This <b>button</b> creates a new project.")
        btn_new.setFont(font)
        btn_open = QPushButton("Open Project", self)
        btn_open.setToolTip("This <b>button</b> opens an existing project.")
        btn_open.setFont(font)

        # insert buttons in window
        box_layout.addStretch(1)
        box_layout.addWidget(btn_new)
        box_layout.addStretch(1)
        box_layout.addWidget(btn_open)
        box_layout.addStretch(1)

        # adding functionality to buttons
        btn_new.clicked.connect(self.create_new_project)
        btn_open.clicked.connect(self.open_project)

        # set layout
        self.setLayout(box_layout)

        # show window
        self.show()

    def paintEvent(self, event):
        """Paint background of Main Menu"""
        painter = QPainter(self)
        current_dir = os.getcwd()
        image_path = os.path.join(current_dir, "assets", "logo.png")
        # TODO: Pfad so aussuchen, dass er immer funktioniert
        pixmap = QPixmap(image_path)
        painter.drawPixmap(self.rect(), pixmap)

    def create_new_project(self):
        """Creates a new project

        This method:
        - gets parameters for new project
        - uploads video path
        - creates project
        - forwards to next part of the program

        Returns:
            None
        """
        # create widget to enter new project properties
        new_project_widget = gui.NewProjectWidget()

        # connect signal between new_project_widget and this window
        new_project_widget.new_project_status_signal.connect(
            self.update_new_project_status
        )

        # start new project widget
        new_project_widget.exec_()
        (
            self.name_input,
            self.gridx,
            self.gridy,
        ) = new_project_widget.get_new_project_inputs()
        # TODO: Umwandeln in Signale?

        # check status of input from "new_project_widget" and continue
        if self.status_new_project == "OK":
            # upload video path
            self.upload_new_video()
            print(self.video_path)

            # TODO: create new project with given name
            # TODO: Überleitung zu Programm

    def upload_new_video(self):
        """Opens file manager to upload video

        This method:
        - opens file manager
        - allows user to choose a video
        - saves path of video

        Returns:
            None
        """
        current_dir = os.getcwd()
        fd = QFileDialog()
        self.video_path, _ = fd.getOpenFileName(
            self,
            "Upload video",
            current_dir,
            "Only video-files(*.mp4)",
        )
        # TODO: auch andere Dateitypen ?

    def update_new_project_status(self, status):
        # status from newProjectWidget
        self.status_new_project = status

    def open_project(self):
        current_dir = os.getcwd()

        # open file manager to choose project
        fd = QFileDialog()
        file_path, _ = fd.getOpenFileName(
            self,
            "Open project",
            current_dir,
            "Only ToBeDetermined-files(*.mp4)",
        )
        # TODO: Enter right file types
        # TODO: Überleitung zu Programm
