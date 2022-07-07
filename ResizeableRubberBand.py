from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizeGrip, QRubberBand


class ResizableRubberBand(QWidget):
    def __init__(self, parent=None):
        super(ResizableRubberBand, self).__init__(parent)

        self.draggable = True
        self.isDragging = True
        self.dragging_threshold = 5
        self.mousePressPos = None
        self.mouseMovePos = None
        self.borderRadius = 5

        self.setWindowFlags(QtCore.Qt.SubWindow)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            QSizeGrip(self), 0,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        layout.addWidget(
            QSizeGrip(self), 0,
            QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self._band = QRubberBand(
            QRubberBand.Rectangle, self)

        # Rubberband Styles
        self.setRubberColor(QtCore.Qt.red)

        self._band.show()
        self.show()

    def getRectCoordinates(self):
        return [self.geometry().x(),
                self.geometry().y(),
                self.geometry().width(),
                self.geometry().height()]

    def setRubberColor(self, rubberColor):
        pal = QtGui.QPalette()
        pal.setBrush(QtGui.QPalette.Highlight, QtGui.QBrush(rubberColor))
        self._band.setPalette(pal)

    def resizeEvent(self, event):
        self._band.resize(self.size())

    def paintEvent(self, event):
        # Get current window size
        window_size = self.size()
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        qp.drawRoundedRect(0, 0, window_size.width(), window_size.height(),
                           self.borderRadius, self.borderRadius)
        qp.end()

    def mousePressEvent(self, event):
        if self.draggable and event.button() == QtCore.Qt.RightButton:
            self.mousePressPos = event.pos()
        super(ResizableRubberBand, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.draggable and event.buttons() & QtCore.Qt.RightButton:
            diff = event.pos() - self.mousePressPos
            if not self.isDragging:
                if diff.manhattanLength() > self.dragging_threshold:
                    self.isDragging = True
            if self.isDragging:
                geo = self.geometry()
                parentRect = self.parent().rect()
                geo.translate(diff)
                if not parentRect.contains(geo):
                    if geo.right() > parentRect.right():
                        geo.moveRight(parentRect.right())
                    elif geo.x() < parentRect.x():
                        geo.moveLeft(parentRect.x())
                    if geo.bottom() > parentRect.bottom():
                        geo.moveBottom(parentRect.bottom())
                    elif geo.y() < parentRect.y():
                        geo.moveTop(parentRect.y())
                self.move(geo.topLeft())
                self.clearMask()
        super(ResizableRubberBand, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.mousePressPos is not None:
            if event.button() == QtCore.Qt.RightButton and self.isDragging:
                event.ignore()
                self.isDragging = False
            self.mousePressPos = None
        super(ResizableRubberBand, self).mouseReleaseEvent(event)
