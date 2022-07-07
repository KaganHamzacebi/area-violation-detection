import sys

import cv2
import numpy as np
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import QWidget

from yolov3 import detect_objects, get_box_dimensions, load_yolo, draw_labels
# from yolov5 import detect_objects, load_yolo, post_process

is_cuda = len(sys.argv) > 1 and sys.argv[1] == "cuda"
# model, classes, output_layers = load_yolo(is_cuda)
model, classes, colors, output_layers = load_yolo(is_cuda)


def yoloDetection(frame, height, width):
    blob, outputs = detect_objects(frame, model, output_layers)
    boxes, confs, class_ids = get_box_dimensions(outputs, height, width)
    fil_labels = [classes[x] for i, x in enumerate(class_ids) if confs[i] > 0.75]
    fil_boxes = [boxes[i] for i in range(len(class_ids)) if confs[i] > 0.75]
    # draw_labels(boxes, confs, colors, class_ids, classes, frame)
    return fil_labels, fil_boxes


'''
def yoloDetection(frame, height, width):
    blob, outputs = detect_objects(frame, model)
    boxes, confs, class_ids = post_process(frame, outputs, classes)
    fil_labels = [classes[x] for i, x in enumerate(class_ids) if confs[i] > 0.75]
    fil_boxes = [boxes[i] for i in range(len(class_ids)) if confs[i] > 0.75]
    # draw_labels(boxes, confs, colors, class_ids, classes, frame)
    return fil_labels, fil_boxes
'''


class VideoThread(QWidget):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, setCB, videoCWD):
        super(QWidget, self).__init__()
        self.timer = None
        self.length = None
        self.frame_rate = None
        self.first = True
        self.end = False
        self.setCB = setCB
        # Video CFG
        self.videoCWD = videoCWD
        self.cap = cv2.VideoCapture(videoCWD)
        self.frame_rate = self.cap.get(cv2.CAP_PROP_FPS)
        self.length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.curFrame = 1

    def start(self):
        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.nextFrameSlot)
        self.timer.start(1000.0 / self.frame_rate)

    def nextFrameSlot(self):
        ret, frame = self.cap.read()
        height, width, channels = frame.shape
        self.yoloJobs(frame, height, width)
        self.change_pixmap_signal.emit(frame)

        if self.first:
            self.pause()
            self.first = False

        if self.curFrame == self.length:
            self.deleteLater()

        self.curFrame = self.curFrame + 1

    def yoloJobs(self, frame, height, width):
        fil_labels, fil_boxes = yoloDetection(frame, height, width)
        self.setCB(fil_labels, fil_boxes)

    def resume(self):
        self.timer.start()

    def pause(self):
        self.timer.stop()

    def deleteLater(self):
        self.cap.release()
        super(QWidget, self).deleteLater()
