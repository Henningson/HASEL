# In this document, we should implement the point implementation schemes.
import VFLabel.cv.subpixel_point_estimation as subpixel_point_estimation
import VFLabel.nn.models

import numpy as np
import torch
import re
from typing import List


def filter_points_on_vocalfold(
    point_predictions, vocalfold_segmentations: List[np.array]
):
    # For each predicted point, check if it was predicted on the vocalfold.
    # If not, remove it.
    filtered_points = point_predictions

    return filtered_points


def classify_points(cotracker_points: np.array, video: np.array):
    # Crop from each point over time
    video = torch.from_numpy(video)
    points = torch.from_numpy(cotracker_points)
    crops, y_windows, x_windows = subpixel_point_estimation.extractWindow(
        video, points, device=points.device
    )

    # Normalize points to [0, 1]
    model = VFLabel.nn.models.Kernel3Classificator()
    model.load_state_dict(torch.load("assets/models/specularity_classificator.pth.tar"))
    model.eval()

    per_crop_max = crops.amax([-1, -2], keepdim=True)
    per_crop_min = crops.amin([-1, -2], keepdim=True)

    normalized_crops = (crops - per_crop_min) / (per_crop_max - per_crop_min)

    # Use 2-layered CNN to classify points
    prediction = model(normalized_crops[:, None, :, :])
    classifications = torch.softmax(prediction, dim=-1).argmax(dim=-1, keepdim=True)

    # Return per point classes in the same format as points over time
    return classifications, crops


# Points over time is Nx3
# Classes over time is Nx1
def compute_subpixel_points(
    point_predictions, classes, crops, num_points_per_frame: int
):
    # 0.1 Reshape points, classes and crops into per frame segments, such that we can easily extract a timeseries.
    # I.e. shape is after this: NUM_POINTS x NUM_FRAMES x ...
    point_predictions = point_predictions.reshape(-1, num_points_per_frame, 3)[
        :, :, [1, 2]
    ].permute(1, 0, 2)
    classes = classes.reshape(-1, num_points_per_frame, 1).permute(1, 0, 2)
    crops = crops.reshape(
        -1, num_points_per_frame, crops.shape[-2], crops.shape[-1]
    ).permute(1, 0, 2, 3)

    specular_duration = 5
    # Iterate over every point and class as well as their respective crops
    optimized_points = torch.zeros_like(point_predictions)
    for point, label, crop in zip(points, classes, crops):

        # Here it now gets super hacky.
        # Convert label array to a string
        labelstring = "".join(map(str, label.squeeze().tolist()))
        # Replace 0s with V for visible
        compute_string = labelstring.replace("0", "V")

        # This regex looks for occurences of VXV, where X may be any mix of specularity or unidentifiable classifications but at most of length 5.
        # If this is given, we will replace VXV by VIV, where X is replaced by that many Is.#
        # Is indicate that we want to interpolate in these values.
        compute_string = re.sub(
            r"(V)([12]{1,5})(V)",
            lambda match: match.group(1) + "I" * len(match.group(2)) + match.group(3),
            compute_string,
        )
        compute_string = re.sub(
            r"(V)([12]{1,5})(V)",
            lambda match: match.group(1) + "I" * len(match.group(2)) + match.group(3),
            compute_string,
        )

        # Finally, every part that couldn't be identified will be labeled as E for error.
        compute_string = compute_string.replace("1", "E")
        compute_string = compute_string.replace("2", "E")

        # TODO: Compute sub-pixel position for each point labeled as 0
        # TODO: Interpolate based on specific cases
        # TODO: Lets regex this shit
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


if __name__ == "__main__":
    from cotracker.utils.visualizer import Visualizer, read_video_from_path
    import VFLabel.io.data as io
    import VFLabel.utils.defines
    import json
    import os

    project_path = VFLabel.utils.defines.TEST_PROJECT_PATH
    video_path = os.path.join(project_path, "video")

    video = np.array(io.read_images_from_folder(video_path, is_gray=True))
    dict = io.dict_from_json("projects/test_project/predicted_laserpoints.json")
    points, ids = io.point_dict_to_cotracker(dict)

    classifications, crops = classify_points(points, video)
    compute_subpixel_points(
        torch.from_numpy(points), classifications, crops, len(dict["Frame0"])
    )
