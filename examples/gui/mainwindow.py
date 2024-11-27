import sys
import VFLabel.gui as gui
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
w = gui.MainWindow()
sys.exit(app.exec_())
