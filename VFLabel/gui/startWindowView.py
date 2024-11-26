import os
import shutil
import json
from time import sleep

from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QApplication,
)
from PyQt5.QtGui import QPixmap, QPainter, QFont

import VFLabel.gui.newProjectWidget, VFLabel.gui.mainWindow


class StartWindowView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_window()

    def init_window(self):
        # general setup of window
        self.setGeometry(100, 100, 1000, 1000)
        self.setWindowTitle("HASEL - Start menu")

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
        - uploads video path
        - gets parameters for new project
        - creates project
        - forwards to next part of the program

        Returns:
            None
        """
        # upload video path
        self.upload_new_video()

        # create widget to enter new project properties
        new_project_widget = VFLabel.gui.newProjectWidget.NewProjectWidget()

        # start new project widget
        status_new_project = new_project_widget.exec_()
        (
            self.name_input,
            self.gridx,
            self.gridy,
        ) = new_project_widget.get_new_project_inputs()
        # TODO: Umwandeln in Signale?

        # check status of input from "new_project_widget" and continue
        if status_new_project == 1:
            # upload video path
            project_path = self.create_folder_structure(
                self.name_input, video_path=self.video_path
            )
            self.open_main_window(project_path)
            print("then")
            pass

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
            "Only video-files(*.mp4 *.avi)",
        )

    def open_project(self):
        current_dir = os.getcwd()

        # open file manager to choose project
        fd = QFileDialog()
        fd.setWindowTitle("Choose existing project")
        fd.setFileMode(QFileDialog.Directory)
        fd.setAcceptMode(QFileDialog.AcceptOpen)
        fd.setDirectory(current_dir)
        status_fd = fd.exec()
        print(status_fd)
        folder_path = fd.selectedFiles()[0]
        fd.close()

        self.open_main_window(folder_path)
        # TODO: Überleitung zu Programm

    def open_main_window(self, project_path):
        print("here")
        main_window = VFLabel.gui.mainWindow.MainWindow()
        main_window.show()

    def create_folder_structure(self, project_name, video_path) -> str:
        # TODO: Where to save the project
        current_dir = os.getcwd()

        # main_window = VFLabel.gui.mainWindow.MainWindow()
        # main_window.show()
        # open file manager to choose project
        fd = QFileDialog()
        fd.setWindowTitle("Select location of project")
        fd.setFileMode(QFileDialog.Directory)
        fd.setAcceptMode(QFileDialog.AcceptOpen)
        fd.setDirectory(current_dir)
        fd.exec_()
        folder_path = fd.selectedFiles()[0]

        # main project folder
        project_path = os.path.join(folder_path, project_name)
        os.mkdir(project_path)
        # TODO: Abfangen, wenn Ordner schon existiert

        # create subfolders
        os.mkdir(os.path.join(project_path, "video"))
        os.mkdir(os.path.join(project_path, "laserpoint_segmentation"))
        os.mkdir(os.path.join(project_path, "glottis_segmentation"))
        os.mkdir(os.path.join(project_path, "vocalfold_segmentation"))

        # save video
        shutil.copy(video_path, project_path)

        # create empty json files
        json_path_label_cycles = os.path.join(project_path, "label_cycles.json")
        json_path_clicked_laserpts = os.path.join(
            project_path, "clicked_laserpoints.json"
        )
        json_path_computed_laserpts = os.path.join(
            project_path, "computed_laserpoints.json"
        )

        with open(json_path_label_cycles, "w") as f:
            pass

        with open(json_path_clicked_laserpts, "w") as f:
            pass

        with open(json_path_computed_laserpts, "w") as f:
            pass

        # copy json file
        json_path_progress_status = os.path.join(project_path, "progress_status.json")
        with open(json_path_progress_status, "w") as f:
            shutil.copyfile(
                os.path.join(current_dir, "assets", "starting_progress_status.json"),
                json_path_progress_status,
            )

        return project_path
