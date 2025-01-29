import sys

from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QMainWindow,
    QVBoxLayout,
    QWidget,  #
    QMessageBox,
)
from PyQt5.QtGui import QImage

import VFLabel.gui_base.viewPointClicker
import VFLabel.utils.defines

if __name__ == "__main__":

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Generate Some Points for a Video")

            # Create a central widget and a layout
            central_widget = QWidget(self)
            layout = QVBoxLayout(central_widget)

            videodata = VFLabel.io.data.read_video("assets/test_data/test_video_1.avi")
            grid_height = 18
            grid_width = 18
            # Set up the zoomable view
            view = VFLabel.gui_base.viewPointClicker.PointClickerView(
                grid_height,
                grid_width,
                0,
                50,
                videodata,
                VFLabel.utils.defines.TEST_PROJECT_PATH,
            )
            layout.addWidget(view)

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
