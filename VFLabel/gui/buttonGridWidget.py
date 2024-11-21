from PyQt5 import QtCore
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton
from PyQt5.QtCore import QSize, pyqtSignal


class ButtonGrid(QWidget):
    buttonSignal = pyqtSignal(int, int)

    def __init__(self, grid_height: int = 18, grid_width: int = 18, parent=None):
        super(ButtonGrid, self).__init__()

        self.setLayout(QGridLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.buttons = []

        for y in range(grid_height):
            y_range = []
            for x in range(grid_width):
                button = GridButton(x, y)
                button.id_signal.connect(self.clicked_button)
                self.layout().addWidget(button, y, x, 1, 1)
                y_range.append(button)
            self.buttons.append(y_range)

    @QtCore.pyqtSlot(int, int)
    def clicked_button(self, x, y):
        self.buttonSignal.emit(x, y)

    def getButton(self, x, y):
        return self.buttons[x][y]

    def reset(self):
        for row in self.buttons:
            for button in row:
                button.reset()


class GridButton(QPushButton):
    id_signal = pyqtSignal(int, int)

    def __init__(self, x, y, parent=None):
        super(GridButton, self).__init__("")
        self.x = x
        self.y = y
        self.clicked.connect(self.on_clicked)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedSize(QSize(25, 25))
        self.setStyleSheet("border: 1px solid #333333;")

    def setActivated(self):
        self.setStyleSheet("background-color : #33DD33")

    def on_clicked(self, bool):
        self.setStyleSheet("background-color : #33DD33")
        self.id_signal.emit(self.x, self.y)

    def reset(self):
        self.setStyleSheet("border: 1px solid #333333;")
