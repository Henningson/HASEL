from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout



from PyQt5 import QtCore
import numpy as np


import utils.transforms
import gui.drawSegmentationWidget
import 

############################### ^
#         #         #         # |
#         #         #         # |
#  DRAW   #  MOVE   # INTERP  # | Vertical Layout
#  SEG    #  SEG    # VIDEO   # | Frames are Horizontal Layout
#         #         #         # |
#         #         #         # |
############################### |
# INTERP #  VIDPLAYERWIDG     # |
############################### v


class VocalfoldSegmentationView(QWidget):
    def __init__(self, video: np.array, parent=None):
        super(VocalfoldSegmentationView, self).__init__(parent)
        vertical_layout = QVBoxLayout()
        horizontal_layout = QHBoxLayout()

        self.video = video
        self.q_video = utils.transforms.vid_2_QImage(video)

        self.segmentation_drawer = 
