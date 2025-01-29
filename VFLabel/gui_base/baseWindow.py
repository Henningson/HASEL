from PyQt5.QtWidgets import QWidget


class BaseWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def close_window():
        pass

    def save_current_state(self):
        pass

    def help(self):
        pass
