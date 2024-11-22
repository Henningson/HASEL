from PyQt5.QtWidgets import QGraphicsEllipseItem
from typing import List


class GraphicEllipseItemWithID(QGraphicsEllipseItem):
    def __init__(
        self, x_pos, y_pos, width, height, pen, brush, x_id, y_id, parent=None
    ):
        super().__init__(x_pos, y_pos, width, height, parent)
        self.setBrush(brush)
        self.setPen(pen)
        self.x_id = x_id
        self.y_id = y_id

    def getID(self) -> List[int]:
        return self.x_id, self.y_id
