from PyQt5.QtWidgets import QWidget


class BaseWindowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def close_window():
        print("close function in base view")
        pass

    def save_current_state(self):
        print("save function in base view")
        pass

    def help(self):
        print("help function in base view")
        pass
