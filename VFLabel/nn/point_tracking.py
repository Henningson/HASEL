import torch
import numpy as np
import os
from typing import List

from cotracker.predictor import CoTrackerPredictor


def track_points(video: torch.tensor, query_points: np.array, device) -> np.array:
    query_points = torch.from_numpy(query_points).float().to(device)

    # Run Offline CoTracker:
    model = CoTrackerPredictor(
        checkpoint=os.path.join("assets/models/scaled_offline.pth")
    )
    model.to(device)

    pred_tracks, pred_visibility = model(
        video, queries=query_points[None], backward_tracking=True
    )

    return pred_tracks, pred_visibility


if __name__ == "__main__":
    from cotracker.utils.visualizer import Visualizer, read_video_from_path

    video = read_video_from_path("assets/test_data/test_video_1.avi")
    video = (
        torch.from_numpy(video).permute(0, 3, 1, 2)[None].float().to("cpu")
    )  # B T C H W
    pred_tracks, pred_visibility = track_points(
        video, np.array([[0.0, 128.0, 256.0]]), "cpu"
    )

    vis = Visualizer(save_dir="./videos", pad_value=100)
    vis.visualize(
        video=video, tracks=pred_tracks, visibility=pred_visibility, filename="teaser"
    )
