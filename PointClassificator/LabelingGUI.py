import os
import json
import cv2

from typing import List
from SpecularHighlightData import SpecularHightlightDatum, PointLabel

from PyQt5.QtCore import QLibraryInfo

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(
    QLibraryInfo.PluginsPath
)

from PyQt5.QtWidgets import (
    QMainWindow,
    QGraphicsScene,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QAction,
    QInputDialog,
    QFileDialog,
)
from PyQt5.QtCore import Qt
from random import shuffle

from GUI import ZoomableView, HorizontalButtonWidget, ImageButton, LabelButtonWidget

from conversions import cvToQPixmap

import numpy as np
import cv2
import FlowLayout


class LabelingGUI(QWidget):
    def __init__(self, data_points: List[SpecularHightlightDatum]):
        super(LabelingGUI, self).__init__()

        self.image_buttons = []
        self.base_path = ""

        layout = QVBoxLayout(self)

        self.graphics_scene = QGraphicsScene()
        self.image_viewer = ZoomableView(self.graphics_scene)
        layout.addWidget(self.image_viewer)

        self.labelbuttons = LabelButtonWidget()
        self.labelbuttons.laserdot_button.clicked.connect(self.setLaserpointLabel)
        self.labelbuttons.specular_button.clicked.connect(self.setSpecularityLabel)
        self.labelbuttons.anything_button.clicked.connect(self.setOtherLabel)
        layout.addWidget(self.labelbuttons)

        horizontal_list = QWidget()
        self.flow_layout = FlowLayout.FlowLayout()
        horizontal_list.setLayout(self.flow_layout)

        scroll_area = QScrollArea()
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(horizontal_list)
        layout.addWidget(scroll_area)

        save_button_widget = HorizontalButtonWidget()
        layout.addWidget(save_button_widget)

        save_button_widget.save_button.clicked.connect(self.generate_dataset)
        self.setLayout(layout)
        self.current_index = 0

        if data_points is not None:
            self.loadDataPoints(data_points)
            self.loadImage(self.current_index)

    def loadImage(self, index) -> None:
        self.current_index = index

        self.graphics_scene.clear()
        self.graphics_scene.addPixmap(cvToQPixmap(self.data_points[index].image))
        self.image_viewer.zoomToFit()

    def nextImage(self) -> None:
        self.current_index = (self.current_index + 1) % len(self.data_points)
        self.loadImage(self.current_index)

    def keyPressEvent(self, event) -> None:
        # Global key handling for pressing buttons in LabelButtonWidget
        self.labelbuttons.keyPressEvent(event)

    def setSpecularityLabel(self) -> None:
        self.data_points[self.current_index].label = PointLabel.SPECULARITY
        self.image_buttons[self.current_index].refresh()
        self.nextImage()

    def setLaserpointLabel(self) -> None:
        self.data_points[self.current_index].label = PointLabel.LASERPOINT
        self.image_buttons[self.current_index].refresh()
        self.nextImage()

    def setOtherLabel(self) -> None:
        self.data_points[self.current_index].label = PointLabel.OTHER
        self.image_buttons[self.current_index].refresh()
        self.nextImage()

    def setBasePath(self, base_path: str) -> None:
        self.base_path = base_path

    def loadDataPoints(self, data_points: List[SpecularHightlightDatum]) -> None:
        self.flow_layout.__del__()

        for image_button in self.image_buttons:
            del image_button

        for datum in data_points:
            image_button = ImageButton(datum)
            image_button.button_id_signal.connect(self.loadImage)
            self.flow_layout.addWidget(image_button)
            self.image_buttons.append(image_button)

        self.data_points = data_points

    def save_current_status(self) -> None:
        """Save current labelling effort, will save every image. Even the non-labeled ones."""

        path = "temp"
        os.makedirs(path, exist_ok=True)
        os.makedirs(os.path.join(path, "images"), exist_ok=True)

        self.generate_datadict_and_save_images(
            self.data_points,
            os.path.join(path, "images"),
            os.path.join(path, "labels.json"),
        )

    def save_temp(self) -> None:
        data_dict = {}

        temp_path = os.path.join(self.base_path, "temp")
        image_path = os.path.join(temp_path, "images")
        json_path = os.path.join(temp_path, "labels.json")

        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(temp_path, exist_ok=True)
        os.makedirs(image_path, exist_ok=True)

        self.generate_datadict_and_save_images(
            self.data_points,
            image_path,
            json_path,
        )

    def generate_dataset(self) -> None:
        """Generate dataset with train, val and test split"""
        train_split: float = 0.8
        val_split: float = 0.1
        test_split: float = 0.1

        if train_split + val_split + test_split != 1.0:
            print("Please specify a valid split. They need to sum to 1")
            return None

        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "train"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "val"), exist_ok=True)
        os.makedirs(os.path.join(self.base_path, "test"), exist_ok=True)

        # Find only points that have been labeled
        labeled_points = [
            data_point
            for data_point in self.data_points
            if data_point.label != PointLabel.UNLABELED
        ]

        # Shuffle this list
        shuffle(labeled_points)

        train_split_index = int(len(labeled_points) * train_split)
        val_split_index = int(len(labeled_points) * (train_split + val_split))

        train = labeled_points[0:train_split_index]
        val = labeled_points[train_split_index:val_split_index]
        test = labeled_points[val_split_index:]

        self.generate_datadict_and_save_images(
            train,
            os.path.join(self.base_path, "train"),
            os.path.join(self.base_path, "train_labels.json"),
        )

        self.generate_datadict_and_save_images(
            val,
            os.path.join(self.base_path, "val"),
            os.path.join(self.base_path, "val_labels.json"),
        )

        self.generate_datadict_and_save_images(
            test,
            os.path.join(self.base_path, "test"),
            os.path.join(self.base_path, "test_labels.json"),
        )

    def read_dataset(self, path: str) -> None:
        pass

    def generate_datadict_and_save_images(
        self, data: List[SpecularHightlightDatum], image_save_path: str, json_path: str
    ) -> None:
        data_dict = {}
        for datum in data:
            im_name = "{0}.png".format(datum.image_id)
            relative_image_path = os.path.join(
                os.path.basename(image_save_path), im_name
            )
            absolute_image_path = os.path.join(image_save_path, im_name)

            point_label_dict = {}
            point_label_dict["id"] = datum.image_id
            point_label_dict["path"] = relative_image_path
            point_label_dict["label"] = datum.label.value
            point_label_dict["label_name"] = datum.label.name

            cv2.imwrite(absolute_image_path, datum.image)

            data_dict["{0}".format(datum.image_id)] = point_label_dict

        with open(json_path, "w") as f:
            json.dump(data_dict, f)


class MainWindow(QMainWindow):
    def __init__(self, data_points):
        super(MainWindow, self).__init__()
        self.setCentralWidget(LabelingGUI(data_points))

        menubar = self.menuBar()

        menuFile = menubar.addMenu("File")

        newAction = QAction("New", self)
        newAction.triggered.connect(self.newEvent)

        openAction = QAction("Open", self)
        openAction.triggered.connect(self.openEvent)

        saveAction = QAction("Save", self)
        saveAction.triggered.connect(self.saveEvent)

        generateDatasetAction = QAction("Generate Dataset", self)
        generateDatasetAction.triggered.connect(self.generateDatasetEvent)

        menuFile.addActions([newAction, openAction])
        menuFile.addSeparator()

        menuFile.addActions([saveAction, generateDatasetAction])

    def newEvent(self):
        dataset_base, ok = QInputDialog.getText(
            self, "Dataset", "Please enter where to save the Dataset:"
        )

        if not ok:
            return

        dir_path = QFileDialog.getExistingDirectory(
            caption="Folder containing the images"
        )

        files = os.listdir(dir_path)
        files = sorted(files)

        data_points = []
        for i, file in enumerate(files):
            if file.lower().endswith(".png") or file.lower().endswith(".jpg"):
                image = cv2.imread(os.path.join(dir_path, file))
                data_points.append(
                    SpecularHightlightDatum(image, i, PointLabel.UNLABELED)
                )

        self.centralWidget().setBasePath(dataset_base)
        self.centralWidget().loadDataPoints(data_points)

    def openEvent(self):
        dir_path = QFileDialog.getExistingDirectory(caption="Basefolder of the dataset")

        temp_path = os.path.join(dir_path, "temp")
        json_path = os.path.join(temp_path, "labels.json")

        f = open(json_path)
        data = json.load(f)

        data_points = []

        for _, value in data.items():
            label = value["label"]
            rel_path = value["path"]
            id = value["id"]
            image = cv2.imread(os.path.join(temp_path, rel_path))

            datum = SpecularHightlightDatum(image, id, PointLabel(label))
            data_points.append(datum)

        self.centralWidget().loadDataPoints(data_points)
        self.centralWidget().setBasePath(dir_path)

    def saveEvent(self):
        self.centralWidget().save_temp()

    def generateDatasetEvent(self):
        self.centralWidget().generate_dataset()
