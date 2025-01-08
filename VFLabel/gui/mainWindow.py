from PyQt5.QtWidgets import QMainWindow, QAction, QToolBar
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon


import VFLabel.gui
import VFLabel.gui.newProjectWidget, VFLabel.gui.mainMenuView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # general setup
        self.showMaximized()
        # self.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: rgb(255, 255, 255);
            }

            QMenuBar {
                background: rgb(240, 248, 255);       /* background*/
                color: rgb(0, 0, 0);        /* text color*/
                border-top: 1px solid rgb(211, 211, 211);
                /*border-bottom: 1px solid rgb(211, 211, 211);*/
            }
            QToolBar {
                background: rgb(240, 248, 255);       /* background*/
                color: rgb(0, 0, 0);       /* text color*/
                /*border-top: 1px solid rgb(211, 211, 211);*/
                border-bottom: 1px solid rgb(211, 211, 211);
            }
            """
        )

        # setup menu bar
        self.setStatusBar(self.statusBar())
        self.menubar = self.menuBar()

        # file submenu
        file_menu = self.menubar.addMenu("&File")
        file_menu.addAction("Save", self.save_current_state)

        # menu close button
        menu_close_window = QAction("Close current window", self)
        menu_close_window.triggered.connect(self.close_current_window)
        self.menubar.addAction(menu_close_window)

        # icons for toolbar - icons from license-free page: https://uxwing.com/
        close_icon_path = "assets/icons/close-square-line-icon.svg"
        save_icon_path = "assets/icons/check-mark-box-line-icon.svg"

        # setup tool bar
        self.toolbar = QToolBar()

        # tool close button
        tool_close_window = QAction(
            QIcon(close_icon_path), "Close current window", self
        )
        tool_close_window.setToolTip("Close current window  Ctrl+c")
        tool_close_window.setShortcut("Ctrl+c")
        tool_close_window.triggered.connect(self.close_current_window)
        self.toolbar.addAction(tool_close_window)

        # tool save button
        self.tool_save_window = QAction(
            QIcon(f"{save_icon_path}"), "Save current State", self
        )
        self.tool_save_window.setToolTip("Save current state  Ctrl+s")
        self.tool_save_window.setShortcut("Ctrl+s")
        self.tool_save_window.triggered.connect(self.save_current_state)
        self.toolbar.addAction(self.tool_save_window)

        self.addToolBar(self.toolbar)

        self.open_start_window()

        self.show()

    def open_start_window(self):
        self.menubar.setVisible(False)
        self.toolbar.setVisible(False)
        # new title
        self.setWindowTitle("HASEL - Start Menu")

        # setup window and its signals
        self.start_window = VFLabel.gui.startWindowView.StartWindowView(self)
        self.start_window.signal_open_main_menu.connect(self.open_main_menu)

        # make it visible in main window
        self.setCentralWidget(self.start_window)

    def open_main_menu(self, project_path):
        self.menubar.setVisible(True)
        self.toolbar.setVisible(True)
        self.tool_save_window.setVisible(False)

        # new title
        self.setWindowTitle(f"HASEL - Main Menu - {project_path}")

        # setup window and its signals
        self.main_menu = VFLabel.gui.mainMenuView.MainMenuView(project_path, self)
        self.main_menu.signal_open_vf_segm_window.connect(
            self.open_vf_segmentation_window
        )
        self.main_menu.signal_open_pt_label_window.connect(
            self.open_point_labeling_window
        )
        self.main_menu.signal_open_glottis_segm_window.connect(
            self.open_glottis_segmentation_window
        )
        self.main_menu.signal_close_main_menu_window.connect(self.open_start_window)

        # make it visible in main window
        self.setCentralWidget(self.main_menu)

    def open_vf_segmentation_window(self, project_path):
        self.tool_save_window.setVisible(True)
        # new title
        self.setWindowTitle(f"HASEL - VF segmentation - {project_path}")

        # setup window and its signals
        self.vf_segm_window = (
            VFLabel.gui.vocalfoldSegmentationView.VocalfoldSegmentationView(
                project_path, self
            )
        )
        self.vf_segm_window.signal_open_main_menu.connect(self.open_main_menu)

        # make it visible in main window
        self.setCentralWidget(self.vf_segm_window)

    def open_glottis_segmentation_window(self, project_path):
        self.tool_save_window.setVisible(True)
        # new title
        self.setWindowTitle(f"HASEL - Glottis segmentation - {project_path}")

        # setup window and its signals
        self.glottis_segm_window = (
            VFLabel.gui.glottisSegmentationView.GlottisSegmentationView(
                project_path, self
            )
        )
        self.glottis_segm_window.signal_open_main_menu.connect(self.open_main_menu)

        # make it visible in main window
        self.setCentralWidget(self.glottis_segm_window)

    def open_point_labeling_window(self, project_path):
        self.tool_save_window.setVisible(True)
        # new title
        self.setWindowTitle(f"HASEL - Point Labeling - {project_path}")

        # setup window and its signals
        self.pt_labeling_window = VFLabel.gui.pointLabelingView.PointLabelingView(
            project_path, self
        )
        self.pt_labeling_window.signal_open_main_menu.connect(self.open_main_menu)

        # make it visible in main window
        self.setCentralWidget(self.pt_labeling_window)

    def close_current_window(self):
        # called when "close current window" in menubar is triggered
        self.centralWidget().close_window()

    def save_current_state(self):
        self.centralWidget().save_current_state()
