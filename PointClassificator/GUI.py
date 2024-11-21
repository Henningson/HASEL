import os

from typing import List
from SpecularHighlightData import SpecularHightlightDatum, PointLabel

from PyQt5.QtCore import QLibraryInfo

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(
    QLibraryInfo.PluginsPath
)

from PyQt5.QtGui import QTransform, QIcon
from PyQt5.QtWidgets import (
    QGraphicsView,
    QHBoxLayout,
    QWidget,
    QPushButton,
)
from PyQt5.QtCore import QSize, Qt, pyqtSignal


from conversions import cvToQPixmap


class ZoomableView(QGraphicsView):
    def __init__(self, parent=None):
        super(ZoomableView, self).__init__(parent)
        self.zoom = 1.0

    def wheelEvent(self, event):
        mouse = event.angleDelta().y() / 120

        if mouse > 0:
            self.zoomIn()
        else:
            self.zoomOut()

    def zoomIn(self):
        self.zoom *= 1.1
        self.updateView()

    def zoomOut(self):
        self.zoom /= 1.1
        self.updateView()

    def zoomReset(self):
        self.zoom = 1
        self.updateView()

    def zoomToFit(self):
        self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)

    def updateView(self):
        self.setTransform(QTransform().scale(self.zoom, self.zoom))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.zoomToFit()

    """
    def mousePressEvent(self, event):
        super(type(self), self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super(type(self), self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super(type(self), self).mouseReleaseEvent(event)
    """


class KeypressButton(QPushButton):
    def __init__(self, key, text="Button", parent=None):
        super(KeypressButton, self).__init__(text, parent)
        self.event_key = key

    def keyPressEvent(self, event):
        if event.key() == self.event_key:
            self.clicked.emit()


class ImageButton(QPushButton):
    button_id_signal = pyqtSignal(int)

    def __init__(self, data_point: SpecularHightlightDatum, parent=None):
        super(ImageButton, self).__init__("", parent=parent)
        self.data_point = data_point
        self.id = data_point.image_id

        pixmap = cvToQPixmap(data_point.image)
        self.setIcon(QIcon(pixmap.scaled(100, 100)))
        self.setIconSize(QSize(100, 100))

        self.clicked.connect(self.emit_id)

        self.refresh()

    def emit_id(self):
        self.button_id_signal.emit(self.id)

    def refresh(self):
        if self.data_point.label == PointLabel.LASERPOINT:
            self.setStyleSheet("border: 5px solid #00AA00;")
        elif self.data_point.label == PointLabel.SPECULARITY:
            self.setStyleSheet("border: 5px solid #FF0000;")
        elif self.data_point.label == PointLabel.OTHER:
            self.setStyleSheet("border: 5px solid #0000AA;")
        else:
            self.setStyleSheet("border: 5px solid #000000;")


class LabelButtonWidget(QWidget):
    def __init__(self, parent=None):
        super(LabelButtonWidget, self).__init__(parent)
        layout = QHBoxLayout()

        self.laserdot_button = KeypressButton(Qt.Key.Key_1, "(1) Laserdot")
        self.specular_button = KeypressButton(Qt.Key.Key_2, "(2) Specular Highlight")
        self.anything_button = KeypressButton(Qt.Key.Key_3, "(3) Anything Else")

        layout.addWidget(self.laserdot_button)
        layout.addWidget(self.specular_button)
        layout.addWidget(self.anything_button)

        self.setLayout(layout)

    def keyPressEvent(self, event):
        self.laserdot_button.keyPressEvent(event)
        self.specular_button.keyPressEvent(event)
        self.anything_button.keyPressEvent(event)


class HorizontalButtonWidget(QWidget):
    def __init__(self, parent=None):
        super(HorizontalButtonWidget, self).__init__(parent)
        layout = QHBoxLayout()

        self.save_button = QPushButton("Save Current Status")

        layout.addWidget(self.save_button)
        self.setLayout(layout)
