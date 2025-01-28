# We can start the program in this file.
import sys

import gui
import qdarktheme
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
qdarktheme.setup_theme()
w = gui.MainWindow()
sys.exit(app.exec_())
