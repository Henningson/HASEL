import os
from torch.utils.data import Dataset
import numpy as np
import cv2

import albumentations as A

from VFLabel.utils.defines import NN_MODE
from albumentations.pytorch import ToTensorV2

from typing import List


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
