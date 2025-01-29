import json
import os

import cv2
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow, QToolBar
from tqdm import tqdm

import VFLabel.cv
import VFLabel.gui_base
import VFLabel.gui_base.baseMainMenue
import VFLabel.gui_base.baseManualPointClick
import VFLabel.gui_dialog.newProject


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # general setup
        self.showMaximized()

        # setup menu bar
        self.setStatusBar(self.statusBar())
        self.menubar = self.menuBar()

        # file submenu
        file_menu = self.menubar.addMenu("&File")
        file_menu.addAction("Save", self.save_current_state)
        file_menu.addAction(
            "Load Glottis Segmentation from Folder",
            self.load_glottis_segmentation_folder,
        )

        file_menu.addAction(
            "Load glottis segmentation from Video", self.load_glottis_segmentation_video
        )

        # menu close button
        menu_close_window = QAction("Close current window", self)
        menu_close_window.triggered.connect(self.close_current_window)
        self.menubar.addAction(menu_close_window)

        # menu help button
        menu_help_window = QAction("Help", self)
        menu_help_window.triggered.connect(self.help)
        self.menubar.addAction(menu_help_window)

        # icons for toolbar - icons from license-free page: https://uxwing.com/
        close_icon_path = "assets/icons/x.svg"
        save_icon_path = "assets/icons/checkmark.svg"
        help_icon_path = "assets/icons/help.svg"

        # setup tool bar
        self.toolbar = QToolBar()

        # tool close button
        tool_close_window = QAction(
            QIcon(f"{close_icon_path}"), "Close current window", self
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

        # tool help button
        self.tool_help_window = QAction(QIcon(f"{help_icon_path}"), "Help", self)
        self.tool_help_window.setToolTip("Help  Ctrl+h")
        self.tool_help_window.setShortcut("Ctrl+h")
        self.tool_help_window.triggered.connect(self.help)
        self.toolbar.addAction(self.tool_help_window)

        self.addToolBar(self.toolbar)

        self.open_start_window()

        self.show()

    def open_start_window(self):
        self.menubar.setVisible(False)
        self.toolbar.setVisible(False)
        # new title
        self.setWindowTitle("HASEL - Start Menu")

        # setup window and its signals
        self.start_window = VFLabel.gui_base.baseStartWindow.BaseStartWindow(self)
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
        self.main_menu = VFLabel.gui_base.baseMainMenue.BaseMainMenue(
            project_path, self
        )
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
        self.main_menu.signal_upload_glottis_segmentation.connect(
            self.upload_glottis_data_video
        )

        self.main_menu.signal_open_manual_point_clicking_window.connect(
            self.open_manual_point_clicking_window
        )

        # make it visible in main window
        self.setCentralWidget(self.main_menu)

    def open_vf_segmentation_window(self, project_path):
        self.tool_save_window.setVisible(True)
        # new title
        self.setWindowTitle(f"HASEL - VF segmentation - {project_path}")

        # setup window and its signals
        self.vf_segm_window = VFLabel.gui_base.baseVocalfold.BaseVocalfold(
            project_path, self
        )
        self.vf_segm_window.signal_open_main_menu.connect(self.open_main_menu)

        # make it visible in main window
        self.setCentralWidget(self.vf_segm_window)

    def open_glottis_segmentation_window(self, project_path):
        self.tool_save_window.setVisible(True)
        # new title
        self.setWindowTitle(f"HASEL - Glottis segmentation - {project_path}")

        # setup window and its signals
        self.glottis_segm_window = VFLabel.gui_base.baseGlottis.BaseGlottis(
            project_path, self
        )
        self.glottis_segm_window.signal_open_main_menu.connect(self.open_main_menu)

        # make it visible in main window
        self.setCentralWidget(self.glottis_segm_window)

    def open_point_labeling_window(self, project_path):
        self.tool_save_window.setVisible(True)
        # new title
        self.setWindowTitle(f"HASEL - Point Labeling - {project_path}")

        # setup window and its signals
        self.pt_labeling_window = VFLabel.gui_base.basePointClick.BasePointClick(
            project_path, self
        )
        self.pt_labeling_window.signal_open_main_menu.connect(self.open_main_menu)

        # make it visible in main window
        self.setCentralWidget(self.pt_labeling_window)

    def open_manual_point_clicking_window(self, project_path):
        self.tool_save_window.setVisible(True)
        # new title
        self.setWindowTitle(f"HASEL - Manual Point Clicking - {project_path}")

        # setup window and its signals
        self.manual_point_click_window = (
            VFLabel.gui_base.baseManualPointClick.BaseManualPointClick(
                project_path, self
            )
        )
        self.manual_point_click_window.signal_open_main_menu.connect(
            self.open_main_menu
        )

        # make it visible in main window
        self.setCentralWidget(self.manual_point_click_window)

    def close_current_window(self) -> None:
        # called when "close current window" in menubar is triggered
        self.centralWidget().close_window()

    def save_current_state(self) -> None:
        self.centralWidget().save_current_state()

    def help(self):
        self.centralWidget().help()

    def load_glottis_segmentation_folder(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(
            caption="Folder containing the segmentation images"
        )

        if dir_path == "":
            return
        segmentations = []
        for image_file in sorted(os.listdir(dir_path)):
            image_path = os.path.join(dir_path, image_file)
            segmentation = cv2.imread(image_path, 0)
            segmentations.append(segmentation)

    def load_glottis_segmentation_video(self) -> None:
        current_dir = os.getcwd()
        video_path, _ = QFileDialog.getOpenFileName(
            self,
            "Video of the glottis segmentation",
            current_dir,
            "Only video-files(*.mp4 *.avi)",
        )

        if video_path == "":
            return

        video = VFLabel.io.data.read_video(video_path)
        self.generate_glottis_data(video)

    def generate_glottis_data(self, segmentations) -> None:
        midlines = [
            VFLabel.cv.analysis.glottal_midline(image) for image in tqdm(segmentations)
        ]

        self.save_segmentations_and_midlines(segmentations, midlines)
        self.update_glottis_progress()
        self.open_main_menu(self.centralWidget().project_path)

    def save_segmentations_and_midlines(self, segmentations, midlines) -> None:
        segmentation_path = os.path.join(
            self.centralWidget().project_path, "glottis_segmentation"
        )
        glottal_midlines_path = os.path.join(
            self.centralWidget().project_path, "glottal_midlines.json"
        )

        glottal_midline_dict = {}
        for frame_index, midline_points in enumerate(midlines):
            upper = midline_points[0]
            lower = midline_points[1]

            glottal_midline_dict[f"Frame{frame_index}"] = {
                "Upper": upper.tolist() if upper is not None else [-1, -1],
                "Lower": lower.tolist() if lower is not None else [-1, -1],
            }

        with open(glottal_midlines_path, "w+") as outfile:
            json.dump(glottal_midline_dict, outfile)

        for frame_index, seg in enumerate(segmentations):
            image_save_path = os.path.join(segmentation_path, f"{frame_index:05d}.png")
            cv2.imwrite(image_save_path, seg)

    def update_glottis_progress(self):
        progress_state_path = os.path.join(
            self.centralWidget().project_path, "progress_status.json"
        )

        with open(progress_state_path, "r+") as prgrss_file:
            file = json.load(prgrss_file)
            file["progress_gl_seg"] = "finished"
            prgrss_file.seek(0)
            prgrss_file.truncate()
            json.dump(file, prgrss_file, indent=4)

    def upload_glottis_data_video(self, asvideo):
        if asvideo:
            self.load_glottis_segmentation_video()
        else:
            self.load_glottis_segmentation_folder()
