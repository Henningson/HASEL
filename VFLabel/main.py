# We can start the program in this file.
import sys
import gui
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
w = gui.StartWindowView()
sys.exit(app.exec_())
