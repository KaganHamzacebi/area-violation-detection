import os
import threading
import time

import cv2
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtCore import QRect, QSize, Qt, pyqtSlot, QPoint
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QFileDialog

from ResizeableRubberBand import ResizableRubberBand
from VideoThread import VideoThread


def doesCollide(rect1, rect2):
    return rect1[0] < rect2[0] + rect2[2] and \
           rect1[0] + rect1[2] > rect2[0] and \
           rect1[1] < rect2[1] + rect2[3] and \
           rect1[3] + rect1[1] > rect2[1]


class Gui(QWidget):
    def __init__(self):
        super().__init__()
        self.videoThread = None
        self.cb = ()
        self.origin = 0
        self.isVideoRunning = False
        self.band = None
        self.bandDrawn = False
        self.isBandBigEnough = False
        self.objectType = "Dog"
        self.collisionDetectThread = threading.Thread(target=self.controlThread)

        self.boxLabels = None
        self.boxes = None

        # Props for drawing
        self.setGeometry(30, 30, 600, 400)
        self.begin = QPoint()
        self.end = QPoint()
        self.show()

        # Props for Window
        self.setWindowTitle("Area Violation Detection by YOLO")
        self.display_width = 1280
        self.display_height = 720
        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.setScaledContents(1)
        self.image_label.setFixedSize(self.display_width, self.display_height)
        self.image_label.setStyleSheet("background-color: lightgray")

        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        hbox = QHBoxLayout()
        vbox.addLayout(hbox)
        # set the vbox layout as the widgets layout
        self.setLayout(vbox)

        # Browse Video Button
        browseVideoBtn = QPushButton("Select a video")
        browseVideoBtn.clicked.connect(self.selectVideoListener)
        hbox.addWidget(browseVideoBtn)

        # ComboBox for item type selection
        self.comboObjBtn = QComboBox(self)
        self.comboObjBtn.addItems(
            ["Dog", "Cat", "Person", "Car", "Truck", "Motorbike", "Bird", "Traffic Light", "Suitcase"])
        self.comboObjBtn.setToolTip("Object to detect")
        self.comboObjBtn.currentIndexChanged.connect(self.objectChangeListener)
        hbox.addWidget(self.comboObjBtn)

        # Continue Video Button
        self.resumeVideoBtn = QPushButton("Resume Video")
        self.resumeVideoBtn.clicked.connect(self.resumeVideoListener)
        self.resumeVideoBtn.setEnabled(False)

        self.pauseVideoBtn = QPushButton("Pause Video")
        self.pauseVideoBtn.setEnabled(False)
        self.pauseVideoBtn.clicked.connect(self.pauseVideoListener)

        hbox.addWidget(self.resumeVideoBtn)
        hbox.addWidget(self.pauseVideoBtn)

    def objectChangeListener(self):
        self.objectType = self.comboObjBtn.currentText()

    def mousePressEvent(self, event):
        if not self.band:
            self.origin = event.pos()
            self.band = ResizableRubberBand(self.image_label)
            self.band.setGeometry(QRect(self.origin, QSize()))
            self.collisionDetectThread.start()

    def mouseMoveEvent(self, event):
        if self.band and not self.bandDrawn:
            diff = self.origin - event.pos()
            if diff.manhattanLength() > 20:
                self.band.setGeometry(QRect(self.origin, event.pos()).normalized())
                self.isBandBigEnough = True

    def mouseReleaseEvent(self, event):
        self.bandDrawn = True
        if not self.isBandBigEnough and self.band is not None:
            self.origin = self.origin + QPoint(100, 100)
            self.band.setGeometry(QRect(self.origin, event.pos()).normalized())
            self.isBandBigEnough = True

    def selectVideoListener(self):
        filename, _ = QFileDialog.getOpenFileName(None, "Select a video",
                                                  os.getcwd(),
                                                  "Video Files (*.mp4)")

        if filename != '':
            # create the video capture thread
            self.videoThread = VideoThread(self.setCB, filename)
            self.end = False
            # set buttons
            self.resumeVideoBtn.setEnabled(True)
            self.pauseVideoBtn.setEnabled(False)
            # connect its signal to the update_image slot
            self.videoThread.change_pixmap_signal.connect(self.update_image)
            # start the thread
            self.videoThread.start()

    def resumeVideoListener(self):
        self.videoThread.start()
        self.resumeVideoBtn.setEnabled(False)
        self.pauseVideoBtn.setEnabled(True)

    def pauseVideoListener(self):
        self.videoThread.pause()
        self.resumeVideoBtn.setEnabled(True)
        self.pauseVideoBtn.setEnabled(False)

    def setCB(self, labels, boxes):
        self.boxLabels = labels
        self.boxes = boxes

    def controlThread(self):
        while True:
            try:
                if self.band is not None and self.boxes is not None and self.boxLabels is not None:
                    bandCoordinates = self.band.getRectCoordinates()
                    anyCollide = False
                    for i, box in enumerate(self.boxes):
                        if self.boxLabels[i] == self.objectType.lower():
                            if doesCollide(box, bandCoordinates):
                                anyCollide = True

                    if anyCollide:
                        self.band.setRubberColor(QtCore.Qt.green)
                    else:
                        self.band.setRubberColor(QtCore.Qt.red)
                else:
                    time.sleep(1)
            finally:
                time.sleep(0.5)

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
