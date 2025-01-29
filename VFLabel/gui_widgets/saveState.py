import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class SaveStateWidget(QWidget):

    save_state_signal = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__()

        self.init_window()

    def init_window(self):
        # definition of question text
        question_text = QLabel("Would you like to save your current state?")
        question_text.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # create finish and toBeContinued btns
        btn_save = QPushButton("Yes, please save it.", self)
        btn_save.setFixedSize(130, 40)
        btn_notSave = QPushButton("No, I already saved it.", self)
        btn_notSave.setFixedSize(130, 40)

        # add functionality to btns
        btn_save.clicked.connect(self.process_to_be_saved)
        btn_notSave.clicked.connect(self.process_not_to_be_saved)

        # define layout and insert all elements
        layout_v = QVBoxLayout()
        layout_h_btn = QHBoxLayout()
        layout_h_text = QHBoxLayout()

        layout_h_text.addStretch(1)
        layout_h_text.addWidget(question_text)
        layout_h_text.addStretch(1)

        layout_h_btn.addStretch(1)
        layout_h_btn.addWidget(btn_save)
        layout_h_btn.addStretch(1)
        layout_h_btn.addWidget(btn_notSave)
        layout_h_btn.addStretch(1)

        layout_v.addLayout(layout_h_text)
        layout_v.addStretch(1)
        layout_v.addLayout(layout_h_btn)
        layout_v.addStretch(1)

        self.setLayout(layout_v)

        # hide 'x' close button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        # general setup
        self.setWindowTitle("Update save state")
        self.show()

    def process_to_be_saved(self):
        # emit current progress
        self.save_state_signal.emit(True)
        self.deleteLater()

    def process_not_to_be_saved(self):
        # emit current progress
        self.save_state_signal.emit(False)
        self.deleteLater()


# app = QApplication(sys.argv)
# w = ProgressStateWidget()
# sys.exit(app.exec_())
