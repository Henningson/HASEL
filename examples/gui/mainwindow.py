import sys
import VFLabel.gui_base as gui_base
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
w = gui_base.MainWindow()
sys.exit(app.exec_())
