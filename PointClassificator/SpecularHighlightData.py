from dataclasses import dataclass
from enum import Enum
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
