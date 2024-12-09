from PyQt5.QtWidgets import (
    QSlider,
    QApplication,
    QPushButton,
    QHBoxLayout,
    QWidget,
    QVBoxLayout,
    QLabel,
    QStyle,
    QStyleOptionSlider,
)
from PyQt5.QtGui import QPainter, QFont, QFontMetrics
from PyQt5.QtCore import Qt
from time import sleep
import numpy as np
import PyQt5.QtCore as QtCore


class VocalfoldSegmentationSliderWidget(QSlider):

    signal_btn_pressed_position = QtCore.pyqtSignal(int)
    signal_begin_segment = QtCore.pyqtSignal(int)
    signal_end_segment = QtCore.pyqtSignal(int)

    def __init__(self, number_images):
        super().__init__()
        self.changed = True

        self.number_images = number_images - 1
        self.marks = np.array([0, number_images - 1])
        self.init_slider()

    def init_slider(self):
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setMaximum(self.number_images)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.groove_width_margin = 35
        self.setStyleSheet(
            f"""
            QSlider::handle:horizontal {{
                background: rgb(0, 0, 255);
                width: 0px;  /* Breite des Handles */
                height: 0px; /* Höhe des Handles */

            }}
            QSlider::groove:horizontal {{
                background: rgb(255, 255, 255);
                height: 40px;  /* Höhe der Slider-Linie */
                border: 1px solid #999;
                margin-right: {self.groove_width_margin}px;
            }}
        """
        )

    def set_slider_new_mark(self, position):
        self.setValue(position)
        self.get_absolute_position(position)

    def get_absolute_position(self, position: int) -> int:
        absolute_position = int(
            (position - self.minimum())
            / (self.maximum() - self.minimum())
            * (self.width() - self.groove_width_margin)
        )
        return absolute_position

    def paintEvent(self, event):
        super().paintEvent(event)
        self.paint_marks(self.marks)

    def clearlayout(self, layout):
        for i in reversed(range(layout.count())):
            layout.removeWidget(layout.itemAt(i).widget())

    def paint_marks(self, marks: np.array):
        # long line shaped btns
        for i in range(len(marks) - 1):
            position = marks[i]
            x = int(self.get_absolute_position(position))
            self.layout.itemAt(i).widget().move(x, int(np.ceil(self.height() / 2)) - 7)

        # btns marking the frame
        for i in range(len(marks)):
            position = marks[i]
            x = int(self.get_absolute_position(position))
            self.layout.itemAt(i + len(marks) - 1).widget().move(
                x, int(np.ceil(self.height() / 2)) - 8
            )

    def create_btns(self, marks: np.array):
        colors = np.array(["lightblue", "lightgreen"])

        # long line shaped btns
        for i in range(len(marks) - 1):
            font = QFont()
            font.setPointSize(14)
            metrics = QFontMetrics(font)

            text_height = metrics.height()

            x = int(self.get_absolute_position(marks[i]))
            p = int(self.get_absolute_position(marks[i + 1]))
            line_btn = QPushButton(self)
            line_btn.clicked.connect(self.line_btn_clicked)
            line_btn.setStyleSheet(f"background-color : {colors[i%2]}")

            line_btn.setFixedSize(p - x + 5, int(text_height * 0.4))
            line_btn.move(x, 0)
            self.layout.addWidget(line_btn)

        # btns marking the frame
        for i in marks:
            font = QFont()
            font.setPointSize(14)
            metrics = QFontMetrics(font)

            text = f"{i}"
            text_width = metrics.horizontalAdvance(text)
            text_height = metrics.height()

            x = int(self.get_absolute_position(i))
            button = QPushButton(text, self)
            button.clicked.connect(self.number_btn_clicked)
            button.setToolTip(f"{i}")
            button.raise_()
            button.move(x, 0)
            button.setFixedSize(text_width, int(text_height * 0.6))
            self.layout.addWidget(button)

    def line_btn_clicked(self):
        sender = self.sender()
        slider_value = self.get_relative_position(int(sender.pos().x()) + 5)
        arg_min_smaller = np.argmin(
            np.where(slider_value - self.marks > 0, slider_value - self.marks, 10000)
        )
        arg_min_bigger = np.argmin(
            np.where(self.marks - slider_value > 0, self.marks - slider_value, 10000)
        )
        self.signal_begin_segment.emit(self.marks[arg_min_smaller])
        self.signal_end_segment.emit(self.marks[arg_min_bigger])
        print(self.marks[arg_min_smaller], self.marks[arg_min_bigger])

    def number_btn_clicked(self):
        sender = self.sender()
        relative_position = self.get_relative_position(sender.pos().x())
        arg_min_smaller = np.argmin(np.abs(relative_position - self.marks))
        self.signal_btn_pressed_position.emit(self.marks[arg_min_smaller])

    def get_relative_position(self, absolute_position):
        position = (absolute_position) * (
            (self.maximum() - self.minimum())
            / (self.width() - self.groove_width_margin)
        )
        +self.minimum()
        return position

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.clearlayout(self.layout)
        self.create_btns(self.marks)

    def update_new_mark_signal(self, number) -> None:
        self.marks = np.concatenate([self.marks, np.array([number])])
        self.marks = np.sort(self.marks)
        self.marks = np.unique(self.marks)
        self.clearlayout(self.layout)
        self.create_btns(self.marks)
        print(self.marks)

    def update_remove_mark_signal(self, number) -> None:
        arg_number = np.argwhere(self.marks == number)
        if arg_number is not None:
            if arg_number != 0 and arg_number != len(self.marks) - 1:
                self.marks = np.delete(self.marks, arg_number)
        self.clearlayout(self.layout)
        self.create_btns(self.marks)
