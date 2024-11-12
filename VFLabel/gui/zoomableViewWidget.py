from PyQt5.QtGui import QTransform
from PyQt5.QtWidgets import QGraphicsView, QMenu


class ZoomableViewWidget(QGraphicsView):
    """
    A QGraphicsView widget that allows zooming in and out with the mouse wheel.

    :param parent: The parent widget for the ZoomableViewWidget instance.
    :type parent: QWidget, optional

    Attributes:
        _zoom (float): The current zoom level of the view.

    Methods:
        wheelEvent(event):
            Handles mouse wheel events to zoom in or out based on scroll direction.

        contextMenuEvent(event):
            Opens a context menu with options for zooming in and out.

        zoomIn():
            Increases the zoom level by a factor of zoom_speed.

        zoomOut():
            Decreases the zoom level by a factor of zoom_speed.

        zoomReset():
            Resets the zoom level to 1.

        zoom() -> float:
            Returns the current zoom level.

        updateView():
            Updates the view transformation based on the current zoom level.
    """

    def __init__(self, parent=None):
        """
        Initializes the ZoomableViewWidget with an optional parent.

        :param parent: The parent widget for the ZoomableViewWidget instance.
        :type parent: QWidget, optional
        """
        super(ZoomableViewWidget, self).__init__(parent)
        self._zoom: float = 1.0
        self._zoom_speed: float = 1.1

    def wheelEvent(self, event) -> None:
        """
        Handles mouse wheel events to adjust the zoom level.

        :param event: The QWheelEvent containing information about the mouse wheel event.
        :type event: QWheelEvent
        """
        mouse = event.angleDelta().y() / 120

        if mouse > 0:
            self.zoomIn()
        else:
            self.zoomOut()

    def contextMenuEvent(self, event) -> None:
        """
        Opens a context menu with options for zooming in and out.

        :param event: The QContextMenuEvent containing information about the context menu event.
        :type event: QContextMenuEvent
        """
        menu = QMenu()
        menu.addAction("Zoom in               MouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out              MouseWheel Down", self.zoomOut)
        menu.exec_(event.globalPos())

    def zoomIn(self) -> None:
        """
        Increases the zoom level by a factor of self._zoom_speed.
        """
        self._zoom *= self._zoom_speed
        self.updateView()

    def zoomOut(self) -> None:
        """
        Decreases the zoom level by a factor of self._zoom_speed.
        """
        self._zoom /= self._zoom_speed
        self.updateView()

    def zoomReset(self) -> None:
        """
        Resets the zoom level to 1.
        """
        self._zoom = 1
        self.updateView()

    def zoom(self) -> float:
        """
        Returns the current zoom level.

        :return: The current zoom level.
        :rtype: float
        """
        return self._zoom

    def zoom_speed(self) -> float:
        """
        Returns the current zoom speed.

        :return: The current zoom level.
        :rtype: float
        """
        return self._zoom_speed

    def set_zoom_speed(self, zoom_speed: float) -> None:
        """
        Set the zoom speed.
        """
        self._zoom_speed = zoom_speed

    def updateView(self) -> None:
        """
        Updates the view transformation based on the current zoom level.
        """
        self.setTransform(QTransform().scale(self.zoom, self.zoom))


if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QImage, QPixmap
    from PyQt5.QtWidgets import (
        QApplication,
        QGraphicsScene,
        QGraphicsView,
        QGraphicsPixmapItem,
        QMainWindow,
        QVBoxLayout,
        QWidget,
    )
    from PyQt5.QtWidgets import QGraphicsView, QMenu
    from PyQt5.QtGui import QTransform

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Zoomable Image View")

            # Create a central widget and a layout
            central_widget = QWidget(self)
            layout = QVBoxLayout(central_widget)

            # Set up the zoomable view
            self.view = ZoomableViewWidget(self)
            layout.addWidget(self.view)

            # Set up the scene for the view
            self.scene = QGraphicsScene(self)
            self.view.setScene(self.scene)

            # Load an image to display in the view
            self.image = QImage("path_to_your_image.jpg")
            pixmap = QPixmap(self.image)
            pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(pixmap_item)

            # Set up the main window
            self.setCentralWidget(central_widget)
            self.setGeometry(100, 100, 800, 600)

            # Show the window
            self.show()

    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()

    # Run the application
    sys.exit(app.exec_())
