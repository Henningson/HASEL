# In this document, we should implement the point implementation schemes.
import VFLabel.cv.subpixel_point_estimation as subpixel_point_estimation
import VFLabel.nn.models

import albumentations as A
from albumentations.pytorch import ToTensorV2
import numpy as np
import torch
import re
from typing import List

from scipy.optimize import curve_fit
import torch.nn.functional as F


def filter_points_not_on_vocalfold(
    point_predictions, vocalfold_segmentations: np.array
) -> np.array:
    # Convert all nans to 0
    filtered_points = np.nan_to_num(point_predictions, 0)

    # Floor points and cast such that we have pixel coordinates
    point_indices = np.floor(filtered_points).astype(int)

    for frame_index, (points_in_frame, segmentation) in enumerate(
        zip(point_indices, vocalfold_segmentations)
    ):
        hits = segmentation[points_in_frame[:, 1], points_in_frame[:, 0]]
        hits = (hits > 0) * 1
        filtered_points[frame_index] *= hits[:, None]

    filtered_points[filtered_points == 0] = np.nan

    return filtered_points


def filter_points_on_glottis(
    point_predictions, vocalfold_segmentations: np.array
) -> np.array:
    # Convert all nans to 0
    filtered_points = np.nan_to_num(point_predictions, 0)

    # Floor points and cast such that we have pixel coordinates
    point_indices = np.floor(filtered_points).astype(int)

    for frame_index, (points_in_frame, segmentation) in enumerate(
        zip(point_indices, vocalfold_segmentations)
    ):
        hits = segmentation[points_in_frame[:, 1], points_in_frame[:, 0]]
        hits = (hits == 0) * 1
        filtered_points[frame_index] *= hits[:, None]

    filtered_points[filtered_points == 0] = np.nan

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
            "assets/models/binary_specularity_classificator.pth.tar",
            weights_only=True,
            map_location=torch.device("cpu"),
        )
    )
    model.eval()

    per_crop_max = crops.amax([-1, -2], keepdim=True)
    per_crop_min = crops.amin([-1, -2], keepdim=True)

    normalized_crops = (crops - per_crop_min) / (per_crop_max - per_crop_min)

    # Use 2-layered CNN to classify points
    prediction = model(normalized_crops[:, None, :, :])
    classifications = (torch.sigmoid(prediction) > 0.5) * 1

    # Return per point classes in the same format as points over time
    return classifications, crops


def quadratic_2d(coords, a, b, c, d, e, f):
    x, y = coords
    return a * x**2 + b * y**2 + c * x * y + d * x + e * y + f


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
    optimized_points_on_crops = torch.zeros_like(point_predictions) * np.nan
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
            r"(V)([0]+)(V)",
            lambda match: match.group(1) + "I" * len(match.group(2)) + match.group(3),
            compute_string,
        )
        compute_string = re.sub(
            r"(V)([0]+)(V)",
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

            normalized_crop = crop[frame_index]
            normalized_crop = (normalized_crop - normalized_crop.min()) / (
                normalized_crop.max() - normalized_crop.min()
            )

            # Find local maximum in 5x5 crop
            local_maximum = torch.unravel_index(
                torch.argmax(normalized_crop[1:-1, 1:-1]), [5, 5]
            )

            # Add one again, since we removed the border from the local maximum lookup
            x0, y0 = local_maximum[1] + 1, local_maximum[0] + 1

            # Get 3x3 subwindow from crop, where the local maximum is centered.
            neighborhood = 1
            x_min = max(0, x0 - neighborhood)
            x_max = min(normalized_crop.shape[1], x0 + neighborhood + 1)
            y_min = max(0, y0 - neighborhood)
            y_max = min(normalized_crop.shape[0], y0 + neighborhood + 1)

            sub_image = normalized_crop[y_min:y_max, x_min:x_max]
            sub_image = (sub_image - sub_image.min()) / (
                sub_image.max() - sub_image.min()
            )

            centroids = subpixel_point_estimation.moment_method_torch(
                sub_image.unsqueeze(0)
            ).squeeze()

            refined_x = (
                x_windows[points_index, frame_index, 0, 0] + centroids[0] + x0 - 1
            ).item()
            refined_y = (
                y_windows[points_index, frame_index, 0, 0] + centroids[1] + y0 - 1
            ).item()

            on_crop_x = (x0 + centroids[0] - 1).item()
            on_crop_y = (y0 + centroids[1] - 1).item()

            optimized_points[points_index, frame_index] = torch.tensor(
                [refined_x, refined_y]
            )
            optimized_points_on_crops[points_index, frame_index] = torch.tensor(
                [on_crop_x, on_crop_y]
            )

        # Interpolate inbetween two points
        for frame_index, label in enumerate(compute_string):
            if label != "I":
                continue

            prev_v_index = compute_string.rfind("V", 0, frame_index)
            next_v_index = compute_string.find("V", frame_index + 1)

            lerp_alpha = (frame_index - prev_v_index) / (next_v_index - prev_v_index)
            point_a = optimized_points[points_index, prev_v_index]
            point_b = optimized_points[points_index, next_v_index]
            lerped_point = VFLabel.utils.transforms.lerp(point_a, point_b, lerp_alpha)

            optimized_points[points_index, frame_index] = lerped_point

    return optimized_points, optimized_points_on_crops


def fill_nan_border_values(points: torch.tensor) -> torch.tensor:

    for point_index, point_over_time in enumerate(points):
        nan_count_start = 0
        nan_count_end = 0

        nan_mask = torch.isnan(point_over_time[:, 0])

        for val in nan_mask:
            # Count nans at beginning of sequence
            if val:
                nan_count_start += 1
            else:
                break

        for val in nan_mask.flip(0):
            # Count nans at end of sequence
            if val:
                nan_count_end += 1
            else:
                break

        if nan_count_end == nan_count_start:
            # Only nans, here we do nothing. Could also check that beforehand.
            continue

        if nan_count_end != 0:
            point_over_time = point_over_time[nan_count_start:-nan_count_end]
        else:
            point_over_time = point_over_time[nan_count_start:]

        point_over_time = torch.nn.functional.pad(
            point_over_time.permute(1, 0), (nan_count_start, nan_count_end), "replicate"
        ).permute(1, 0)
        points[point_index] = point_over_time

    return points


def smooth_points(points: torch.tensor) -> torch.tensor:
    # We know that only values are nan, that lie at the border of the frames.
    # So we can easily convolve with a gaussian kernel

    # Define a Gaussian kernel
    def gaussian_kernel(size, sigma):
        x = torch.arange(-size // 2 + 1, size // 2 + 1)
        kernel = torch.exp(-0.5 * (x / sigma) ** 2)
        kernel /= kernel.sum()  # Normalize
        return kernel

    kernel_size = 5
    sigma = 1.0
    kernel = gaussian_kernel(kernel_size, sigma).view(1, 1, -1)

    for point_over_time in points:
        is_not_nan = ~torch.isnan(point_over_time[:, 0])
        non_nan_points = point_over_time[is_not_nan]

        if len(non_nan_points) < 10:
            continue

        a = non_nan_points.permute(1, 0).unsqueeze(1)
        padded_points = torch.nn.functional.pad(
            a, (kernel_size // 2, kernel_size // 2), "replicate"
        )
        smoothed_points = F.conv1d(padded_points, kernel.double(), padding=0)
        smoothed_points = smoothed_points.squeeze(1).permute(1, 0)
        point_over_time[is_not_nan] = smoothed_points

    return points


if __name__ == "__main__":
    from cotracker.utils.visualizer import Visualizer, read_video_from_path
    import VFLabel.io.data as io
    import VFLabel.utils.defines
    import json
    import os
    import matplotlib.pyplot as plt

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

    points = smooth_points(points)
    points = fill_nan_border_values(points)

    average_per_frame_movement = torch.zeros_like(points[0, :, :])
    counts = torch.zeros_like(points[:, 0, :1])

    for per_frame_points in points:
        average_per_frame_movement = torch.nan_to_num(per_frame_points, 0.0)
        counts = ~torch.isnan(per_frame_points[:, 0]).any(dim=-1, keepdims=True)

    x_diff = torch.diff(average_per_frame_movement[:, 0])
    y_diff = torch.diff(average_per_frame_movement[:, 1])
    diff = (x_diff.pow(2) + y_diff.pow(2)).sqrt()

    # Define a Gaussian kernel
    def gaussian_kernel(size, sigma):
        x = torch.arange(-size // 2 + 1, size // 2 + 1)
        kernel = torch.exp(-0.5 * (x / sigma) ** 2)
        kernel /= kernel.sum()  # Normalize
        return kernel

    kernel_size = 7
    sigma = 2.0
    kernel = gaussian_kernel(kernel_size, sigma).view(1, 1, -1)

    smoothed_values = F.conv1d(
        diff.view(1, 1, -1), kernel.double(), padding=kernel_size // 2
    ).squeeze()
    plt.plot(diff.numpy().squeeze())
    plt.show()

    for per_frame_points in points:
        x_values = per_frame_points[:, 0]
        x_mean = x_values[~torch.isnan(x_values)].mean()
        x_values = torch.nan_to_num(x_values, x_mean)

        y_values = per_frame_points[:, 1]
        y_mean = y_values[~torch.isnan(y_values)].mean()
        y_values = torch.nan_to_num(y_values, y_mean)

        x_diff = torch.diff(x_values)
        y_diff = torch.diff(y_values)

        diff = (x_diff.pow(2) + y_diff.pow(2)).sqrt()

        # Define a Gaussian kernel
        def gaussian_kernel(size, sigma):
            x = torch.arange(-size // 2 + 1, size // 2 + 1)
            kernel = torch.exp(-0.5 * (x / sigma) ** 2)
            kernel /= kernel.sum()  # Normalize
            return kernel

        kernel_size = 7
        sigma = 2.0
        kernel = gaussian_kernel(kernel_size, sigma).view(1, 1, -1)

        # Reshape values to match conv1d input format: [batch, channels, length]
        diff = diff.view(1, 1, -1)

        # Apply convolution (with padding to preserve length)
        smoothed_values = F.conv1d(
            diff, kernel.double(), padding=kernel_size // 2
        ).squeeze()

        data = smoothed_values.numpy()
        plt.plot(data)
        plt.show()

    a = 1
