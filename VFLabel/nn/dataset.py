import os
import torch
from torch.utils.data import Dataset
import numpy as np
import cv2

import albumentations as A

from VFLabel.utils.defines import NN_MODE
from albumentations.pytorch import ToTensorV2

from typing import List


import cv2

from dataclasses import dataclass
from enum import Enum
import numpy as np

import json
from collections import Counter


class HaselDataset(Dataset):
    def __init__(self, path, train: NN_MODE = NN_MODE.TRAIN, split_factor: float = 0.9):
        self.base_path = path

        train_transform = A.Compose(
            [
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.Rotate(limit=(-40, 40), p=0.5),
                A.Affine(translate_percent=0.15, p=0.5),
                A.RandomGamma(),
                A.RandomBrightnessContrast(),
                A.Perspective(scale=(0.05, 0.2), p=0.5),
                A.Normalize(
                    mean=[0.0],
                    std=[1.0],
                    max_pixel_value=255.0,
                ),
                ToTensorV2(),
            ]
        )

        eval_transform = A.Compose(
            [
                A.Normalize(
                    mean=[0.0],
                    std=[1.0],
                    max_pixel_value=255.0,
                ),
                ToTensorV2(),
            ]
        )

        image_dir = os.path.join(self.base_path, "images")
        segmentation_dir = os.path.join(self.base_path, "laserpoint_segmentations")

        self.transform = train_transform if train == NN_MODE.TRAIN else eval_transform

        self._segmentations = self.load_segmentations(segmentation_dir)
        self._images = self.load_images_from_list(
            image_dir, self.get_files_in_dir(segmentation_dir)
        )

        split_at = int(len(self._segmentations) * split_factor)
        if train == NN_MODE.TRAIN:
            self._segmentations = self._segmentations[0:split_at]
            self._images = self._images[0:split_at]
        else:
            self._segmentations = self._segmentations[split_at:-1]
            self._images = self._images[split_at:-1]

    def load_images(self, path) -> List[np.array]:
        image_data = []
        for file in sorted(os.listdir(path)):
            if file.endswith(".png"):
                img_path = os.path.join(path, file)
                image_data.append(cv2.imread(img_path, 0))

        return image_data

    def load_images_from_list(self, path, files) -> List[np.array]:
        return [cv2.imread(os.path.join(path, file), 0) for file in files]

    def get_files_in_dir(self, path: str) -> List[str]:
        return [file for file in sorted(os.listdir(path)) if file.endswith(".png")]

    def __len__(self):
        return len(self._images)

    def __getitem__(self, index):
        image = self._images[index]
        segmentation = self._segmentations[index]

        if self.transform is not None:
            augmentations = self.transform(image=image, masks=[segmentation])

            image = augmentations["image"]
            segmentation = augmentations["masks"][0]

        return image, segmentation


class Specularity(Dataset):
    def __init__(self, base_path: str, mode: MODE, transform=None):
        path = None
        json_path = None

        if mode == MODE.train:
            json_path = os.path.join(base_path, "train_labels.json")
        elif mode == MODE.eval:
            json_path = os.path.join(base_path, "val_labels.json")
        elif mode == MODE.test:
            json_path = os.path.join(base_path, "test_labels.json")

        self.transform = transform

        f = open(json_path)
        data = json.load(f)

        self.images = []
        self.labels = []

        for _, value in data.items():
            label = value["label"]
            rel_path = value["path"]
            image = cv2.imread(os.path.join(base_path, rel_path), 0)

            image_copy = image.astype(float) / 255
            image_copy = (image_copy - image_copy.min()) / (
                image_copy.max() - image_copy.min()
            )
            image_copy *= 255
            image_copy = image.astype(np.uint8)

            self.images.append(image_copy)
            self.labels.append(label)

    def printStatistics(self):
        counter = Counter(self.labels)

        for key, value in counter.items():
            print(
                "Label: {0}, Occurences: {1}, Percent: {2:0.3f}".format(
                    PointLabel(key), value, value / len(self.images) * 100
                )
            )

    def __len__(self):
        return len(self.images)

    def trimLength(self, amount):
        assert amount < len(self.images)

        self.images = self.images[0:-amount]

    def __getitem__(self, index):
        image = self.images[index]
        label = self.labels[index]

        image = self.transform(image=image)

        return image["image"].to(DEVICE), torch.tensor([label], device=DEVICE)
