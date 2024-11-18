import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QSlider,
    QPushButton,
    QLabel,
)
from PyQt5.QtCore import Qt, QTimer


class TimerSliderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timer Slider Example")
        self.resize(400, 200)

        # Initialize the slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(0)

        # Label to show slider value
        self.label = QLabel("Value: 0")
        self.label.setAlignment(Qt.AlignCenter)

        # Buttons to start and stop the timer
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_slider)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.slider)
        layout.addWidget(self.label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)

        # Button actions
        self.start_button.clicked.connect(self.start_timer)
        self.stop_button.clicked.connect(self.stop_timer)

    def start_timer(self):
        # Start the timer with a 100 ms interval
        self.timer.start(100)

    def stop_timer(self):
        # Stop the timer
        self.timer.stop()

    def update_slider(self):
        # Update slider value
        current_value = self.slider.value()
        if current_value < self.slider.maximum():
            self.slider.setValue(current_value + 1)
            self.label.setText(f"Value: {current_value + 1}")
        else:
            self.timer.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimerSliderApp()
    window.show()
    sys.exit(app.exec_())
