import sys
import time

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LoadingBarDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading Bar Example")
        self.setGeometry(100, 100, 400, 200)

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.layout.addWidget(self.progress_bar)

        # Start button
        self.start_button = QPushButton("Start Process", self)
        self.start_button.clicked.connect(self.run_process)
        self.layout.addWidget(self.start_button)

    def run_process(self):
        for i in range(101):  # Simulates a process running from 0% to 100%
            time.sleep(0.05)  # Simulated delay
            self.progress_bar.setValue(i)
            QApplication.processEvents()  # Updates the GUI during the loop


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoadingBarDemo()
    window.show()
    sys.exit(app.exec_())
