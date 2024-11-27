import sys

from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QImage

import VFLabel.gui

if __name__ == "__main__":

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Zoomable Image View")

            # Create a central widget and a layout
            central_widget = QWidget(self)
            layout = QVBoxLayout(central_widget)

            # Set up the zoomable view
            view = VFLabel.gui.ZoomableViewWidget(self)
            layout.addWidget(view)

            # Load an image to display in the view
            image = QImage("assets/test_data/test_image.png")
            view.set_image(image)

            # Set up the main window
            self.setCentralWidget(central_widget)
            self.setGeometry(100, 100, 800, 600)

            # Show the window
            self.show()

    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()

    # Run the application
    sys.exit(app.exec_())
