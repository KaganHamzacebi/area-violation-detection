import sys
from PyQt5.QtWidgets import QApplication
from gui import Gui

if __name__ == "__main__":
    app = QApplication(sys.argv)
    yoloGUI = Gui()
    yoloGUI.setFixedSize(1304, 771)
    yoloGUI.move(300, 100)
    yoloGUI.show()
    sys.exit(app.exec_())
