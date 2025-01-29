import sys

import gui_base
import qdarktheme
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
qdarktheme.setup_theme()
w = gui_base.MainWindow()
sys.exit(app.exec_())
