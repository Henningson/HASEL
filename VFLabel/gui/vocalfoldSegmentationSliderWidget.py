import numpy as np
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QSlider


class VocalfoldSegmentationSliderWidget(QSlider):

    signal_btn_pressed_position = QtCore.pyqtSignal(int)
    signal_begin_segment = QtCore.pyqtSignal(int)
    signal_end_segment = QtCore.pyqtSignal(int)
    signal_marks = QtCore.pyqtSignal(object)

    def __init__(self, number_images, marks=None):
        super().__init__()

        # initialize marks (limit boundaries for interpolation)
        if marks is None:
            self.marks = np.array([0, number_images - 1])
        else:
            self.marks = marks

        self.signal_marks.emit(self.marks)

        self.init_slider(number_images - 1)

    def init_slider(self, number_images):

        # initialize slider layout
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setMaximum(number_images)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.groove_width_margin = 35

    def set_marks(self, marks):
        self.marks = marks
        self.signal_marks.emit(self.marks)

    def get_absolute_position(self, relative_position: int) -> int:
        absolute_position_x = int(
            (relative_position - self.minimum())
            / (self.maximum() - self.minimum())
            * (self.width() - self.groove_width_margin)
        )
        return absolute_position_x

    def get_relative_position(self, absolute_position_x):
        # corresponds to slider value
        relative_position = (absolute_position_x) * (
            (self.maximum() - self.minimum())
            / (self.width() - self.groove_width_margin)
        )
        +self.minimum()
        return relative_position

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.clearlayout(self.layout)
        self.create_btns(self.marks)

    def paintEvent(self, event):
        super().paintEvent(event)
        self.paint_marks(self.marks)

    def paint_marks(self, marks: np.array):
        # adjust position of btns connecting the marks (long line shaped buttons)
        for index in range(len(marks) - 1):
            relative_position = marks[index]
            absolute_position = int(self.get_absolute_position(relative_position))
            self.layout.itemAt(index).widget().move(
                absolute_position, int(np.ceil(self.height() / 2)) - 7
            )

        # adjust position of mark btns (small btns with frame number)
        for index in range(len(marks)):
            relative_position = marks[index]
            absolute_position = int(self.get_absolute_position(relative_position))
            self.layout.itemAt(index + len(marks) - 1).widget().move(
                absolute_position, int(np.ceil(self.height() / 2)) - 8
            )

    def clearlayout(self, layout):
        # remove all buttons
        for i in reversed(range(layout.count())):
            layout.removeWidget(layout.itemAt(i).widget())

    def create_btns(self, marks: np.array):
        # long line shaped btns alternate in these two colors
        colors = np.array(["lightblue", "lightgreen"])

        # create btns connecting the marks (long line shaped buttons)
        for i in range(len(marks) - 1):
            # get information for height of button
            font = QFont()
            font.setPointSize(14)
            metrics = QFontMetrics(font)
            text_height = metrics.height()

            # get information for width of button
            absolute_position_x_previous = int(self.get_absolute_position(marks[i]))
            absolute_position_x_next = int(self.get_absolute_position(marks[i + 1]))

            # create button, move to right position and set layout and functionality
            line_btn = QPushButton(self)
            line_btn.clicked.connect(self.line_btn_clicked)
            line_btn.setStyleSheet(f"background-color : {colors[i%2]}")
            line_btn.setFixedSize(
                absolute_position_x_next - absolute_position_x_previous + 5,
                int(text_height * 0.4),
            )
            line_btn.move(absolute_position_x_previous, 0)
            self.layout.addWidget(line_btn)

        # create mark btns (for the interpolation limit boundaries) (small btns with frame number)
        for i in marks:
            # get information for width and height of button
            font = QFont()
            font.setPointSize(14)
            metrics = QFontMetrics(font)

            text = f"{i}"
            text_width = metrics.horizontalAdvance(text)
            text_height = metrics.height()

            # create btn, add functionality and set layout
            button = QPushButton(text, self)
            button.clicked.connect(self.number_btn_clicked)
            button.setToolTip(f"{i}")
            button.setFixedSize(text_width, int(text_height * 0.6))
            button.raise_()

            # position the button
            absolute_position_x = int(self.get_absolute_position(i))
            button.move(absolute_position_x, 0)

            self.layout.addWidget(button)

    def line_btn_clicked(self):
        sender = self.sender()
        relative_position = self.get_relative_position(int(sender.pos().x()) + 5)

        # get upper and lower boundary for segment of current frame
        arg_min_lower = np.argmin(
            np.where(
                relative_position - self.marks > 0,
                relative_position - self.marks,
                10000,
            )
        )
        arg_min_upper = np.argmin(
            np.where(
                self.marks - relative_position > 0,
                self.marks - relative_position,
                10000,
            )
        )

        # emit upper and lower boundary for segment of current frame
        self.signal_begin_segment.emit(self.marks[arg_min_lower])
        self.signal_end_segment.emit(self.marks[arg_min_upper])

    def number_btn_clicked(self):
        sender = self.sender()
        # find mark btn that is clicked
        relative_position = self.get_relative_position(sender.pos().x())
        arg_clicked_mark = np.argmin(np.abs(relative_position - self.marks))

        # emit number of clicked mark button
        self.signal_btn_pressed_position.emit(self.marks[arg_clicked_mark])

    def update_new_mark_signal(self, number) -> None:
        # new mark is added

        # add mark to array
        self.marks = np.concatenate([self.marks, np.array([number])])
        self.marks = np.sort(self.marks)
        self.marks = np.unique(self.marks)

        # redo layout with new constellation of buttons
        self.clearlayout(self.layout)
        self.create_btns(self.marks)

        # emit new mark array
        self.signal_marks.emit(self.marks)

    def update_remove_mark_signal(self, number) -> None:
        # mark is removed

        # remove mark if it is at the removing position
        arg_number = np.argwhere(self.marks == number)
        if arg_number is not None:
            # first and last mark can not be removed
            if arg_number != 0 and arg_number != len(self.marks) - 1:
                self.marks = np.delete(self.marks, arg_number)

        # redo layout with new constellation of buttons
        self.clearlayout(self.layout)
        self.create_btns(self.marks)

        # emit new mark array
        self.signal_marks.emit(self.marks)
