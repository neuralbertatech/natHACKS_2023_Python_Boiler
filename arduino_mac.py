"""
This is the oddball task
- it displays either a blue or green circle and records when user hits space
it pumps data about what happens when to an lsl stream
it also receive eeg data from a muse, or simulates it
This data is recorder along with events
EVENT KEY:
0 - Begin trial
1 - normal color displayed (blue)
2 - oddball color displayed (green)
3 - user pressed space
11 - end trial
It contains partially complete code to graph ERP afterwards.
The data is stored with tines normalized (timestamp 0 when stim first displayed, for each trial)
so setting up an ERP graph should be reasonably simple
Project ideas: any project where the user sees something displayed and interacts with it, while eeg is recorded
"""

import sys

from PyQt6 import QtGui
from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QGridLayout
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import QApplication

class ArduinoMacos(QWidget):
    def __init__(self, parent=None, arduino_port=None):
        super().__init__(parent)

        self.arduino_port = arduino_port
        self.width = 600
        self.height = 600
        self.logo = "../utils/logo_icon.jpg"
        self.title = "Arduino Testing Window"

        # Configure the window
        self.setMinimumSize(self.width, self.height)
        self.setWindowIcon(QtGui.QIcon(self.logo))
        self.setWindowTitle(self.title)

        # init layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(100, 100, 100, 100)
        self.label = QLabel()
        self.label.setFont(QtGui.QFont("Arial", 14))
        self.label.setText(
            "This is a placeholder window to test the arduino function and turn it on and off"
        )
        self.layout.addWidget(self.label)
        self.info = QLabel()
        self.info.setFont(QtGui.QFont("Arial", 14))
        self.info.setText(
            "The following serial port has been selected: " + str(self.arduino_port)
        )
        self.layout.addWidget(self.info)

        # set up a button to activate / deactivate the arduino
        self.arduino_button = QPushButton("Activate Arduino")
        self.arduino_button.setEnabled(True)
        self.layout.addWidget(self.arduino_button, 4, 0, 1, -1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.arduino_button.clicked.connect(self.activate_arduino)

        # This values was randomly generated - it must match between the Central and Peripheral devices
        # Any changes you make here must be suitably made in the Arduino program as well
        self.TDCS_UUID = "00001101-0000-1000-8000-00805f9b34fb"

        self.on_value = bytearray([0x01])
        self.off_value = bytearray([0x00])

        self.TDCS = False

    def activate_arduino(self):
        if self.arduino_button.text() == "Activate Arduino":
            self.arduino_button.setText("Deactivate Arduino")
        else:
            self.arduino_button.setText("Activate Arduino")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ArduinoMacos()
    win.show()
    sys.exit(app.exec())
