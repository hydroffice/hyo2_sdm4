import logging
import os
from datetime import datetime, timedelta

import matplotlib
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from matplotlib import rc_context as rc_context

from hyo2.sdm4.app.gui.surveydatamonitor.dialogs.export_data_monitor_dialog import ExportDataMonitorDialog
from hyo2.sdm4.app.gui.surveydatamonitor.dialogs.monitor_option_dialog import MonitorOption
from hyo2.sdm4.app.gui.surveydatamonitor.widgets.estimation_dock import EstimationDock
from hyo2.sdm4.app.gui.surveydatamonitor.widgets.info_dock import InfoDock
from hyo2.sdm4.app.gui.surveydatamonitor.widgets.map_dock import MapDock
from hyo2.sdm4.app.gui.surveydatamonitor.widgets.plot_dock_depth_time import PlotDockDepthTime
from hyo2.sdm4.app.gui.surveydatamonitor.widgets.plot_dock_draft_time import PlotDockDraftTime
from hyo2.sdm4.app.gui.surveydatamonitor.widgets.plot_dock_tss_time import PlotDockTssTime
from hyo2.sdm4.app.gui.surveydatamonitor.widgets.plot_support import PlotSupport
from hyo2.sdm4.lib import monitor
from hyo2.ssm2.app.gui.soundspeedmanager.widgets.widget import AbstractWidget

matplotlib.use('Qt5Agg')
logger = logging.getLogger(__name__)


class SurveyDataMonitor(AbstractWidget):
    here = os.path.abspath(os.path.join(os.path.dirname(__file__)))  # to be overloaded
    media = os.path.abspath(os.path.join(here, os.pardir, 'media')).replace("\\", "/")

    def __init__(self, main_win, lib, timing=3.0):
        AbstractWidget.__init__(self, main_win=main_win, lib=lib)
        self.monitor = monitor.SurveyDataMonitor(ssm=self.lib)
        self.settings = QtCore.QSettings()
        self._plotting_timing = timing * 1000  # milliseconds

        self._plotting_active = False
        self._plotting_pause = False
        self._last_nr_samples = 0

        # noinspection PyTypeChecker
        self._plotting_samples = int(self.settings.value("monitor/plotting_samples", 200))
        self.settings.setValue("monitor/plotting_samples", self._plotting_samples)

        # ###    ACTIONS   ###
        self.start_monitor_act = None
        self.pause_monitor_act = None
        self.stop_monitor_act = None
        self.open_output_act = None
        self.add_data_act = None
        self.export_data_act = None
        self.view_tss_time_plot_action = None
        self.view_draft_time_plot_action = None
        self.view_depth_time_plot_action = None
        self.view_info_viewer_action = None
        self._make_actions()

        # ###    PLOTS    ###

        # create the overall layout
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.frame.setLayout(self.main_layout)

        # docks
        self.dw_info_viewer = InfoDock(parent=self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.dw_info_viewer)
        self.dw_map = MapDock(parent=self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.dw_map)
        self.dw_plot_tss = PlotDockTssTime(parent=self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.dw_plot_tss)
        self.dw_plot_draft = PlotDockDraftTime(parent=self, sharex=self.dw_plot_tss.tss_ax)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.dw_plot_draft)
        self.dw_plot_depth = PlotDockDepthTime(parent=self, sharex=self.dw_plot_tss.tss_ax)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.dw_plot_depth)
        self.dw_estimation_viewer = EstimationDock(parent=self)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.dw_estimation_viewer)

        self.options_dialog = MonitorOption(parent=self, main_win=self, lib=self.lib, monitor=self.monitor)
        self.options_dialog.setHidden(True)

        # initial plot views
        self.dw_map.setHidden(True)
        self._make_estimation_viewer_visible(False)
        self._make_info_viewer_visible(False)
        self._make_tss_time_plot_visible(False)
        self._make_draft_time_plot_visible(False)
        self._make_depth_time_plot_visible(False)

    @property
    def plotting_samples(self):
        return self._plotting_samples

    @plotting_samples.setter
    def plotting_samples(self, value):
        self._plotting_samples = value
        self.settings.setValue("monitor/plotting_samples", self._plotting_samples)

    def _make_actions(self):

        # ### Data Monitor ###
        monitor_bar = self.addToolBar('Data Monitor')
        monitor_bar.setIconSize(QtCore.QSize(40, 40))

        # start
        self.start_monitor_act = QtGui.QAction(QtGui.QIcon(os.path.join(self.media, 'start.png')),
                                               'Start monitoring survey data', self)
        # self.start_monitor_act.setShortcut('Ctrl+Alt+B')
        # noinspection PyUnresolvedReferences
        self.start_monitor_act.triggered.connect(self.on_start_monitor)
        monitor_bar.addAction(self.start_monitor_act)
        self.main_win.monitor_menu.addAction(self.start_monitor_act)

        # pause
        self.pause_monitor_act = QtGui.QAction(QtGui.QIcon(os.path.join(self.media, 'pause.png')),
                                               'Pause monitoring survey data', self)
        # self.pause_monitor_act.setShortcut('Ctrl+Alt+P')
        # noinspection PyUnresolvedReferences
        self.pause_monitor_act.triggered.connect(self.on_pause_monitor)
        self.pause_monitor_act.setDisabled(True)
        monitor_bar.addAction(self.pause_monitor_act)
        self.main_win.monitor_menu.addAction(self.pause_monitor_act)

        # stop
        self.stop_monitor_act = QtGui.QAction(QtGui.QIcon(os.path.join(self.media, 'stop.png')),
                                              'Stop monitoring survey data', self)
        # self.stop_monitor_act.setShortcut('Ctrl+Alt+S')
        # noinspection PyUnresolvedReferences
        self.stop_monitor_act.triggered.connect(self.on_stop_monitor)
        self.stop_monitor_act.setDisabled(True)
        monitor_bar.addAction(self.stop_monitor_act)
        self.main_win.monitor_menu.addAction(self.stop_monitor_act)

        # options
        self.options_action = QtGui.QAction(QtGui.QIcon(os.path.join(self.media, 'options.png')),
                                            'Set options', self)
        # self.options_action.setShortcut('Ctrl+Alt+O')
        # noinspection PyUnresolvedReferences
        self.options_action.triggered.connect(self.on_view_options)
        monitor_bar.addAction(self.options_action)
        self.main_win.monitor_menu.addAction(self.options_action)

        # ### Data Manager ###
        manager_bar = self.addToolBar('Data Manager')
        manager_bar.setIconSize(QtCore.QSize(40, 40))

        # open output folder
        self.open_output_act = QtGui.QAction(QtGui.QIcon(os.path.join(self.media, 'load.png')),
                                             'Open output folder', self)
        # self.open_output_act.setShortcut('Alt+O')
        # noinspection PyUnresolvedReferences
        self.open_output_act.triggered.connect(self.on_open_output)
        manager_bar.addAction(self.open_output_act)

        # add data
        self.add_data_act = QtGui.QAction(QtGui.QIcon(os.path.join(self.media, 'import_data.png')),
                                          'Add data to the current data set', self)
        # self.add_data_act.setShortcut('Alt+A')
        # noinspection PyUnresolvedReferences
        self.add_data_act.triggered.connect(self.on_add_data)
        manager_bar.addAction(self.add_data_act)

        # export data
        self.export_data_act = QtGui.QAction(QtGui.QIcon(os.path.join(self.media, 'export_data.png')),
                                             'Export data', self)
        # self.export_data_act.setShortcut('Alt+X')
        # noinspection PyUnresolvedReferences
        self.export_data_act.triggered.connect(self.on_export_data)
        manager_bar.addAction(self.export_data_act)

        # ### Data Views ###
        views_bar = self.addToolBar('Data Views')
        views_bar.setIconSize(QtCore.QSize(40, 40))

        # view info viewer
        # noinspection PyArgumentList
        self.view_info_viewer_action = QtGui.QAction(QtGui.QIcon(os.path.join(self.media, 'info_viewer.png')),
                                                     'View info on current data', self, checkable=True)
        # self.view_info_viewer_action.setShortcut('Ctrl+V')
        # noinspection PyUnresolvedReferences
        self.view_info_viewer_action.triggered.connect(self.on_view_info_viewer)
        views_bar.addAction(self.view_info_viewer_action)

        # view tss vs time plot
        # noinspection PyArgumentList
        self.view_tss_time_plot_action = QtGui.QAction(QtGui.QIcon(os.path.join(self.media, 'tss_plot.png')),
                                                       'View TSS vs time plot', self, checkable=True)
        # self.view_tss_time_plot_action.setShortcut('Ctrl+T')
        # noinspection PyUnresolvedReferences
        self.view_tss_time_plot_action.triggered.connect(self.on_view_tss_time_plot)
        views_bar.addAction(self.view_tss_time_plot_action)

        # view draft vs time plot
        # noinspection PyArgumentList
        self.view_draft_time_plot_action = QtGui.QAction(QtGui.QIcon(os.path.join(self.media, 'draft_plot.png')),
                                                         'View draft vs time plot', self, checkable=True)
        # self.view_draft_time_plot_action.setShortcut('Ctrl+D')
        # noinspection PyUnresolvedReferences
        self.view_draft_time_plot_action.triggered.connect(self.on_view_draft_time_plot)
        views_bar.addAction(self.view_draft_time_plot_action)

        # view avg depth vs time plot
        # noinspection PyArgumentList
        self.view_depth_time_plot_action = QtGui.QAction(
            QtGui.QIcon(os.path.join(self.media, 'avg_depth_plot.png')),
            'View avg depth vs time plot', self, checkable=True)
        # self.view_depth_time_plot_action.setShortcut('Ctrl+A')
        # noinspection PyUnresolvedReferences
        self.view_depth_time_plot_action.triggered.connect(self.on_view_depth_time_plot)
        views_bar.addAction(self.view_depth_time_plot_action)

        # view estimation viewer
        # noinspection PyArgumentList
        self.view_estimation_viewer_action = QtGui.QAction(QtGui.QIcon(os.path.join(self.media, 'next_viewer.png')),
                                                           'View info on next estimated cast', self, checkable=True)
        # self.view_estimation_viewer_action.setShortcut('Ctrl+E')
        # noinspection PyUnresolvedReferences
        self.view_estimation_viewer_action.triggered.connect(self.on_view_estimation_viewer)
        views_bar.addAction(self.view_estimation_viewer_action)

    def plotting(self):
        if not self._plotting_active:
            logger.debug("Stop plotting")
            return

        if self._plotting_pause:
            logger.debug("Pause plotting")
            # noinspection PyTypeChecker
            QtCore.QTimer.singleShot(self._plotting_timing, self.plotting)
            return

        # logger.debug("Plotting every %s milliseconds" % self._plotting_timing)

        # update text
        self.monitor.lock_data()
        self.dw_info_viewer.info_viewer.setPlainText(self.monitor.data_info)
        self.dw_estimation_viewer.info_viewer.setPlainText(self.monitor.next_cast_info)
        self.dw_estimation_viewer.update_mode(self.monitor.mode)
        cur_time = datetime.now()
        # logger.debug("current time: %s, next cast time: %s" % (cur_time, self.monitor.next_cast_time))
        if self.monitor.next_cast_time:
            if cur_time > self.monitor.next_cast_time:
                self.dw_estimation_viewer.start_blinking()
            else:
                self.dw_estimation_viewer.stop_blinking()
        if self.monitor.casttime.plotting_mode:
            self.plotting_analysis()
        self.monitor.unlock_data()

        # update plots
        cur_nr_samples = self.monitor.nr_of_samples()
        if cur_nr_samples > self._last_nr_samples:
            logger.debug("Plotting -> samples: %d" % cur_nr_samples)
            self.update_plot_data(cur_nr_samples)
        self._last_nr_samples = cur_nr_samples

        # noinspection PyTypeChecker
        QtCore.QTimer.singleShot(self._plotting_timing, self.plotting)

    def refresh_plots(self):
        self.dw_map.c.draw()
        self.dw_plot_tss.c.draw()
        self.dw_plot_draft.c.draw()
        self.dw_plot_depth.c.draw()
        self.update()

    def _clear_plot_data(self):
        self.dw_map.map_points.set_array(np.ma.resize(self.dw_map.map_points.get_array(), (0,)))
        self.dw_map.map_points.set_offsets(np.ma.resize(self.dw_map.map_points.get_offsets(), (0, 2)))
        # print("1.\n%s" % (self.dw_map.map_points.get_array().shape, ))
        # print("2.\n%s" % (self.dw_map.map_points.get_offsets().shape, ))
        self.dw_plot_tss.tss.set_xdata([])
        self.dw_plot_tss.tss.set_ydata([])
        self.dw_plot_draft.draft.set_xdata([])
        self.dw_plot_draft.draft.set_ydata([])
        self.dw_plot_depth.depth.set_xdata([])
        self.dw_plot_depth.depth.set_ydata([])
        self.refresh_plots()

    def set_initial_plot_area(self, area_label):
        logger.debug("set initial area to: %s" % area_label)

        if area_label == "World":

            self.dw_map.plot_world()

        elif area_label == "Contiguous United States":

            self.dw_map.plot_conus()

        elif area_label == "Alaska":

            self.dw_map.plot_alaska()

        elif area_label == "Hawaii":

            self.dw_map.plot_hawaii()

        else:
            raise RuntimeError("Unknown area: %s" % area_label)

        self.settings.setValue("monitor/initial_area", area_label)
        self.update_plot_data()

    def update_plot_data(self, nr_of_samples=None):

        if nr_of_samples is None:
            nr_of_samples = self.monitor.nr_of_samples()

        if nr_of_samples < 2:
            return

        self.monitor.lock_data()

        # just plot the latest nth samples, if available
        plot_idx = self._plotting_samples
        if plot_idx > nr_of_samples:
            plot_idx = nr_of_samples

        # logger.debug("plotting latest %d samples" % plot_idx)
        times = self.monitor.times[-plot_idx:]
        min_time = min(times) - timedelta(seconds=5)
        max_time = max(times) + timedelta(seconds=5)
        cast_longs, cast_lats = self.monitor.lonlat_casts(min_time - timedelta(days=3650),
                                                          max_time + timedelta(days=3650))
        logger.debug("casts to visualize: %d" % len(cast_longs))
        tsss = self.monitor.tsss[-plot_idx:]
        min_tsss = min(tsss) - 0.3
        max_tsss = max(tsss) + 0.3

        # find the tsss zoom range with new tsss samples
        try:
            min_zoom, max_zoom = self.dw_plot_tss.tss_ax.get_ylim()
            nr_of_new_samples = nr_of_samples - self._last_nr_samples
            if nr_of_new_samples > plot_idx:
                nr_of_new_samples = plot_idx
            new_tsss = self.monitor.tsss[-nr_of_new_samples:]
            min_zoom = min(min_zoom, min(new_tsss) - 0.3)
            max_zoom = max(max_zoom, max(new_tsss) + 0.3)
            min_tsss_zoom = max(min_zoom, min_tsss)
            max_tsss_zoom = min(max_zoom, max_tsss)
        except Exception:
            min_tsss_zoom = min_tsss
            max_tsss_zoom = max_tsss

        drafts = self.monitor.drafts[-plot_idx:]
        min_drafts = min(drafts) - 0.5
        max_drafts = max(drafts) + 0.5
        depths = self.monitor.depths[-plot_idx:]
        min_depths = min(depths) - 5.
        max_depths = max(depths) + 5.
        self.dw_plot_tss.tss.set_xdata(times)
        self.dw_plot_tss.tss.set_ydata(tsss)
        self.dw_plot_draft.draft.set_xdata(times)
        self.dw_plot_draft.draft.set_ydata(drafts)
        self.dw_plot_depth.depth.set_xdata(times)
        self.dw_plot_depth.depth.set_ydata(depths)

        longs = self.monitor.longs[-plot_idx:]
        lats = self.monitor.lats[-plot_idx:]
        self.dw_map.map_points.set_array(np.array(tsss))
        self.dw_map.map_points.set_offsets(np.vstack([longs, lats]).T)
        self.dw_map.map_points.set_clim(vmin=min_tsss, vmax=max_tsss)
        self.dw_map.map_casts.set_offsets(np.vstack([cast_longs, cast_lats]).T)

        if self.dw_map.f_colorbar is None:
            with rc_context(PlotSupport.plot_context):
                self.dw_map.f_colorbar = self.dw_map.f.colorbar(self.dw_map.map_points, ax=self.dw_map.map_ax,
                                                                aspect=50, fraction=0.07,
                                                                orientation='horizontal', format='%.1f')
                self.dw_map.f.tight_layout()
                self.dw_map.f.subplots_adjust(bottom=0.01, top=0.99)

        self.dw_map.f_colorbar.solids.set(alpha=1)
        self.dw_map.f_colorbar.mappable.set_clim(vmin=min_tsss, vmax=max_tsss)

        self.dw_plot_tss.tss_ax.set_xlim(min_time, max_time)
        self.dw_plot_tss.tss_ax.set_ylim(min_tsss_zoom, max_tsss_zoom)
        self.dw_plot_draft.draft_ax.set_ylim(max_drafts, min_drafts)
        self.dw_plot_depth.depth_ax.set_ylim(max_depths, min_depths)

        self.monitor.unlock_data()

        self.refresh_plots()
        # logger.debug("updated")

    def plotting_analysis(self):
        self.monitor.casttime.plotting_analysis(self.monitor.current_time)

    def start_plotting(self):
        if self._plotting_pause:
            logger.debug("Resume plotting")
            self._plotting_pause = False
            return

        self._plotting_active = True
        self._plotting_pause = False
        self._last_nr_samples = 0

        logger.debug("Start plotting")

        self.plotting()

    def pause_plotting(self):
        self._plotting_active = True
        self._plotting_pause = True

    def stop_plotting(self):
        if self.monitor.active:
            self.monitor.stop_monitor()
        self.dw_estimation_viewer.stop_blinking()
        self._plotting_active = False
        self._plotting_pause = False

    # ### SLOTS ###

    # data monitor

    @QtCore.Slot()
    def on_start_monitor(self):

        if hasattr(self.main_win, "switch_to_monitor_tab"):
            self.main_win.switch_to_monitor_tab()

        if not self.lib.use_sis():
            msg = "The SIS listener is disabled!\n\n" \
                  "To activate the listening, go to \"Setup\" tab, then \"Input\" sub-tab."
            # noinspection PyCallByClass,PyTypeChecker
            QtWidgets.QMessageBox.warning(self, "Sound Speed Manager - SIS", msg,
                                          QtWidgets.QMessageBox.StandardButton.Ok)
            return

        if not self.lib.listen_sis():
            msg = "Unable to listen SIS!\n\nDouble check the SSM-SIS configuration."
            # noinspection PyCallByClass,PyTypeChecker
            QtWidgets.QMessageBox.warning(self, "Sound Speed Manager - SIS", msg,
                                          QtWidgets.QMessageBox.StandardButton.Ok)
            return

        clear_data = True
        nr_of_samples = self.monitor.nr_of_samples()
        if nr_of_samples > 0:

            msg = "Some data are already present(%s samples)!\n\n" \
                  "Do you want to start a new monitoring session?\n" \
                  "If you click on No, the data will be appended." % nr_of_samples
            # noinspection PyCallByClass,PyUnresolvedReferences
            ret = QtWidgets.QMessageBox.warning(self, "Survey Data Monitor", msg,
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.StandardButton.No:
                clear_data = False

        if clear_data:
            self.monitor.clear_data()
            self._clear_plot_data()

        self.monitor.start_monitor(clear_data=clear_data)
        self.start_plotting()

        self.start_monitor_act.setEnabled(False)
        self.pause_monitor_act.setEnabled(True)
        self.stop_monitor_act.setEnabled(True)
        self.dw_map.setVisible(True)
        self._make_info_viewer_visible(False)
        self._make_estimation_viewer_visible(True)
        self._make_tss_time_plot_visible(True)
        self._make_draft_time_plot_visible(False)
        self._make_depth_time_plot_visible(False)

    @QtCore.Slot()
    def on_pause_monitor(self):

        if hasattr(self.main_win, "switch_to_monitor_tab"):
            self.main_win.switch_to_monitor_tab()

        self.monitor.pause_monitor()
        self.pause_plotting()

        self.start_monitor_act.setEnabled(True)
        self.pause_monitor_act.setEnabled(False)
        self.stop_monitor_act.setEnabled(True)

    @QtCore.Slot()
    def on_stop_monitor(self):

        if hasattr(self.main_win, "switch_to_monitor_tab"):
            self.main_win.switch_to_monitor_tab()

        self.monitor.stop_monitor()
        self.stop_plotting()

        self.start_monitor_act.setEnabled(True)
        self.pause_monitor_act.setEnabled(False)
        self.stop_monitor_act.setEnabled(False)

        if self.monitor.nr_of_samples() == 0:
            self.dw_map.setVisible(False)
            self._make_info_viewer_visible(False)
            self._make_estimation_viewer_visible(False)
            self._make_tss_time_plot_visible(False)
            self._make_draft_time_plot_visible(False)
            self._make_depth_time_plot_visible(False)

    # data manager

    @QtCore.Slot()
    def on_open_output(self):
        self.monitor.open_output_folder()

    @QtCore.Slot()
    def on_add_data(self):
        logger.debug("Adding data")

        if self.monitor.active:
            msg = "The survey data monitoring is ongoing!\n\n" \
                  "To add data, you have to first stop the monitoring."
            # noinspection PyCallByClass,PyTypeChecker
            QtWidgets.QMessageBox.warning(self, "Survey Data Monitor", msg, QtWidgets.QMessageBox.StandardButton.Ok)
            return

        # noinspection PyCallByClass
        selections, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Add data", self.monitor.output_folder,
                                                               "Monitor db(*.mon);;Kongsberg EM Series(*.all)")
        if not selections:
            return
        logger.debug("user selected %d files" % len(selections))

        # check if data are already present
        clear_data = False
        nr_of_samples = self.monitor.nr_of_samples()
        if nr_of_samples > 0:

            msg = "Some data are already present(%s samples)!\n\n" \
                  "Do you want to merge the new samples with the existing ones?\n" \
                  "If you click on No, a different session will be used." % nr_of_samples
            # noinspection PyCallByClass,PyUnresolvedReferences
            ret = QtWidgets.QMessageBox.warning(self, "Survey Data Monitor", msg,
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.StandardButton.No:
                clear_data = True

        if clear_data:
            self.monitor.clear_data()

        self._clear_plot_data()

        file_ext = os.path.splitext(selections[0])[-1]
        if file_ext == ".mon":

            self.progress.start(title="Survey Data Monitor", text="Database data loading")
            self.progress.update(20)
            self.monitor.add_db_data(filenames=selections)
            self.progress.end()

        elif file_ext == ".all":

            self.progress.start(title="Survey Data Monitor", text="Kongsberg data loading")
            self.progress.update(20)
            self.monitor.add_kongsberg_data(filenames=selections)
            self.progress.end()

        else:
            raise RuntimeError("Passed unsupported file extension: %s" % file_ext)

        nr_of_samples = self.monitor.nr_of_samples()
        self.update_plot_data(nr_of_samples=nr_of_samples)
        if nr_of_samples > 2:
            self._make_tss_time_plot_visible(True)
            self._make_draft_time_plot_visible(True)
            self.dw_map.setVisible(True)
        self.refresh_plots()

    @QtCore.Slot()
    def on_export_data(self):
        logger.debug("Exporting data")

        nr_of_samples = self.monitor.nr_of_samples()
        if nr_of_samples == 0:
            msg = "There are currently not samples to export!\n"
            # noinspection PyCallByClass,PyTypeChecker
            QtWidgets.QMessageBox.warning(self, "Survey Data Monitor", msg, QtWidgets.QMessageBox.StandardButton.Ok)
            return

        dlg = ExportDataMonitorDialog(lib=self.lib, monitor=self.monitor, main_win=self.main_win, parent=self)
        dlg.exec_()

    # data views

    @QtCore.Slot()
    def on_view_tss_time_plot(self):
        if self.dw_plot_tss.isVisible():
            self._make_tss_time_plot_visible(False)
        else:
            self._make_tss_time_plot_visible(True)

        self.refresh_plots()

    @QtCore.Slot()
    def on_view_draft_time_plot(self):
        if self.dw_plot_draft.isVisible():
            self._make_draft_time_plot_visible(False)
        else:
            self._make_draft_time_plot_visible(True)

        self.refresh_plots()

    @QtCore.Slot()
    def on_view_depth_time_plot(self):
        if self.dw_plot_depth.isVisible():
            self._make_depth_time_plot_visible(False)
        else:
            self._make_depth_time_plot_visible(True)

        self.refresh_plots()

    @QtCore.Slot()
    def on_view_info_viewer(self):
        if self.dw_info_viewer.isVisible():
            self._make_info_viewer_visible(False)
        else:
            self._make_info_viewer_visible(True)

        self.refresh_plots()

    @QtCore.Slot()
    def on_view_estimation_viewer(self):
        if self.dw_estimation_viewer.isVisible():
            self._make_estimation_viewer_visible(False)
        else:
            self._make_estimation_viewer_visible(True)

        self.refresh_plots()

    @QtCore.Slot()
    def on_view_options(self):

        if hasattr(self.main_win, "switch_to_monitor_tab"):
            self.main_win.switch_to_monitor_tab()

        if self.options_dialog.isVisible():
            self.options_dialog.setHidden(True)
        else:
            self.options_dialog.setHidden(False)

    def _make_tss_time_plot_visible(self, flag):
        if flag:
            self.dw_plot_tss.setVisible(True)
            self.view_tss_time_plot_action.setChecked(True)
        else:
            self.dw_plot_tss.setVisible(False)
            self.view_tss_time_plot_action.setChecked(False)

    def _make_draft_time_plot_visible(self, flag):
        if flag:
            self.dw_plot_draft.setVisible(True)
            self.view_draft_time_plot_action.setChecked(True)
        else:
            self.dw_plot_draft.setVisible(False)
            self.view_draft_time_plot_action.setChecked(False)

    def _make_depth_time_plot_visible(self, flag):

        if flag:
            self.dw_plot_depth.setVisible(True)
            self.view_depth_time_plot_action.setChecked(True)
        else:
            self.dw_plot_depth.setVisible(False)
            self.view_depth_time_plot_action.setChecked(False)

    def _make_info_viewer_visible(self, flag):

        if flag:
            self.dw_info_viewer.setVisible(True)
            self.view_info_viewer_action.setChecked(True)
        else:
            self.dw_info_viewer.setVisible(False)
            self.view_info_viewer_action.setChecked(False)

    def _make_estimation_viewer_visible(self, flag):

        if flag:
            self.dw_estimation_viewer.setVisible(True)
            self.view_estimation_viewer_action.setChecked(True)
        else:
            self.dw_estimation_viewer.setVisible(False)
            self.view_estimation_viewer_action.setChecked(False)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.Resize:
            self.refresh_plots()

        super().eventFilter(obj, event)
