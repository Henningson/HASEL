import time

from PyQt5.QtCore import QObject, QSize, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QProgressDialog


class ProgressDialog:
    def __init__(self, iterable, title="Progress", parent=None):
        self.iterable = iterable
        self.total = len(iterable)
        self.progress = QProgressDialog(title, None, 0, self.total, parent)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setValue(0)
        self.cancelled = False

        def handle_cancel():
            self.cancelled = True
            self.progress.close()

        self.progress.canceled.connect(handle_cancel)

    def __iter__(self):
        for i, item in enumerate(self.iterable):
            self.progress.setValue(i)
            QApplication.processEvents()  # Allow GUI to update
            yield item
        self.progress.close()

    def __len__(self):
        return self.total


# Example Usage
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    for i in ProgressDialog(range(100), "Processing Items"):
        time.sleep(0.05)  # Simulate work
