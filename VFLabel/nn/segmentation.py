import os
from typing import List

import albumentations as A
import numpy as np
import segmentation_models_pytorch as smp
import torch
from albumentations.pytorch import ToTensorV2
from tqdm import tqdm

import VFLabel.io.data
import VFLabel.nn.train_binary_seg_model

# TODO: Pass device along in functions instead of defining it globally
DEVICE = "cpu"


def segment_glottis(encoder: str, images: List[np.array]):

    model_path = os.path.join("assets", "models", f"glottis_{encoder}.pth.tar")
    model = smp.Unet(
        encoder_name=encoder,  # choose encoder, e.g. mobilenet_v2 or efficientnet-b7
        encoder_weights="imagenet",  # use `imagenet` pre-trained weights for encoder initialization
        in_channels=3,  # model input channels (1 for gray-scale images, 3 for RGB, etc.)
        classes=1,
    ).to(DEVICE)
    state_dict = torch.load(model_path, weights_only=True)

    if "optimizer" in state_dict:
        del state_dict["optimizer"]

    model.load_state_dict(state_dict)

    transform = A.Compose(
        [
            A.Normalize(),
            ToTensorV2(),
        ]
    )

    segmentations = []
    for image in tqdm(images):
        augmentations = transform(image=image)
        image = augmentations["image"]

        image = image.to(device=DEVICE).unsqueeze(0)

        pred_seg = model(image).squeeze()
        sigmoid = pred_seg.sigmoid()
        segmentation = (sigmoid > 0.5) * 255
        segmentations.append(segmentation.detach().cpu().numpy())
    return segmentations


def segment_glottis_from_folder(
    encoder: str,
    image_folder: str,
) -> List[np.array]:

    image_files = VFLabel.io.read_images_from_folder(image_folder)

    model_path = os.path.join("assets", "models", f"glottis_{encoder}.pth.tar")

    model = smp.Unet(
        encoder_name=encoder,  # choose encoder, e.g. mobilenet_v2 or efficientnet-b7
        encoder_weights="imagenet",  # use `imagenet` pre-trained weights for encoder initialization
        in_channels=3,  # model input channels (1 for gray-scale images, 3 for RGB, etc.)
        classes=1,
    ).to(DEVICE)
    state_dict = torch.load(model_path, weights_only=True)

    if "optimizer" in state_dict:
        del state_dict["optimizer"]

    model.load_state_dict(state_dict)

    transform = A.Compose(
        [
            A.Normalize(),
            ToTensorV2(),
        ]
    )

    segmentations = []
    for image in tqdm(image_files):
        augmentations = transform(image=image)
        image = augmentations["image"]

        image = image.to(device=DEVICE).unsqueeze(0)

        pred_seg = model(image).squeeze()
        sigmoid = pred_seg.sigmoid()
        segmentation = (sigmoid > 0.5) * 255
        segmentations.append(segmentation.detach().cpu().numpy())
    return segmentations


if __name__ == "__main__":
    import cv2

    images = VFLabel.io.data.read_images_from_folder("assets/test_data/MK_CROP")
    segmentations = segment_glottis("efficientnet-b0", images)

    for segmentation in segmentations:
        cv2.imwrite("Test.png", segmentation)
