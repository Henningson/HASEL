import os
from typing import List

import numpy as np
import torch
from cotracker.predictor import CoTrackerPredictor


def track_points_windowed(
    video: np.array,
    query_points: np.array,
    window_size: int = 50,
    stride: int = 25,
    device="cuda",
) -> np.array:
    video = torch.from_numpy(video).to(device)
    query_points = torch.from_numpy(query_points).float().to(device)

    # Run Offline CoTracker:
    model = CoTrackerPredictor(
        checkpoint=os.path.join("assets/models/scaled_offline.pth")
    )
    model.to(device)

    num_query_points: int = query_points.shape[0]
    video_length: int = video.shape[0]

    final_points = np.zeros([video_length, num_query_points, 2], dtype=float)
    final_visibility = np.zeros([video_length, num_query_points], dtype=np.uint8)
    counts = np.zeros([video_length, num_query_points, 2], dtype=np.float32)
    iterations = video_length // stride

    for i in range(iterations):

        # Calculate the start and end indices for the current chunk
        start_idx = i * stride
        end_idx = min(start_idx + window_size, video_length)

        video_tensor = video[start_idx:end_idx]
        video_tensor = (
            video_tensor.permute(0, 3, 1, 2)[None].float().to(device)
        )  # B T C H W
        pred_tracks, pred_visibility = model(
            video_tensor,
            queries=query_points[None],
            backward_tracking=True,
        )

        # Add the values to the final tensor and update the counts
        final_points[start_idx:end_idx] += pred_tracks.squeeze(0).detach().cpu().numpy()
        final_visibility[start_idx:end_idx] += (
            pred_visibility.squeeze(0).detach().cpu().numpy()
        )
        counts[start_idx:end_idx] += 1

        if i < iterations - 1:
            # Find suitable query points from second half of window size
            frame_with_most_good_points = (
                pred_visibility[:, stride:window_size].sum(dim=-1).argmax()
            )
            new_query_points = torch.zeros_like(query_points)
            new_query_points[:, 0] = frame_with_most_good_points
            new_query_points[:, 1:3] = pred_tracks[
                0, stride + frame_with_most_good_points
            ]
            query_points = new_query_points

    # Average the overlapping regions
    final_points /= counts
    final_visibility = (final_visibility / counts[:, :, 0] > 0.5) * 1.0

    return final_points, final_visibility


def track_points(
    video: torch.tensor, query_points: np.array, device="cuda"
) -> np.array:
    query_points = torch.from_numpy(query_points).float().to(device)

    # Run Offline CoTracker:
    model = CoTrackerPredictor(
        checkpoint=os.path.join("assets/models/scaled_offline.pth")
    )
    model.to(device)

    pred_tracks, pred_visibility = model(
        video,
        queries=query_points[None],
        backward_tracking=True,
    )

    return pred_tracks, pred_visibility


if __name__ == "__main__":
    import json

    from cotracker.utils.visualizer import Visualizer, read_video_from_path

    import VFLabel.io.data as io

    video = read_video_from_path("assets/test_data/test_video_1.avi")[:175]
    dict = io.dict_from_json("projects/test_project/clicked_laserpoints.json")
    points, ids = io.point_dict_to_cotracker(dict)

    pred_points, pred_visibility = track_points_windowed(video, points)

    cotracker_dict = io.cotracker_to_point_dict(pred_points, ids[:, [1, 2]])
    array = io.cotracker_to_numpy_array(pred_points, ids[:, [1, 2]], 18, 18)

    json_path = "projects/test_project/predicted_laserpoints.json"
    io.write_json(json_path, cotracker_dict)

    vis = Visualizer(save_dir="./videos", pad_value=100)
    vis.visualize(
        video=torch.from_numpy(video).permute(0, 3, 1, 2)[None].float(),
        tracks=torch.from_numpy(pred_points).unsqueeze(0),
        visibility=torch.from_numpy(pred_visibility).unsqueeze(0),
        filename="teaser",
    )
