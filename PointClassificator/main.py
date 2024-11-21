import LabelingGUI
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    viewer_app = QApplication(["Specular Highlight Labeling"])
    viewer = LabelingGUI.MainWindow(None)
    viewer.show()

    # Launch the Qt application
    viewer_app.exec()
