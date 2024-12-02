# In this document, we should implement the point implementation schemes.
import subpixel_point_estimation
import VFLabel.nn.models

import numpy as np
import torch
from typing import List


def filter_points_on_vocalfold(
    point_predictions, vocalfold_segmentations: List[np.array]
):
    # For each predicted point, check if it was predicted on the vocalfold.
    # If not, remove it.
    filtered_points = point_predictions

    return filtered_points


def classify_points(point_predictions_over_time, video_images: List[np.array]):
    # Crop from each point over time
    video = torch.from_numpy(np.array(video_images))
    points = torch.from_numpy(point_predictions_over_time)
    crops, y_windows, x_windows = subpixel_point_estimation.extractWindow(video, points)

    # Normalize points to [0, 1]
    model = VFLabel.nn.models.Kernel3Classificator()
    model.load_state_dict(torch.load("assets/models/specularity_classificator.pth.tar"))

    per_crop_max = crops.max(dim=(-2, -1), keepdim=True)
    per_crop_min = crops.max(dim=(-2, -1), keepdim=True)

    normalized_crops = (crops - per_crop_min) / (per_crop_max - per_crop_min)

    # Use 2-layered CNN to classify points
    prediction = model(normalized_crops)
    classifications = torch.softmax(prediction, dim=-1).argmax(dim=-1)

    # Return per point classes in the same format as points over time
    return classifications


# Points over time is FxNx2
# Classes over time is FxNx1
def compute_subpixel_points(points_over_time, classes_over_time, video):
    video = torch.from_numpy(np.array(video))
    points = torch.from_numpy(points_over_time)

    # Extract point crops
    crops, y_windows, x_windows = subpixel_point_estimation.extractWindow(video, points)

    # 1. Compute sub-pixel position for each point that was classified as visible by the 2 layered network

    # Extract video_regions from points_over_time where classes_over_time is class VISIBLE.

    # Compute sub-pixel point from image via moment method

    # 2. We now need to define different cases for the interpolation:

    # Case 1: VISIBLE -> UNDEFINED -> UNDEFINED -> VISIBLE
    # In this case, we will just interpolate over the undefined areas
    # If the section of undefined points inbetween is longer, we assume thats the glottal gap.

    # Case 2: VISIBLE -> SPECULARITY*N -> VISIBLE
    # If we find any amount of specularities inbetweeb visible points, we just interpolate regularly.
    return None
