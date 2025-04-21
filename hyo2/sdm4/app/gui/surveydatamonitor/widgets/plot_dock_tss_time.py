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


class PlotDockTssTime(QtWidgets.QDockWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.w2 = None
        self.dw2 = None
        self.f2 = None
        self.c2 = None
        self.draft = None
        self.draft_ax = None
        self.nv2 = None

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
            self.tss_ax = self.f.add_subplot(111)
            # self.tss_ax.set_ylabel('Sound Speed [m/s]')
            # self.tss_ax.set_xlabel('Time')
            self.tss, = self.tss_ax.plot([], [],
                                         color=PlotSupport.tss_color,
                                         linestyle='--',
                                         marker='o',
                                         label='TSS',
                                         ms=3
                                         )
            self.tss_ax.set_ylim(bottom=1450.0, top=1550.0)
            self.tss_ax.set_xlim(left=datetime.now(),
                                 right=datetime.now() + timedelta(seconds=60))
            self.tss_ax.grid(True)
            self.tss_ax.ticklabel_format(useOffset=False, axis='y')
            # dates = matplotlib.dates.date2num(list_of_datetimes)
            self.nav = NavToolBar(canvas=self.c, parent=self.w, coordinates=True)
            self.nav.setIconSize(QtCore.QSize(14, 14))
        vbox.addWidget(self.c)
        vbox.addWidget(self.nav)
        vbox.setContentsMargins(0, 0, 0, 0)

        self.setWindowTitle("Surface Sound Speed vs. Time")
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setWidget(self.w)
        self.installEventFilter(parent)
