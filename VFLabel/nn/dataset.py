import json
import os
import re
from collections import Counter
from typing import List

import albumentations as A
import cv2
import numpy as np
import torch
from albumentations.pytorch import ToTensorV2
from torch.utils.data import Dataset

import VFLabel.utils.enums
from VFLabel.utils.enums import NN_MODE


class HaselDataset(Dataset):
    def __init__(
        self,
        path,
        train: NN_MODE = NN_MODE.TRAIN,
        preprocess_func=None,
        split_factor: float = 0.9,
    ):
        self.base_path = path
        self.preprocess_func = preprocess_func

        train_transform = A.Compose(
            [
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.Rotate(limit=(-40, 40), p=0.5),
                A.Affine(translate_percent=0.15, p=0.5),
                A.RandomGamma(),
                A.RandomBrightnessContrast(),
                # A.Perspective(scale=(0.05, 0.2), p=0.5),
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

        if self.preprocess_func:
            image = self.preprocess_func(image)

        return image, segmentation


class Specularity(Dataset):
    def __init__(self, base_path: str, mode: NN_MODE, transform=None):
        json_path = None

        if mode == NN_MODE.TRAIN:
            json_path = os.path.join(base_path, "train_labels.json")
        elif mode == NN_MODE.EVAL:
            json_path = os.path.join(base_path, "val_labels.json")
        elif mode == NN_MODE.TEST:
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
            image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
            image_copy = image.astype(np.uint8)

            self.images.append(image_copy)
            self.labels.append(label)

    def printStatistics(self):
        counter = Counter(self.labels)

        for key, value in counter.items():
            print(
                "Label: {0}, Occurences: {1}, Percent: {2:0.3f}".format(
                    VFLabel.utils.enums.PointLabel(key),
                    value,
                    value / len(self.images) * 100,
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

        if self.transform is not None:
            image = self.transform(image=image)["image"]

        return image, torch.tensor([label])


class HLE_BAGLS_Fireflies_Dataset(Dataset):
    def __init__(self, datasets_path: str, mode: NN_MODE, split_at: float = 0.9):
        self.base_path = datasets_path

        train_transform = A.Compose(
            [
                A.Resize(height=512, width=256),
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.Rotate(limit=(-40, 40), p=0.5),
                A.Affine(translate_percent=0.15, p=0.5),
                # A.RandomGamma(),
                # A.RandomBrightnessContrast(),
                A.Normalize(),
                ToTensorV2(),
            ]
        )

        eval_transform = A.Compose(
            [
                A.Resize(height=512, width=256),
                A.Normalize(),
                ToTensorV2(),
            ]
        )

        self.transform = train_transform if mode == NN_MODE.TRAIN else eval_transform
        self.segmentations = None

        ff_images, ff_segmentations = self.load_fireflies(
            os.path.join(self.base_path, "fireflies_dataset_v5"), mode
        )

        bagls_images, bagls_segmentations = self.load_bagls(
            os.path.join(self.base_path, "BAGLS"), mode
        )

        hle_images, hle_segmentations = self.load_hle(
            os.path.join(self.base_path, "HLEDataset", "dataset"), mode
        )

        if mode != NN_MODE.TEST:
            ff_images = self.split(ff_images, split_at, mode)
            ff_segmentations = self.split(ff_segmentations, split_at, mode)

            bagls_images = self.split(bagls_images, split_at, mode)
            bagls_segmentations = self.split(bagls_segmentations, split_at, mode)

        self._segmentations = ff_segmentations + bagls_segmentations + hle_segmentations
        self._images = ff_images + bagls_images + hle_images

    def split(self, images, split_factor, mode: NN_MODE):
        split_at = int(len(images) * split_factor)
        if mode == NN_MODE.TRAIN:
            images = images[0:split_at]
        elif mode == NN_MODE.EVAL:
            images = images[split_at:-1]

        return images

    def load_fireflies(self, fireflies_path: str, mode: NN_MODE):

        if mode == NN_MODE.TRAIN or mode == NN_MODE.EVAL:
            fireflies_path = os.path.join(fireflies_path, "train")
        else:
            fireflies_path = os.path.join(fireflies_path, "test")

        images = self.load_image_paths(os.path.join(fireflies_path, "images"))
        segmentations = self.load_image_paths(
            os.path.join(fireflies_path, "segmentation")
        )

        return images, segmentations

    def load_bagls(self, bagls_path: str, mode: NN_MODE):
        if mode == NN_MODE.TRAIN or mode == NN_MODE.EVAL:
            bagls_path = os.path.join(bagls_path, "training")
        else:
            bagls_path = os.path.join(bagls_path, "test")

        images = self.load_bagls_image_paths(bagls_path)
        segmentations = self.load_bagls_segmentation_paths(bagls_path)

        return images, segmentations

    def load_hle(self, hle_path: str, mode: NN_MODE):
        keys = None
        if mode == NN_MODE.TRAIN:
            keys = ["CF", "CM", "DD", "FH"]
        elif mode == NN_MODE.EVAL:
            keys = ["LS"]
        elif mode == NN_MODE.TEST:
            keys = ["MK", "MS", "RH", "SS", "TM"]

        images = self.load_hle_image_paths(hle_path, keys)
        segmentations = self.load_hle_segmentation_paths(hle_path, keys)

        return images, segmentations

    def load_hle_image_paths(self, hle_path, keys) -> List[str]:
        image_data = []
        for dir in keys:
            image_data += self.load_image_paths(os.path.join(hle_path, dir, "png"))

        return image_data

    def load_hle_segmentation_paths(self, hle_path, keys) -> List[str]:
        image_data = []
        for dir in keys:
            image_data += self.load_image_paths(
                os.path.join(hle_path, dir, "glottal_mask")
            )

        return image_data

    def preprocess_fireflies_segmentations(self, segmentation: np.array):
        segmentation[segmentation == 3] = 2
        segmentation[segmentation == 2] = 0
        return segmentation

    def load_bagls_image_paths(self, path) -> List[str]:
        image_paths = []
        files = os.listdir(path)

        # Why are these files not 0-indexed? :(
        # Need to sort them by regexing first.
        sorted_files = sorted(files, key=lambda x: int(re.search(r"\d+", x).group()))
        for file in sorted_files:
            if file.endswith(".png") and not "_" in file:
                image_paths.append(os.path.join(path, file))

        return image_paths

    def load_bagls_segmentation_paths(self, path) -> List[str]:
        image_paths = []
        files = os.listdir(path)

        # Why are these files not 0-indexed? :(
        # Need to sort them by regexing first.
        sorted_files = sorted(files, key=lambda x: int(re.search(r"\d+", x).group()))
        for file in sorted_files:
            if file.endswith(".png") and "_seg" in file:
                image_paths.append(os.path.join(path, file))

        return image_paths

    def load_image_paths(self, path) -> List[str]:
        image_paths = []
        for file in sorted(os.listdir(path)):
            if file.endswith(".png"):
                image_paths.append(os.path.join(path, file))

        return image_paths

    def __len__(self):
        return len(self._images)

    def __getitem__(self, index):
        image = cv2.imread(self._images[index], 1)
        segmentation = cv2.imread(self._segmentations[index], 0)

        if "fireflies" in self._segmentations[index]:
            segmentation = self.preprocess_fireflies_segmentations(segmentation)
        else:
            segmentation[segmentation > 0] = 1

        if self.transform is not None:
            augmentations = self.transform(image=image, masks=[segmentation])

            image = augmentations["image"]
            segmentation = augmentations["masks"][0]

        return image, segmentation
