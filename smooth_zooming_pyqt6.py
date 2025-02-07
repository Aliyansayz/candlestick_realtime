### REFERENCE For Future Use


from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PyQt6.QtGui import QWheelEvent, QKeyEvent, QPainter
from PyQt6.QtCore import Qt, QRectF
import sys
import random


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Create a bar chart visualization
        self.bars = []
        for i in range(10):
            rect = self.scene.addRect(i * 30, 0, 20, random.randint(50, 200))
            self.bars.append(rect)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.zoom_factor = 1.15  # Zoom-in multiplier

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            factor = self.zoom_factor if event.angleDelta().y() > 0 else 1 / self.zoom_factor
            self.scale(factor, factor)

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Plus:
                self.scale(self.zoom_factor, self.zoom_factor)
            elif event.key() == Qt.Key.Key_Minus:
                self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = ZoomableGraphicsView()
    view.show()
    sys.exit(app.exec())
