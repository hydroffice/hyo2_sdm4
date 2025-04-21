import logging
from datetime import datetime, timedelta

import matplotlib
from PySide6 import QtCore, QtWidgets
from matplotlib import rc_context as rc_context
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavToolBar
from matplotlib.figure import Figure

from hyo2.sdm4.app.gui.surveydatamonitor.widgets.plot_support import PlotSupport

matplotlib.use('Qt5Agg')
logger = logging.getLogger(__name__)


class PlotDockDepthTime(QtWidgets.QDockWidget):

    def __init__(self, parent=None, sharex=None):
        super().__init__(parent=parent)

        self.w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(self.w)
        self.w.setLayout(vbox)
        with rc_context(PlotSupport.plot_context):
            self.f = Figure(figsize=PlotSupport.f_sz, dpi=PlotSupport.f_dpi)
            self.f.patch.set_alpha(0.0)
            self.c = FigureCanvas(self.f)
            self.c.setParent(self.w)
            self.c.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)  # key for press events!!!
            self.c.setFocus()
            self.depth_ax = self.f.add_subplot(111, sharex=sharex)
            self.depth_ax.invert_yaxis()
            self.depth, = self.depth_ax.plot([], [],
                                             color=PlotSupport.avg_depth_color,
                                             linestyle='--',
                                             marker='o',
                                             label='Avg Depth',
                                             ms=3
                                             )
            self.depth_ax.set_ylim(1000.0, 0.0)
            self.depth_ax.set_xlim(datetime.now(), datetime.now() + timedelta(seconds=60))
            self.depth_ax.grid(True)
            self.depth_ax.ticklabel_format(useOffset=False, axis='y')
            self.nav = NavToolBar(canvas=self.c, parent=self.w, coordinates=True)
            self.nav.setIconSize(QtCore.QSize(14, 14))
        vbox.addWidget(self.c)
        vbox.addWidget(self.nav)
        vbox.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle("Average Depth vs. Time")
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setWidget(self.w)
        self.installEventFilter(parent)
