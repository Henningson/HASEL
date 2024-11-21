import os
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSignal


class NewProjectWidget(QDialog):

    # state of window signal
    new_project_status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_window()

    def init_window(self):
        # Basic setup
        self.setGeometry(300, 300, 500, 100)
        self.setWindowTitle("New project")

        layout = QFormLayout()

        # create input areas
        self.name_input = QLineEdit()
        self.gridx_input = QLineEdit()
        self.gridy_input = QLineEdit()

        # add input areas to layout
        layout.addRow("Project Name: ", self.name_input)
        layout.addRow("Grid x: ", self.gridx_input)
        layout.addRow("Grid y: ", self.gridy_input)

        # create buttons
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("CANCEL")

        # add buttons to layout
        layout.addWidget(self.ok_button)
        layout.addWidget(self.cancel_button)

        # add functionality to buttons
        self.ok_button.clicked.connect(self.pass_status)
        self.cancel_button.clicked.connect(self.pass_status)

        self.setLayout(layout)
        self.show()

    def get_new_project_inputs(self):
        return self.name_input.text(), self.gridx_input.text(), self.gridy_input.text()

    def get_video_input(self):
        return self.video_path

    def pass_status(self):
        """sends signal about this window status to MainWindow

        Return:
            None
        """
        sender = self.sender()
        if sender == self.ok_button:
            self.new_project_status_signal.emit("OK")
        elif sender == self.cancel_button:
            self.new_project_status_signal.emit("CANCEL")
        else:
            pass
        self.close()

    def closeEvent(self, event):
        if event.spontaneous():
            # window closed by predefined button in the top right corner
            self.new_project_status_signal.emit("CANCEL")
        event.accept()
