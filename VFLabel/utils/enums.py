from enum import Enum


class Specularity(Enum):
    """For classification if a point is visible or not"""

    UNIDENTIFIABLE = 0
    SPECULARITY = 1
    VISIBLE = 2


class FullSegmentation(Enum):
    BACKGROUND = 0
    GLOTTIS = 1
    VOCALFOLD = 2
    LASERPOINT = 3


class LaserpointSegmentation(Enum):
    BACKGROUND = 0
    LASERPOINT = 1


class GlottisSegmentation(Enum):
    BACKGROUND = 0
    GLOTTIS = 1


class VocalfoldSegmentation(Enum):
    BACKGROUND = 0
    VOCALFOLD = 1


class DRAW_MODE(Enum):
    OFF = 0
    ON = 1


class REMOVE_MODE(Enum):
    OFF = 0
    ON = 1


class NN_MODE(Enum):
    EVAL = 0
    TRAIN = 1
