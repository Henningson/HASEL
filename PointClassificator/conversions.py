import cv2
import numpy as np

from PyQt5.QtGui import QPixmap, QImage, QIcon


def cvToQImage(image):
    image_copy = image.copy()
    if len(image.shape) == 2:
        image_copy = cv2.cvtColor(image_copy, cv2.COLOR_GRAY2RGB)

    height, width, channel = image_copy.shape
    bytesPerLine = 3 * width
    return QImage(
        np.require(image_copy, np.uint8, "C"),
        width,
        height,
        bytesPerLine,
        QImage.Format_RGB888,
    )


def cvToQPixmap(image):
    qimage = cvToQImage(image)
    return QPixmap(qimage)


def cvToQIcon(image):
    qpixmap = cvToQPixmap(image)
    return QIcon(qpixmap)
