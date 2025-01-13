from enum import Enum
from dataclasses import dataclass
import numpy as np


class PointLabel(Enum):
    UNLABELED = -1
    LASERPOINT = 0
    SPECULARITY = 1
    OTHER = 2


@dataclass
class SpecularHightlightDatum:
    """Class for saving Specular Highlight Data"""

    image: np.array
    image_id: int
    label: PointLabel


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
    TRAIN = 0
    EVAL = 1
    TEST = 2


class GRID_BUTTON_MODE(Enum):
    UNSET = 0
    HIGHLIGHTED = 1
    SET = 2
