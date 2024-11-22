# In this document, we should implement the point implementation schemes.
import numpy as np
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

    # Normalize points to [0, 1] ([-1, 1] for Sigmoids?)

    # Use 2-layered CNN to classify points

    # Return per point classes in the same format as points over time
    return None


def compute_subpixel_points(points_over_time, classes_over_time, video):
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
