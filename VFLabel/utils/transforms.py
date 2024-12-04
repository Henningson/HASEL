import numpy as np
import cv2

from PyQt5.QtGui import QImage
from typing import List


def qpixmap_to_cv(qpixmap):
    # Convert QPixmap to QImage
    qimage = qpixmap.toImage()

    # Ensure the image is in a readable format (RGB32 or ARGB32)
    qimage = qimage.convertToFormat(QImage.Format_RGBA8888)

    # Get width, height, and byte data
    width = qimage.width()
    height = qimage.height()
    ptr = qimage.bits()
    ptr.setsize(qimage.byteCount())

    # Convert to NumPy array
    array = np.array(ptr).reshape((height, width, 4))  # RGBA

    # Convert RGBA to BGR (OpenCV format)
    cv_image = cv2.cvtColor(array, cv2.COLOR_RGBA2BGR)

    return cv_image


def np_2_QImage(image: np.array) -> QImage:
    height, width, channel = image.shape
    bytesPerLine = 3 * width
    return QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)


# We assume NumPy-Style format [NUM_FRAMES, HEIGHT, WIDTH, CHANNEL]
def vid_2_QImage(video: np.array) -> List[QImage]:
    return [np_2_QImage(image) for image in video]


def lerp(v0, v1, t):
    return (1 - t) * v0 + t * v1
