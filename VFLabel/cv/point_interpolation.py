# In this document, we should implement the point implementation schemes.
import VFLabel.cv.subpixel_point_estimation as subpixel_point_estimation
import VFLabel.nn.models

import albumentations as A
from albumentations.pytorch import ToTensorV2
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
    # TODO: Implement me

    return filtered_points


def classify_points(cotracker_points: np.array, video: np.array):
    # Crop from each point over time
    video = torch.from_numpy(video)
    points = torch.from_numpy(cotracker_points)
    crops, y_windows, x_windows = subpixel_point_estimation.extractWindow(
        video, points, device=points.device
    )

    # Normalize points to [0, 1]
    model = VFLabel.nn.models.BinaryKernel3Classificator()
    model.load_state_dict(
        torch.load(
            "assets/models/binary_specularity_classificator.pth.tar", weights_only=True
        )
    )
    model.eval()

    per_crop_max = crops.amax([-1, -2], keepdim=True)
    per_crop_min = crops.amin([-1, -2], keepdim=True)

    normalized_crops = (crops - per_crop_min) / (per_crop_max - per_crop_min)
    """normalized_crops = normalized_crops.numpy()

    eval_transform = A.Compose(
        [
            A.Normalize(
                mean=[0.0],
                std=[1.0],
                max_pixel_value=255.0,
            ),
            ToTensorV2(),
        ],
    )
    transformed_images = []
    for crop in normalized_crops:
        transformed_images.append(eval_transform(image=crop)["image"])
    normalized_crops = np.concatenate(transformed_images, 0)
    normalized_crops = torch.from_numpy(normalized_crops)"""

    # Use 2-layered CNN to classify points
    prediction = model(normalized_crops[:, None, :, :])
    classifications = (torch.sigmoid(prediction) > 0.5) * 1

    # Return per point classes in the same format as points over time
    return classifications, crops


# Points over time is Nx3
# Classes over time is Nx1
def compute_subpixel_points(
    point_predictions, labels, video, num_points_per_frame: int
):
    crops, y_windows, x_windows = subpixel_point_estimation.extractWindow(
        video, point_predictions, device=point_predictions.device
    )

    # 0.1 Reshape points, classes and crops into per frame segments, such that we can easily extract a timeseries.
    # I.e. shape is after this: NUM_POINTS x NUM_FRAMES x ...
    point_predictions = point_predictions.reshape(
        video.shape[0], num_points_per_frame, 3
    )[:, :, [1, 2]].permute(1, 0, 2)
    y_windows = y_windows.reshape(
        video.shape[0], num_points_per_frame, crops.shape[-2], crops.shape[-1]
    ).permute(1, 0, 2, 3)
    x_windows = x_windows.reshape(
        video.shape[0], num_points_per_frame, crops.shape[-2], crops.shape[-1]
    ).permute(1, 0, 2, 3)
    labels = labels.reshape(video.shape[0], num_points_per_frame).permute(1, 0)
    crops = crops.reshape(
        video.shape[0], num_points_per_frame, crops.shape[-2], crops.shape[-1]
    ).permute(1, 0, 2, 3)

    specular_duration = 5
    # Iterate over every point and class as well as their respective crops
    optimized_points = torch.zeros_like(point_predictions) * np.nan
    for points_index, (points, label, crop) in enumerate(
        zip(point_predictions, labels, crops)
    ):

        # Here it now gets super hacky.
        # Convert label array to a string
        labelstring = "".join(map(str, label.squeeze().tolist()))
        # Replace 0s with V for visible
        compute_string = labelstring.replace("1", "V")

        # This regex looks for occurences of VXV, where X may be any mix of specularity or unidentifiable classifications but at most of length 5.
        # If this is given, we will replace VXV by VIV, where X is replaced by that many Is.#
        # Is indicate that we want to interpolate in these values.
        compute_string = re.sub(
            r"(V)([0]{1,5})(V)",
            lambda match: match.group(1) + "I" * len(match.group(2)) + match.group(3),
            compute_string,
        )
        compute_string = re.sub(
            r"(V)([0]{1,5})(V)",
            lambda match: match.group(1) + "I" * len(match.group(2)) + match.group(3),
            compute_string,
        )

        # Finally, every part that couldn't be identified will be labeled as E for error.
        compute_string = compute_string.replace("0", "E")
        compute_string = compute_string.replace("1", "E")
        compute_string = compute_string.replace("2", "E")
        print(compute_string)

        # Compute sub-pixel position for each point labeled as visible (V)
        for frame_index, label in enumerate(compute_string):
            if label != "V":
                continue

            new_point = torch.from_numpy(
                subpixel_point_estimation.moment_method(
                    crop[frame_index].unsqueeze(0).numpy()
                )
            ).squeeze()
            x_pos = x_windows[points_index, frame_index, 0, 0] + new_point[0]
            y_pos = y_windows[points_index, frame_index, 0, 0] + new_point[1]
            optimized_points[points_index, frame_index] = torch.tensor([x_pos, y_pos])

        # Interpolate inbetween two points
        for frame_index, label in enumerate(compute_string):
            if label != "I":
                continue

            prev_v_index = compute_string.rfind("V", 0, frame_index)
            next_v_index = compute_string.find("V", frame_index + 1)

            lerp_alpha = (frame_index - prev_v_index) / (next_v_index - prev_v_index)
            point_a = points[prev_v_index]
            point_b = points[next_v_index]
            lerped_point = VFLabel.utils.transforms.lerp(point_a, point_b, lerp_alpha)
            optimized_points[points_index, frame_index] = lerped_point

        a = 1

    return optimized_points


if __name__ == "__main__":
    from cotracker.utils.visualizer import Visualizer, read_video_from_path
    import VFLabel.io.data as io
    import VFLabel.utils.defines
    import json
    import os

    project_path = VFLabel.utils.defines.TEST_PROJECT_PATH
    video_path = os.path.join(project_path, "video")

    video = np.array(io.read_images_from_folder(video_path, is_gray=True))[:175]
    dict = io.dict_from_json("projects/test_project/predicted_laserpoints.json")
    points, ids = io.point_dict_to_cotracker(dict)

    classifications, crops = classify_points(points, video)
    points, classes = compute_subpixel_points(
        torch.from_numpy(points),
        classifications,
        torch.from_numpy(video),
        len(dict["Frame0"]),
    )

    a = 1
