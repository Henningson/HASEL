import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)


class BrushScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.brush_color = Qt.black
        self.brush_size = 5
        self.previous_point = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.previous_point = event.scenePos()
            self.add_ellipse_at_point(event.scenePos())

    def mouseMoveEvent(self, event):
        if self.previous_point:
            current_point = event.scenePos()
            self.add_line_between_points(self.previous_point, current_point)
            self.previous_point = current_point

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.previous_point = None

    def add_ellipse_at_point(self, point):
        brush = QBrush(self.brush_color)
        pen = QPen(self.brush_color)
        self.addEllipse(
            point.x() - self.brush_size / 2,
            point.y() - self.brush_size / 2,
            self.brush_size,
            self.brush_size,
            pen,
            brush,
        )

    def add_line_between_points(self, point1, point2):
        pen = QPen(self.brush_color)
        pen.setWidth(self.brush_size)
        self.addLine(point1.x(), point1.y(), point2.x(), point2.y(), pen)


class BrushView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.scene = scene

    def wheelEvent(self, event):
        delta = event.angleDelta().y() // 120  # Mouse wheel delta
        new_size = max(1, self.scene.brush_size + delta)

        if new_size != self.scene.brush_size:
            self.scene.brush_size = new_size
            self.parent().parent().update_window_title()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Size: 5")

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Graphics scene and view
        self.scene = BrushScene()
        self.view = BrushView(self.scene, self)
        self.layout.addWidget(self.view)

        # Set the scene size
        self.scene.setSceneRect(0, 0, 800, 600)

    def update_window_title(self):
        self.setWindowTitle(f"Brush Size: {self.scene.brush_size}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
