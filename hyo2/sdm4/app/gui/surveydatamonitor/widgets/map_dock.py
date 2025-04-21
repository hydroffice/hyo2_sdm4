import logging

import cartopy.crs as ccrs
import matplotlib
from PySide6 import QtCore, QtWidgets
from cartopy.feature import NaturalEarthFeature
from matplotlib import cm
from matplotlib import rc_context as rc_context
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavToolBar
from matplotlib.figure import Figure

from hyo2.sdm4.app.gui.surveydatamonitor.widgets.plot_support import PlotSupport

matplotlib.use('Qt5Agg')

logger = logging.getLogger(__name__)


class MapDock(QtWidgets.QDockWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.w = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(self.w)
        self.w.setLayout(vbox)
        with rc_context(PlotSupport.plot_context):

            self.f = Figure(figsize=PlotSupport.f_map_sz, dpi=PlotSupport.f_dpi)
            self.f.patch.set_alpha(0.0)
            self.c = FigureCanvas(self.f)
            self.c.setParent(self.w)
            self.c.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)  # key for press events!!!
            self.c.setFocus()

            self.map_ax = self.f.add_subplot(111)

            self.map = None
            self.map_colormap = cm.get_cmap('jet')
            self.map_points = None
            self.map_casts = None
            self.f_colorbar = None

            self.nav = NavToolBar(canvas=self.c, parent=self.w, coordinates=True)
            self.nav.setIconSize(QtCore.QSize(14, 14))

        vbox.addWidget(self.c)
        vbox.addWidget(self.nav)
        vbox.setContentsMargins(0, 0, 0, 0)

        self.setWindowTitle("Surface Sound Speed Map")
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setWidget(self.w)
        self.installEventFilter(parent)

        settings = QtCore.QSettings()
        area_label = settings.value("monitor/initial_area", "World")
        if area_label == "World":

            self.plot_world()

        elif area_label == "Contiguous United States":

            self.plot_conus()

        elif area_label == "Alaska":

            self.plot_alaska()

        elif area_label == "Hawaii":

            self.plot_hawaii()

        else:
            raise RuntimeError("Unknown area: %s" % area_label)

    def plot_world(self):
        logger.debug("plotting world area")
        with rc_context(PlotSupport.plot_context):
            self.map_ax.remove()
            self.map_ax = self.f.add_subplot(111, projection=ccrs.PlateCarree())

            self.nav.update()

            scale = '110m'
            ocean = NaturalEarthFeature('physical', 'ocean', scale, edgecolor='#777777',
                                        facecolor="#5da1c9", zorder=2)
            # noinspection PyUnresolvedReferences
            self.map_ax.add_feature(ocean)
            # noinspection PyUnresolvedReferences
            self.map_ax.gridlines(color='#909090', linestyle='--', zorder=3)
            self.map_points = self.map_ax.scatter([], [], c=[], s=20, alpha=0.4,
                                                  vmin=1450.0, vmax=1550.0, cmap=self.map_colormap, zorder=4)
            self.map_casts = self.map_ax.scatter([], [], marker="+", s=40, alpha=0.8, color="k",
                                                 label="Sound Speed Casts", zorder=4)
            self.map_ax.legend(loc="upper right", prop={'size': 6})
            self.map_ax.set_extent([-180, 180, -80, 80], crs=ccrs.PlateCarree())

            if self.f_colorbar is not None:
                self.f_colorbar.remove()
            self.f_colorbar = None

    def plot_conus(self):
        logger.debug("plotting conus area")
        with rc_context(PlotSupport.plot_context):
            self.map_ax.remove()
            self.map_ax = self.f.add_subplot(111, projection=ccrs.PlateCarree())

            self.nav.update()

            scale = '110m'
            ocean = NaturalEarthFeature('physical', 'ocean', scale, edgecolor='#777777',
                                        facecolor="#5da1c9", zorder=2)
            # noinspection PyUnresolvedReferences
            self.map_ax.add_feature(ocean)
            # noinspection PyUnresolvedReferences
            self.map_ax.gridlines(color='#909090', linestyle='--', zorder=3)
            self.map_points = self.map_ax.scatter([], [], c=[], s=20, alpha=0.4,
                                                  vmin=1450.0, vmax=1550.0, cmap=self.map_colormap, zorder=4)
            self.map_casts = self.map_ax.scatter([], [], marker="+", s=40, alpha=0.8, color="k",
                                                 label="Sound Speed Casts", zorder=4)
            self.map_ax.legend(loc="upper right", prop={'size': 6})
            self.map_ax.set_extent([-129.17, -65.69, 23.81, 49.38], crs=ccrs.PlateCarree())

            if self.f_colorbar is not None:
                self.f_colorbar.remove()
            self.f_colorbar = None

    def plot_alaska(self):
        logger.debug("plotting alaska area")
        with rc_context(PlotSupport.plot_context):
            self.map_ax.remove()
            self.map_ax = self.f.add_subplot(111, projection=ccrs.PlateCarree())

            self.nav.update()

            scale = '110m'
            ocean = NaturalEarthFeature('physical', 'ocean', scale, edgecolor='#777777',
                                        facecolor="#5da1c9", zorder=2)
            # noinspection PyUnresolvedReferences
            self.map_ax.add_feature(ocean)
            # noinspection PyUnresolvedReferences
            self.map_ax.gridlines(color='#909090', linestyle='--', zorder=3)
            self.map_points = self.map_ax.scatter([], [], c=[], s=20, alpha=0.4,
                                                  vmin=1450.0, vmax=1550.0, cmap=self.map_colormap, zorder=4)
            self.map_casts = self.map_ax.scatter([], [], marker="+", s=40, alpha=0.8, color="k",
                                                 label="Sound Speed Casts", zorder=4)
            self.map_ax.legend(loc="upper right", prop={'size': 6})
            self.map_ax.set_extent([-180, -130, 50, 74], crs=ccrs.PlateCarree())

            if self.f_colorbar is not None:
                self.f_colorbar.remove()
            self.f_colorbar = None

    def plot_hawaii(self):
        logger.debug("plotting hawaii area")
        with rc_context(PlotSupport.plot_context):
            self.map_ax.remove()
            self.map_ax = self.f.add_subplot(111, projection=ccrs.PlateCarree())

            self.nav.update()

            scale = '110m'
            ocean = NaturalEarthFeature('physical', 'ocean', scale, edgecolor='#777777',
                                        facecolor="#5da1c9", zorder=2)
            # noinspection PyUnresolvedReferences
            self.map_ax.add_feature(ocean)
            # noinspection PyUnresolvedReferences
            self.map_ax.gridlines(color='#909090', linestyle='--', zorder=3)
            self.map_points = self.map_ax.scatter([], [], c=[], s=20, alpha=0.4,
                                                  vmin=1450.0, vmax=1550.0, cmap=self.map_colormap, zorder=4)
            self.map_casts = self.map_ax.scatter([], [], marker="+", s=40, alpha=0.8, color="k",
                                                 label="Sound Speed Casts", zorder=4)
            self.map_ax.legend(loc="upper right", prop={'size': 6})
            self.map_ax.set_extent([-167, -147, 14, 26], crs=ccrs.PlateCarree())

            if self.f_colorbar is not None:
                self.f_colorbar.remove()
            self.f_colorbar = None
