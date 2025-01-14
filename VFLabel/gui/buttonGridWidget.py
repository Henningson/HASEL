from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton
from PyQt5.QtCore import QSize, pyqtSignal

from VFLabel.utils.enums import GRID_BUTTON_MODE


class ButtonGrid(QWidget):
    buttonSignal = pyqtSignal(int, int)

    def __init__(self, grid_height: int = 18, grid_width: int = 18, parent=None):
        super(ButtonGrid, self).__init__()

        button_size: int = 25

        self.setLayout(QGridLayout())
        self.setFixedSize(QSize(button_size * grid_width, button_size * grid_height))
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.buttons = []

        for y in range(grid_height + 1):
            y_range = []
            for x in range(grid_width + 1):
                if y == grid_height:
                    if x == grid_width:
                        continue
                    label = QPushButton(str(x))
                    label.setContentsMargins(0, 0, 0, 0)
                    label.setFixedSize(QSize(button_size, button_size))
                    self.layout().addWidget(label, y, x, 1, 1)
                    continue
                if x == grid_width:
                    label = QPushButton(str(y))
                    label.setContentsMargins(0, 0, 0, 0)
                    label.setFixedSize(QSize(button_size, button_size))
                    self.layout().addWidget(label, y, x, 1, 1)
                    continue

                button = GridButton(x, y, button_size=button_size)
                button.id_signal.connect(self.clicked_button)
                self.layout().addWidget(button, y, x, 1, 1)
                y_range.append(button)

            if len(y_range) == 0:
                continue

            self.buttons.append(y_range)

        # Only one button can be highlighted at a time.
        self.highlighted_button_id = None

    @QtCore.pyqtSlot(int, int)
    def clicked_button(self, x, y):
        self.buttonSignal.emit(x, y)

        if not self.highlighted_button_id:
            self.highlighted_button_id = [x, y]

        if x == self.highlighted_button_id[0] and y == self.highlighted_button_id[1]:
            return

        if (
            self.getButton(
                self.highlighted_button_id[0], self.highlighted_button_id[1]
            ).mode
            == GRID_BUTTON_MODE.HIGHLIGHTED
        ):
            self.reset_button(
                self.highlighted_button_id[0], self.highlighted_button_id[1]
            )
        self.highlighted_button_id = [x, y]

    def activate_highlighted(self):
        self.getButton(
            self.highlighted_button_id[0], self.highlighted_button_id[1]
        ).setActivated()

    def getButton(self, x, y):
        return self.buttons[y][x]

    def reset_all(self):
        for row in self.buttons:
            for button in row:
                button.reset()

    @QtCore.pyqtSlot(int, int)
    def reset_button(self, x, y):
        self.buttons[y][x].reset()


class GridButton(QPushButton):
    id_signal = pyqtSignal(int, int)

    def __init__(self, x: int, y: int, button_size: int = 25, parent=None):
        super(GridButton, self).__init__("")
        self.x = x
        self.y = y
        self.clicked.connect(self.on_clicked)

        self.mode = GRID_BUTTON_MODE.UNSET

        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedSize(QSize(button_size, button_size))
        self.setStyleSheet("border: 1px solid #333333;")

    def setActivated(self):
        self.setStyleSheet("background-color : #33FF33")
        self.mode = GRID_BUTTON_MODE.SET

    def on_clicked(self, bool):
        if self.mode == GRID_BUTTON_MODE.SET:
            return

        self.id_signal.emit(self.x, self.y)
        self.setStyleSheet("background-color : #DD3333")
        self.mode = GRID_BUTTON_MODE.HIGHLIGHTED

    def reset(self):
        self.setStyleSheet("border: 1px solid #333333;")
        self.mode = GRID_BUTTON_MODE.UNSET
