#!/usr/bin/env python
"""
This graphs EEG data, live. 
"""

from __future__ import annotations
import csv
import logging
import pdb
import random
import sys
import time
from dataclasses import dataclass

from Board import Board, get_board_id, SIMULATE
from fixation_cross import FixationCrossBuilder
from utils.save_to_csv import save_to_csv

import statistics as stats
from multiprocessing import Process, Queue

from random import randint

import brainflow
import numpy as np
import pyqtgraph as pg
from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, DetrendOperations, FilterTypes
from PyQt6.QtCore import QTimer
from PyQt6.QtOpenGL import *
from PyQt6.QtWidgets import *

from pyqtgraph.Qt import QtCore

from Board import PILL

from typing import NoReturn

from PyQt6 import QtWidgets
from PyQt6.QtCore import QPoint
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QPainter
from PyQt6.QtGui import QPen
from PyQt6.QtGui import QPolygon

from typing import List
from typing import NoReturn
from typing import Tuple

###########################################################

class OddballTaskDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Oddball Task")

        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel("Cick OK to start")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class OddballTask(QWidget):
    def __init__(self, parent=None) -> NoReturn:
        super().__init__(parent=parent)
        
        self.__init_qt_window()
        self.__init_layout()
        self.__setup_board()
        if not self.__show_popup_dialog():
            self.close()
            return

        self.__setup_loop_variables()
        self.__start_task()

    def __init_qt_window(self) -> NoReturn:
        # Set the window size
        width = 800
        height = 200
        self.setMinimumSize(width, height)

        # setting window title
        self.setWindowTitle('PyQt6 Oddball Task')

    def __init_layout(self) -> NoReturn:
        builder = FixationCrossBuilder()
        self.red_cross = builder.set_color("red").build()
        self.green_cross = builder.set_color("green").build()
        self.layout = QVBoxLayout()
        #self.layout.addWidget(self.green_cross)
        self.setLayout(self.layout)

    def __setup_board(self) -> NoReturn:
        self.board = Board(data_type=SIMULATE)

    def __show_popup_dialog(self) -> bool:
        dialog = OddballTaskDialog()
        return dialog.exec()

    def __setup_loop_variables(self) -> NoReturn:
        self.current_iteration = 0
        self.total_iterations = 20
        self.oddball_chance = 0.2

    def __start_task(self) -> NoReturn:
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_stimulus)
        self.timer.start(1000)
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(250)
        self.hide_timer.timeout.connect(self.hide_all_stimulus)
        self.data_read_timer = QTimer()
        self.data_read_timer.timeout.connect(self.read_new_data)
        self.data_read_timer.start(10)

    def read_new_data(self) -> NoReturn:
        for datum in self.board.get_new_data():
            if datum is not None and len(datum) > 0:
                print(f"Collected data point {datum}")

    def show_stimulus(self) -> NoReturn:
        if self.current_iteration >= self.total_iterations:
            self.timer.stop()
            return

        self.current_iteration += 1
        if random.random() <= self.oddball_chance:
            self.__oddball_stimulus()
        else:
            self.__normal_stimulus()

        self.hide_timer.start()


    def hide_all_stimulus(self) -> NoReturn:
        self.__hide_stimulus(self.red_cross)
        self.__hide_stimulus(self.green_cross)
        

    def __normal_stimulus(self) -> NoReturn:
        self.__show_stimulus(self.green_cross)

    def __oddball_stimulus(self) -> NoReturn:
        self.__show_stimulus(self.red_cross)

    def __hide_stimulus(self, stimulus: QWidget) -> NoReturn:
        stimulus.setParent(None)

    def __show_stimulus(self, stimulus) -> NoReturn:
        self.layout.addWidget(stimulus)
        

    def closeEvent(self, event):
        QApplication.quit()
        event.accept()



class OddballTaskOld(QWidget):
    def __init__(
        self,
        hardware=None,
        model=None, sim_type=None,
        data_type=None,
        serial_port=None,
        save_file=None,
        parent=None,
        board_id=None,
        board=None,
    ):
        super().__init__(parent)
        self._init_logger()

        self.logger.info("Initializing Oddball Task (Graph window)")
        self.sim_type = sim_type
        self.hardware = hardware
        self.model = model
        self.data_type = data_type
        # save file should be an ok file name to save to with approriate ending ('.csv')
        self.save_file = save_file
        self.board_id = get_board_id(data_type, hardware, model)
        self.board = board

        if self.board:
            self.exg_channels = self.board.get_exg_channels()
            self.marker_channels = self.board.get_marker_channels()
            self.sampling_rate = self.board.get_sampling_rate()
            self.description = self.board.get_board_description()
        else:
            self.exg_channels = BoardShim.get_exg_channels(self.board_id)
            self.marker_channels = BoardShim.get_marker_channel(self.board_id)
            self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
            self.description = BoardShim.get_board_descr(board_id)

        self.update_speed_ms = 50
        self.window_size = 5 # number of seconds to display
        self.num_points = self.window_size * self.sampling_rate

        if not self.board:
            self.board = Board(
                data_type,
                hardware,
                model,
                board_id,
                serial_port=serial_port,
                num_points=self.num_points,
            )

        self.hardware_connected = True
        self.logger.info("Hardware connected; stream started.")

        self.chan_num = len(self.exg_channels)
        self.exg_channels = np.array(self.exg_channels)
        self.marker_channels = np.array(self.marker_channels)
        print("board decription {}".format(self.description))

        self.logger.debug("EXG channels is {}".format(self.exg_channels))

        # set up stuff to save our data
        # just a numpy array for now
        # 10 minutes of data
        # init a cursor to keep track of where we are in the data
        self.data_max_len = self.sampling_rate * 600
        self.data = np.zeros((self.data_max_len, self.chan_num))
        self.cur_line = 0

        self.graphWidget = pg.GraphicsLayoutWidget()

        layout = QVBoxLayout()
        self.label = QLabel("Real Time Plot")
        layout.addWidget(self.label)
        self.setLayout(layout)
        layout.addWidget(self.graphWidget)

        self._init_timeseries()

        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def _init_logger(self):
        log_file = "boiler.log"
        logging.basicConfig(level=logging.INFO, filemode="a")
        
        f = logging.Formatter(
            "Logger: %(name)s: %(levelname)s at: %(asctime)s, line %(lineno)d: %(message)s"
        )
        stdout = logging.StreamHandler(sys.stdout)
        boiler_log = logging.FileHandler(log_file)
        stdout.setFormatter(f)
        boiler_log.setFormatter(f)
        
        self.logger = logging.getLogger("OddballTask")
        self.logger.addHandler(boiler_log)
        self.logger.addHandler(stdout)
        self.logger.info("Oddball task started at {}".format(time.time()))

    def _init_timeseries(self):
        self.plots = list()
        self.curves = list()
        for i in range(self.chan_num + 1):
            p = self.graphWidget.addPlot(row=i, col=0)
            p.showAxis("left", False)
            p.setMenuEnabled("left", False)
            p.showAxis("bottom", False)
            p.setMenuEnabled("bottom", False)
            if i == 0:
                p.setTitle("TimeSeries Plot")
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)

    def update(self):
        self.logger.debug("Graph window is updating")

        # this is data to be saved. It is only new data since our last call
        data = self.board.get_new_data()
        
        # save data to our csv super quick
        save_to_csv(
            data, self.save_file, self.exg_channels, self.logger
        )
        # note that the data objectwill porbably contain lots of dattathat isn't eeg
        # how much and what it is depends on the board. exg_channels contains the key for
        # what is and isn't eeg. We will ignore non eeg and not save it
        # self.logger.info('data[0] length is {}'.format(len(data[0])))

        data_len = data.shape[1]
        if data_len + self.cur_line >= self.data_max_len:
            # we need to roll over and start at the beginning of the file
            self.data[self.cur_line : self.data_max_len, :] = data[
                self.exg_channels, : self.data_max_len - self.cur_line
            ].T
            self.data[0 : data_len - (self.data_max_len - self.cur_line), :] = data[
                self.exg_channels, self.data_max_len - self.cur_line :
            ].T
            self.cur_line = data_len - (self.data_max_len - self.cur_line)
        else:
            self.data[self.cur_line : self.cur_line + data.shape[1], :] = data[
                self.exg_channels, :
            ].T
            self.cur_line = self.cur_line + data.shape[1]

        # this is data to be graphed. It is the most recent data, of the length that we want to graph
        data = self.board.get_data_quantity(self.num_points)
        # self.logger.info("Data for graphing is: {}".format(data))
        # self.logger.info('data for graphing length is {}'.format(len(data)))
        for count, channel in enumerate(self.exg_channels):
            # plot timeseries
            DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
            DataFilter.perform_bandpass(
                data[channel],
                self.sampling_rate,
                1.0,
                60.0,
                2,
                FilterTypes.BUTTERWORTH.value,
                0,
            )
            # DataFilter.perform_bandpass(
            #     data[channel],
            #     self.sampling_rate,
            #     51.0,
            #     100.0,
            #     2,
            #     FilterTypes.BUTTERWORTH.value,
            #     0,
            # )
            # DataFilter.perform_bandstop(
            #     data[channel],
            #     self.sampling_rate,
            #     50.0,
            #     4.0,
            #     2,
            #     FilterTypes.BUTTERWORTH.value,
            #     0,
            # )
            DataFilter.perform_bandstop(
                data[channel],
                self.sampling_rate,
                58.0,
                62.0,
                2,
                FilterTypes.BUTTERWORTH.value,
                0,
            )
            self.curves[count].setData(data[channel].tolist())

        self.curves[len(self.exg_channels)].setData(data[self.marker_channels].tolist())
        self.logger.debug(
            "Marker channel data was {}".format(data[self.marker_channels].tolist())
        )
        self.logger.debug(
            "Graph window finished updating (successfully got data from board and applied it to graphs)"
        )

    def closeEvent(self, event):
        self.timer.stop()
        self.board.stop()
        self.logger.info(self.data.shape)
        self.logger.info(self.data)
        self.logger.info("Now closing graph window")
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = OddballTask()
    win.show()
    # sys.exit(app.exec())
    pg.exec()
