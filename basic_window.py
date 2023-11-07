#!/usr/bin/env python
"""
This is a very basic PyQt6 window that demonstrates how to create a window with a file dialog
"""

import sys

from PyQt6.QtWidgets import QMainWindow, QGridLayout, QWidget, QVBoxLayout, QFileDialog, QApplication

import pyqtgraph as pg


class MenuWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set the window size
        width = 800
        height = 200
        self.setMinimumSize(width, height)

        # setting window title
        self.setWindowTitle('PyQt6 Blank Window')

        # init layout
        self.layout = QGridLayout()
        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        # here is where you create your widgets and add them to the layout
        self.graphWidget = pg.GraphicsLayoutWidget()
        self.graph_layout = QVBoxLayout()
        self.layout.addLayout(self.graph_layout, 0, 0)
        self.graph_layout.addWidget(self.graphWidget)

        # returns a tuple. first in the tuple is a list of user selected files. next is a string
        # saying what filter was used to select them
        self.files, _ = QFileDialog.getOpenFileNames()

        print('you selected the files', self.files)

    def closeEvent(self, event):
        # this code will autorun just before the window closes
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MenuWindow()
    win.show()
    sys.exit(app.exec())
