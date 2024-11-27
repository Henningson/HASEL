import numpy as np
from typing import List


def glottal_area_waveform(segmentation_video: np.array) -> np.array:
    return segmentation_video.sum(axis=(1, 2))


def glottal_midline_video(segmentation_video: np.array) -> List[np.array]:
    return [glottal_midline(frame) for frame in segmentation_video]


def glottal_midline(segmentation: np.array) -> np.array:
    glottal_point_indices = np.argwhere(segmentation > 0)

    if glottal_point_indices.size == 0:
        return None, None

    y = glottal_point_indices[:, 1]
    x = glottal_point_indices[:, 0]

    A = np.vstack(np.vstack([x, np.ones(len(x))]).T)
    m, c = np.linalg.lstsq(A, y, rcond=None)[0]

    upper_point = np.array([m * x.min() + c, x.min()])
    lower_point = np.array([m * x.max() + c, x.max()])

    return upper_point, lower_point
