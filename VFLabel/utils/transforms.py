import numpy as np

from PyQt5.QtGui import QImage
from typing import List


def np_2_QImage(image: np.array) -> QImage:
    height, width, channel = image.shape
    bytesPerLine = 3 * width
    return QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)


# We assume NumPy-Style format [NUM_FRAMES, HEIGHT, WIDTH, CHANNEL]
def vid_2_QImage(video: np.array) -> List[QImage]:
    return [np_2_QImage(image) for image in video]


def lerp(v0, v1, t):
    return (1 - t) * v0 + t * v1
