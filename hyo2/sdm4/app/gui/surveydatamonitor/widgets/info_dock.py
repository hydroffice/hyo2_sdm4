import logging

import matplotlib
from PySide6 import QtGui, QtCore, QtWidgets

logger = logging.getLogger(__name__)
matplotlib.use('Qt5Agg')


class InfoDock(QtWidgets.QDockWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(self.w)
        self.w.setLayout(vbox)

        self.info_viewer = QtWidgets.QTextEdit(self)
        self.resize(QtCore.QSize(400, 80))
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
        self.setWindowTitle("Data Info")
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setWidget(self.w)
        self.installEventFilter(parent)
