import logging
from datetime import datetime, timedelta

import matplotlib
from PySide6 import QtCore, QtWidgets
from matplotlib import rc_context as rc_context
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavToolBar
from matplotlib.figure import Figure

from hyo2.sdm4.app.gui.surveydatamonitor.widgets.plot_support import PlotSupport

logger = logging.getLogger(__name__)
matplotlib.use('Qt5Agg')


class PlotDockDraftTime(QtWidgets.QDockWidget):

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
            self.draft_ax = self.f.add_subplot(111, sharex=sharex)
            self.draft_ax.invert_yaxis()
            # self.draft_ax.set_ylabel('Depth [m]')
            # self.draft_ax.set_xlabel('Time')
            self.draft, = self.draft_ax.plot([], [],
                                             color=PlotSupport.draft_color,
                                             linestyle='--',
                                             marker='o',
                                             label='TSS',
                                             ms=3
                                             )
            self.draft_ax.set_ylim(10.0, 0.0)
            self.draft_ax.set_xlim(datetime.now(), datetime.now() + timedelta(seconds=60))
            self.draft_ax.grid(True)
            self.draft_ax.ticklabel_format(useOffset=False, axis='y')
            self.nav = NavToolBar(canvas=self.c, parent=self.w, coordinates=True)
            self.nav.setIconSize(QtCore.QSize(14, 14))
        vbox.addWidget(self.c)
        vbox.addWidget(self.nav)
        vbox.setContentsMargins(0, 0, 0, 0)

        self.setWindowTitle("Transducer Depth vs. Time")
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setWidget(self.w)
