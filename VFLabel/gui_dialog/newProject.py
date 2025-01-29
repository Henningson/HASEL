from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton


class NewProjectDialog(QDialog):

    def __init__(self, video_name):
        super().__init__()
        self.init_window(video_name)

    def init_window(self, video_name):
        # TODO: incorporate video name as proposed project name
        # TODO: Abfangen wenn Name schon existiert
        # Basic setup
        self.setGeometry(300, 300, 500, 100)
        self.setWindowTitle("New project")

        layout = QFormLayout()

        # create input areas
        self.name_input = QLineEdit()
        self.name_input.setText(video_name)
        self.gridx_input = QLineEdit()
        # self.gridx_input.setInputMask("9999")
        self.gridy_input = QLineEdit()

        # add input areas to layout
        layout.addRow("Project folder name: ", self.name_input)
        layout.addRow("LaserGrid width: ", self.gridx_input)
        layout.addRow("LaserGrid height: ", self.gridy_input)
        # TODO: allow only integers, Pflicht, dass Felder gefüllt werden müssen
        # TODO: descriptions?

        # create buttons
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("CANCEL")

        # add buttons to layout
        layout.addWidget(self.ok_button)
        layout.addWidget(self.cancel_button)

        # add functionality to buttons
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.setLayout(layout)
        self.show()

    def get_new_project_inputs(self):
        return self.name_input.text(), self.gridx_input.text(), self.gridy_input.text()

    def get_video_input(self):
        return self.video_path

    def closeEvent(self, event):
        if event.spontaneous():
            # window closed by predefined button in the top right corner
            self.reject()
