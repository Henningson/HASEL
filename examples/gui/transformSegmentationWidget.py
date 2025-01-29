import sys

from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QImage

from PyQt5.QtCore import QPointF

import VFLabel.gui_base


if __name__ == "__main__":

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Zoomable Image View")

            # Create a central widget and a layout
            central_widget = QWidget(self)
            layout = QVBoxLayout(central_widget)

            # Set up the zoomable view
            point_list = [
                QPointF(100, 100),
                QPointF(100, 150),
                QPointF(150, 150),
            ]
            image = QImage("assets/test_data/test_image.png")

            view = VFLabel.gui_base.TransformableSegmentation(
                image, polygon_points=point_list
            )
            layout.addWidget(view)

            # Set up the scene for the view

            # Set up the main window^
            self.setCentralWidget(central_widget)
            self.setGeometry(100, 100, 800, 600)

            # Show the window
            self.show()

    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()

    # Run the application
    sys.exit(app.exec_())
