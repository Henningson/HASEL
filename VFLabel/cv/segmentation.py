import cv2
import numpy as np
import VFLabel.cv.laserpoints

from typing import List


def compute_glottal_midline(segmentation: np.array) -> np.array:
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


# Input is a FRAME x GRID_HEIGHT x GRID_WIDTH x 2 array, that is generated e.g. in PointClickWidget.
def generate_laserpoint_segmentations(
    laserpoint_array: np.array, image_height: int, image_width: int, radius: int = 3
) -> List[np.array]:
    images = []
    for frame in laserpoint_array:
        segmentation = np.zeros((image_height, image_width), dtype=np.uint8)

        laserpoints = VFLabel.cv.laserpoints.get_points_from_tensor(frame)
        for point_2d in laserpoints:
            segmentation = cv2.circle(
                segmentation,
                point_2d.round().astype(int),
                radius,
                color=255,
                thickness=-1,
            )
        images.append(segmentation)

    return images
