import cv2
import numpy as np
import VFLabel.cv.laserpoints

from typing import List


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
