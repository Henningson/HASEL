import os

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFileDialog, QInputDialog
from PyQt5.QtGui import QPixmap, QPainter, QFont


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
        # Open dialog to enter new name
        text, ok = QInputDialog.getText(
            self, "Name of new project", "Please enter the name of the new project"
        )
        if ok:
            print(text)
        # TODO: create new project with given name
        # TODO: upload video
        # TODO: Überleitung zu Programm

    def open_project(self):
        current_dir = os.getcwd()

        # open file manager to choose project
        fd = QFileDialog()
        fname = fd.getOpenFileName(
            self,
            "Open project",
            current_dir,
            "Only ToBeDetermined-files(*.mp4)",
        )
        # TODO: Enter right file types
        print(fname)
        # TODO: Überleitung zu Programm
