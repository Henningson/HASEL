import numpy as np

from PyQt5.QtGui import QImage


def np_2_QImage(image: np.array) -> QImage:
    height, width, channel = image.shape
    bytesPerLine = 3 * width
    return QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)
