from PySide6 import QtGui, QtCore, QtWidgets
import matplotlib

import logging

from hyo2.sdm4.lib.estimate.abstractestimator import EstimationModes

logger = logging.getLogger(__name__)
matplotlib.use('Qt5Agg')


class EstimationDock(QtWidgets.QDockWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(self.w)
        self.w.setLayout(vbox)

        self.info_viewer = QtWidgets.QTextEdit(self)
        self.setMinimumSize(QtCore.QSize(320, 120))
        self.resize(QtCore.QSize(400, 240))
        self.info_viewer.setTextColor(QtGui.QColor("#4682b4"))
        # create a monospace font
        font = QtGui.QFont("Courier New")
        font.setStyleHint(QtGui.QFont.StyleHint.TypeWriter)
        font.setFixedPitch(True)
        font.setPointSize(8)
        self.info_viewer.document().setDefaultFont(font)

        # set the tab size
        metrics = QtGui.QFontMetrics(font)
        self.info_viewer.setTabStopDistance(3 * metrics.horizontalAdvance(' '))

        self.info_viewer.setReadOnly(True)

        vbox.addWidget(self.info_viewer)
        vbox.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle("Next-cast Info")
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setWidget(self.w)
        self.installEventFilter(parent)

        self._last_mode = EstimationModes.UNKNOWN
        self._blink = False
        self._stop_blinking = False
        self._is_blinking = False
        self._bg_color = None
        self.update_mode(self._last_mode)

    def update_mode(self, mode):

        if self._last_mode == mode:
            return

        if mode == EstimationModes.UNKNOWN:
            self._bg_color = "#d3d3d3"

        elif mode == EstimationModes.PANIC:
            self._bg_color = "#fa8072"

        elif mode == EstimationModes.STEADY:
            self._bg_color = "#87cefa"

        elif mode == EstimationModes.RELAX:
            self._bg_color = "#90ee90"

        self.info_viewer.setStyleSheet("background: %s;" % self._bg_color)

    def start_blinking(self):
        if self._is_blinking:  # it is already blinking
            return

        self._stop_blinking = False
        self._is_blinking = True

        self._blinking()

    def stop_blinking(self):
        self._stop_blinking = True
        self._is_blinking = False

    def _blinking(self):
        if self._stop_blinking:
            self.info_viewer.setStyleSheet("background: %s;" % self._bg_color)
            return

        if not self._blink:
            self.info_viewer.setStyleSheet("background: #ffffff;")
        else:
            self.info_viewer.setStyleSheet("background: %s;" % self._bg_color)

        self._blink = not self._blink

        # noinspection PyTypeChecker
        QtCore.QTimer.singleShot(1000, self._blinking)
