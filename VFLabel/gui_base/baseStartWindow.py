import json
import os
import shutil

import cv2
from PyQt5.QtCore import QRect, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QPixmap
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QPushButton

import VFLabel.gui_base
import VFLabel.gui_base.baseWindow as baseWindow
import VFLabel.gui_base.baseMainMenue
import VFLabel.gui_dialog.newProject


def append_to_file(file_path, text_to_append):
    try:
        # Open the file in append mode ('a')
        with open(file_path, "a") as file:
            # Write the text and add a newline
            file.write(text_to_append + "\n")
        print(f"Successfully appended: '{text_to_append}' to {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


def read_last_nonempty_line(file_path):
    try:
        # Open the file in read mode
        with open(file_path, "r") as file:
            # Read all lines in reverse order
            for line in reversed(file.readlines()):
                # Strip whitespace and check if the line is nonempty
                if line.strip():
                    last_nonempty_line = line.strip()
                    return last_nonempty_line
        return None
    except FileNotFoundError:
        print(f"Error: The file at {file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


class BaseStartWindow(baseWindow.BaseWindow):
    signal_open_main_menu = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_window()

    def init_window(self):
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
        btn_recent = QPushButton("Open Recent", self)
        btn_recent.setToolTip(
            "This <b>button</b> opens the most recent opened project."
        )
        btn_recent.setFont(font)

        # insert buttons in window
        box_layout.addStretch(1)
        box_layout.addWidget(btn_new)
        box_layout.addStretch(1)
        box_layout.addWidget(btn_open)
        box_layout.addStretch(1)
        box_layout.addWidget(btn_recent)
        box_layout.addStretch(1)

        # adding functionality to buttons
        btn_new.clicked.connect(self.create_new_project)
        btn_open.clicked.connect(self.open_project)
        btn_recent.clicked.connect(self.open_recent_project)

        # set layout
        self.setLayout(box_layout)

        # show window
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        current_dir = os.getcwd()
        image_path = os.path.join(current_dir, "assets", "logo.png")
        pixmap = QPixmap(image_path)

        window_width = self.width()
        window_height = self.height()
        img_size = min(window_width, window_height)

        x_offset = (window_width - img_size) // 2
        y_offset = (window_height - img_size) // 2

        target_rect = QRect(x_offset, y_offset, img_size, img_size)
        painter.drawPixmap(target_rect, pixmap)

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
        status = self.load_new_video()
        if not status:
            return

        # extract name of video from path
        # Linux
        splitted_video_path = self.video_path.split("/")
        if len(splitted_video_path) == 1:
            # Windows
            splitted_video_path = self.video_path.split("\\")

        video_name = splitted_video_path[-1]
        video_name = video_name.replace(".mp4", "")
        video_name = video_name.replace(".avi", "")

        # create widget to enter new project properties
        new_project_widget = VFLabel.gui_dialog.newProject.NewProjectDialog(video_name)

        # start new project widget
        status_new_project = new_project_widget.exec_()
        (
            self.name_input,
            self.gridx,
            self.gridy,
        ) = new_project_widget.get_new_project_inputs()
        # TODO: Umwandeln in Signale?
        # TODO: Überlegen, wo gridwerte reingespeichert und dort speichern

        # check status of input from "new_project_widget" and continue
        if status_new_project == 1:
            # create folder structure for new project
            project_path = self.create_folder_structure(
                self.name_input, video_path=self.video_path
            )

            append_to_file("assets/temp/recent_projects", project_path)
            self.open_main_window(project_path)

    def open_recent_project(self) -> None:
        most_recent_path = read_last_nonempty_line("assets/temp/recent_projects")

        if most_recent_path:
            self.open_main_window(most_recent_path)

    def load_new_video(self) -> int:
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
        if self.video_path:
            return 1
        else:
            return 0

    def open_project(self):
        current_dir = os.getcwd()

        # open file manager to choose project
        fd = QFileDialog()
        fd.setWindowTitle("Choose existing project")
        fd.setFileMode(QFileDialog.Directory)
        fd.setAcceptMode(QFileDialog.AcceptOpen)
        fd.setDirectory(current_dir)
        status_fd = fd.exec()

        # if status ok, save path and open main window
        if status_fd == QFileDialog.Accepted:
            folder_path = fd.selectedFiles()[0]
            if folder_path:
                append_to_file("assets/temp/recent_projects", folder_path)

                self.open_main_window(folder_path)

    def open_main_window(self, project_path) -> None:
        self.signal_open_main_menu.emit(project_path)

    def create_folder_structure(self, project_name, video_path) -> str:
        current_dir = os.getcwd()

        # open file manager to choose project
        fd = QFileDialog()
        fd.setWindowTitle("Select location of the project folder")
        fd.setFileMode(QFileDialog.Directory)
        fd.setAcceptMode(QFileDialog.AcceptOpen)
        fd.setDirectory(current_dir)
        fd.exec_()
        folder_path = fd.selectedFiles()[0]

        # main project folder
        project_path = os.path.join(folder_path, project_name)
        os.makedirs(project_path, exist_ok=True)
        # TODO: Abfangen, wenn Ordner schon existiert

        # create subfolders
        images_folder = "video"
        os.makedirs(os.path.join(project_path, images_folder), exist_ok=True)
        os.makedirs(
            os.path.join(project_path, "laserpoint_segmentation"), exist_ok=True
        )
        os.makedirs(os.path.join(project_path, "glottis_segmentation"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "vocalfold_segmentation"), exist_ok=True)

        # save video
        if not os.path.samefile(video_path, project_path):
            shutil.copy(video_path, project_path)
        # divide video into frames and save frames
        self.video_into_frames(video_path, project_path, images_folder)

        # create empty json files
        json_path_label_cycles = os.path.join(project_path, "label_cycles.json")
        json_path_optimized_label_cycles = os.path.join(
            project_path, "optimized_label_cycles.json"
        )
        json_path_clicked_laserpts = os.path.join(
            project_path, "clicked_laserpoints.json"
        )
        json_path_computed_laserpts = os.path.join(
            project_path, "computed_laserpoints.json"
        )
        json_path_vf_points = os.path.join(project_path, "vocalfold_points.json")

        with open(json_path_label_cycles, "w") as f:
            pass

        with open(json_path_optimized_label_cycles, "w") as f:
            pass

        with open(json_path_clicked_laserpts, "w") as f:
            pass

        with open(json_path_computed_laserpts, "w") as f:
            pass
        with open(json_path_vf_points, "w") as f:
            pass

        # copy json file
        json_path_progress_status = os.path.join(project_path, "progress_status.json")

        shutil.copyfile(
            os.path.join(current_dir, "assets", "starting_progress_status.json"),
            json_path_progress_status,
        )
        print("done")
        with open(json_path_progress_status, "r+") as f:
            file = json.load(f)
            file["grid_x"] = self.gridx
            file["grid_y"] = self.gridy
            f.seek(0)
            json.dump(file, f, indent=4)

        return project_path

    def video_into_frames(self, video_path, project_path, images_folder) -> None:
        images_path = os.path.join(project_path, images_folder)

        video = cv2.VideoCapture(video_path)

        if not video.isOpened():
            print(f"Video couldn't be opened! Path might be wrong: {video_path}")
            return

        frame_count = 0

        while True:
            # read frame
            ret, frame = video.read()

            # stopping condition: no more frames
            if not ret:
                break

            # save frame
            frame_path = os.path.join(images_path, f"{frame_count:04d}.png")
            cv2.imwrite(frame_path, frame)

            frame_count += 1

        video.release()
