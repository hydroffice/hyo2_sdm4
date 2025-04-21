import logging

from PySide6 import QtCore, QtGui, QtWidgets

from hyo2.abc2.app.qt_progress import QtProgress
from hyo2.sdm4.lib.monitor import SurveyDataMonitor
from hyo2.ssm2.app.gui.soundspeedmanager.dialogs.dialog import AbstractDialog

logger = logging.getLogger(__name__)


class MonitorOption(AbstractDialog):

    def __init__(self, main_win, lib, monitor, parent=None):
        AbstractDialog.__init__(self, main_win=main_win, lib=lib, parent=parent)
        if not isinstance(monitor, SurveyDataMonitor):
            raise RuntimeError("Passed invalid monitor object: %s" % type(lib))
        self._monitor = monitor

        self.setWindowTitle("Survey Data Monitor Options")
        self.setMinimumWidth(300)

        # outline ui
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)
        self._tabs = QtWidgets.QTabWidget()
        self.mainLayout.addWidget(self._tabs)

        double_validator = QtGui.QDoubleValidator(0, 10000, 4, self)

        settings = QtCore.QSettings()

        # ### general options ###

        general_options = QtWidgets.QWidget(self)
        general_main_layout = QtWidgets.QVBoxLayout()
        general_options.setLayout(general_main_layout)
        self._tabs.addTab(general_options, "General")

        general_main_layout.addSpacing(12)

        # label
        hbox = QtWidgets.QHBoxLayout()
        general_main_layout.addLayout(hbox)
        hbox.addStretch()
        self.active_estimator_label = QtWidgets.QLabel("<i>Active Estimator</i>")
        hbox.addWidget(self.active_estimator_label)
        hbox.addStretch()
        # button group
        self.active_estimator = QtWidgets.QButtonGroup()
        # disabled
        hbox = QtWidgets.QHBoxLayout()
        general_main_layout.addLayout(hbox)
        hbox.addSpacing(30)
        none_estimator = QtWidgets.QRadioButton("None")
        self.active_estimator.addButton(none_estimator)
        hbox.addWidget(none_estimator)
        hbox.addStretch()
        # cast time
        hbox = QtWidgets.QHBoxLayout()
        general_main_layout.addLayout(hbox)
        hbox.addSpacing(30)
        casttime_estimator = QtWidgets.QRadioButton("CastTime")
        self.active_estimator.addButton(casttime_estimator)
        hbox.addWidget(casttime_estimator)
        hbox.addStretch()
        # noinspection PyUnresolvedReferences
        self.active_estimator.buttonClicked.connect(self.on_active_estimator_changed)

        general_main_layout.addSpacing(12)

        hbox = QtWidgets.QHBoxLayout()
        general_main_layout.addLayout(hbox)
        hbox.addStretch()
        self.time_intervals_label = QtWidgets.QLabel("<i>Default Values</i>")
        hbox.addWidget(self.time_intervals_label)
        hbox.addStretch()

        # draft
        hbox = QtWidgets.QHBoxLayout()
        general_main_layout.addLayout(hbox)
        hbox.addStretch()
        # label
        self.default_draft_label = QtWidgets.QLabel("Transducer Draft [m]:")
        self.default_draft_label.setFixedWidth(150)
        hbox.addWidget(self.default_draft_label)
        # input value
        self.default_draft = QtWidgets.QLineEdit()
        self.default_draft.setFixedWidth(60)
        self.default_draft.setValidator(double_validator)
        # noinspection PyUnresolvedReferences
        self.default_draft.textEdited.connect(self.on_default_draft_changed)
        hbox.addWidget(self.default_draft)
        hbox.addStretch()

        # avg depth
        hbox = QtWidgets.QHBoxLayout()
        general_main_layout.addLayout(hbox)
        hbox.addStretch()
        # label
        self.avg_depth_label = QtWidgets.QLabel("Average Depth [m]:")
        self.avg_depth_label.setFixedWidth(150)
        hbox.addWidget(self.avg_depth_label)
        # input value
        self.avg_depth = QtWidgets.QLineEdit()
        self.avg_depth.setFixedWidth(60)
        self.avg_depth.setValidator(double_validator)
        # noinspection PyUnresolvedReferences
        self.avg_depth.textEdited.connect(self.on_avg_depth_changed)
        hbox.addWidget(self.avg_depth)
        hbox.addStretch()

        general_main_layout.addSpacing(12)

        # plot analysis
        hbox = QtWidgets.QHBoxLayout()
        general_main_layout.addLayout(hbox)
        hbox.addStretch()
        # label
        self.plot_analysis = QtWidgets.QCheckBox("Plot analysis")
        self.plot_analysis.setFixedWidth(80)
        hbox.addWidget(self.plot_analysis)
        # noinspection PyUnresolvedReferences
        self.plot_analysis.stateChanged.connect(self.on_plot_analysis_changed)
        hbox.addWidget(self.plot_analysis)
        hbox.addStretch()

        general_main_layout.addStretch()

        # ### cast time options ###

        casttime_options = QtWidgets.QWidget(self)
        casttime_main_layout = QtWidgets.QVBoxLayout()
        casttime_options.setLayout(casttime_main_layout)
        self.casttime_tab_idx = self._tabs.addTab(casttime_options, "CastTime")
        # logger.debug("casttime idx: %d" % self.casttime_tab_idx)

        casttime_main_layout.addStretch()

        casttime_main_layout.addSpacing(12)

        hbox = QtWidgets.QHBoxLayout()
        casttime_main_layout.addLayout(hbox)
        hbox.addStretch()
        self.time_intervals_label = QtWidgets.QLabel("<i>Time Intervals</i>")
        hbox.addWidget(self.time_intervals_label)
        hbox.addStretch()

        # initial interval
        hbox = QtWidgets.QHBoxLayout()
        casttime_main_layout.addLayout(hbox)
        hbox.addStretch()
        # label
        self.initial_interval_label = QtWidgets.QLabel("Initial interval [min]:")
        self.initial_interval_label.setFixedWidth(150)
        hbox.addWidget(self.initial_interval_label)
        # input value
        self.initial_interval = QtWidgets.QLineEdit()
        self.initial_interval.setFixedHeight(20)
        self.initial_interval.setFixedWidth(60)
        self.initial_interval.setValidator(double_validator)
        # noinspection PyUnresolvedReferences
        self.initial_interval.textEdited.connect(self.on_casttime_options_changed)
        hbox.addWidget(self.initial_interval)
        hbox.addStretch()

        # minimum interval
        hbox = QtWidgets.QHBoxLayout()
        casttime_main_layout.addLayout(hbox)
        hbox.addStretch()
        # label
        self.minimum_interval_label = QtWidgets.QLabel("Minimum interval [min]:")
        self.minimum_interval_label.setFixedWidth(150)
        hbox.addWidget(self.minimum_interval_label)
        # input value
        self.minimum_interval = QtWidgets.QLineEdit()
        self.minimum_interval.setFixedHeight(20)
        self.minimum_interval.setFixedWidth(60)
        self.minimum_interval.setValidator(double_validator)
        # noinspection PyUnresolvedReferences
        self.minimum_interval.textEdited.connect(self.on_casttime_options_changed)
        hbox.addWidget(self.minimum_interval)
        hbox.addStretch()

        # maximum interval
        hbox = QtWidgets.QHBoxLayout()
        casttime_main_layout.addLayout(hbox)
        hbox.addStretch()
        # label
        self.maximum_interval_label = QtWidgets.QLabel("Maximum interval [min]:")
        self.maximum_interval_label.setFixedWidth(150)
        hbox.addWidget(self.maximum_interval_label)
        # input value
        self.maximum_interval = QtWidgets.QLineEdit()
        self.maximum_interval.setFixedHeight(20)
        self.maximum_interval.setFixedWidth(60)
        self.maximum_interval.setValidator(double_validator)
        # noinspection PyUnresolvedReferences
        self.maximum_interval.textEdited.connect(self.on_casttime_options_changed)
        hbox.addWidget(self.maximum_interval)
        hbox.addStretch()

        casttime_main_layout.addSpacing(12)

        # Sonar info

        hbox = QtWidgets.QHBoxLayout()
        casttime_main_layout.addLayout(hbox)
        hbox.addStretch()
        self.sonar_info_label = QtWidgets.QLabel("<i>Sonar Info</i>")
        hbox.addWidget(self.sonar_info_label)
        hbox.addStretch()

        # half swath angle
        hbox = QtWidgets.QHBoxLayout()
        casttime_main_layout.addLayout(hbox)
        hbox.addStretch()
        # label
        self.half_swath_angle_label = QtWidgets.QLabel("Half Swath Angle [deg]:")
        self.half_swath_angle_label.setFixedWidth(150)
        hbox.addWidget(self.half_swath_angle_label)
        # input value
        self.half_swath_angle = QtWidgets.QLineEdit()
        self.half_swath_angle.setFixedHeight(20)
        self.half_swath_angle.setFixedWidth(60)
        self.half_swath_angle.setValidator(double_validator)
        # noinspection PyUnresolvedReferences
        self.half_swath_angle.textEdited.connect(self.on_casttime_options_changed)
        hbox.addWidget(self.half_swath_angle)
        hbox.addStretch()

        casttime_main_layout.addSpacing(12)

        # Allowable error

        hbox = QtWidgets.QHBoxLayout()
        casttime_main_layout.addLayout(hbox)
        hbox.addStretch()
        self.allowable_error_label = QtWidgets.QLabel("<i>Allowable Error</i>")
        hbox.addWidget(self.allowable_error_label)
        hbox.addStretch()

        # fixed component
        hbox = QtWidgets.QHBoxLayout()
        casttime_main_layout.addLayout(hbox)
        hbox.addStretch()
        # label
        self.fixed_allowable_error_label = QtWidgets.QLabel("Fixed component [m]:")
        self.fixed_allowable_error_label.setFixedWidth(150)
        hbox.addWidget(self.fixed_allowable_error_label)
        # input value
        self.fixed_allowable_error = QtWidgets.QLineEdit()
        self.fixed_allowable_error.setFixedHeight(20)
        self.fixed_allowable_error.setFixedWidth(60)
        self.fixed_allowable_error.setValidator(double_validator)
        # noinspection PyUnresolvedReferences
        self.fixed_allowable_error.textEdited.connect(self.on_casttime_options_changed)
        hbox.addWidget(self.fixed_allowable_error)
        hbox.addStretch()

        # variable component
        hbox = QtWidgets.QHBoxLayout()
        casttime_main_layout.addLayout(hbox)
        hbox.addStretch()
        # label
        self.variable_allowable_error_label = QtWidgets.QLabel("Percentage of depth [%]:")
        self.variable_allowable_error_label.setFixedWidth(150)
        hbox.addWidget(self.variable_allowable_error_label)
        # input value
        self.variable_allowable_error = QtWidgets.QLineEdit()
        self.variable_allowable_error.setFixedHeight(20)
        self.variable_allowable_error.setFixedWidth(60)
        self.variable_allowable_error.setValidator(double_validator)
        # noinspection PyUnresolvedReferences
        self.variable_allowable_error.textEdited.connect(self.on_casttime_options_changed)
        hbox.addWidget(self.variable_allowable_error)
        hbox.addStretch()

        casttime_main_layout.addSpacing(18)

        # apply button
        hbox = QtWidgets.QHBoxLayout()
        casttime_main_layout.addLayout(hbox)
        hbox.addStretch()
        # button
        self.casttime_recalculate_button = QtWidgets.QPushButton("Recalculate Now")
        self.casttime_recalculate_button.setFixedWidth(120)
        # noinspection PyUnresolvedReferences
        self.casttime_recalculate_button.clicked.connect(self.on_casttime_recalculate)
        hbox.addWidget(self.casttime_recalculate_button)
        hbox.addStretch()

        casttime_main_layout.addSpacing(12)

        # ### view options ###

        view_options = QtWidgets.QWidget(self)
        options_main_layout = QtWidgets.QVBoxLayout()
        view_options.setLayout(options_main_layout)
        self._tabs.addTab(view_options, "Plots")

        options_main_layout.addSpacing(12)

        # label
        hbox = QtWidgets.QHBoxLayout()
        options_main_layout.addLayout(hbox)
        hbox.addStretch()
        self.max_samples_label = QtWidgets.QLabel("<i>Plot latest samples</i>")
        hbox.addWidget(self.max_samples_label)
        hbox.addStretch()
        # slider
        hbox = QtWidgets.QHBoxLayout()
        options_main_layout.addLayout(hbox)
        hbox.addStretch()
        self.max_samples = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self)
        self.max_samples.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.max_samples.setSingleStep(1)
        self.max_samples.setTickInterval(1000)
        self.max_samples.setMinimum(1)
        self.max_samples.setMaximum(10000)
        self.max_samples.setMinimumWidth(260)
        self.max_samples.setValue(self.main_win.plotting_samples)
        self.max_samples_label.setText("<i>Plot latest %d samples</i>" % self.max_samples.value())
        # noinspection PyUnresolvedReferences
        self.max_samples.valueChanged.connect(self.on_max_samples_changed)
        hbox.addWidget(self.max_samples)
        hbox.addStretch()

        options_main_layout.addSpacing(18)

        # label
        hbox = QtWidgets.QHBoxLayout()
        options_main_layout.addLayout(hbox)
        hbox.addStretch()
        self.active_estimator_label = QtWidgets.QLabel("<i>Initial Plotted Area</i>")
        hbox.addWidget(self.active_estimator_label)
        hbox.addStretch()
        # button group
        self.initial_area = QtWidgets.QButtonGroup()
        initial_area_value = settings.value("monitor/initial_area", "World")
        settings.setValue("monitor/initial_area", initial_area_value)
        # world
        hbox = QtWidgets.QHBoxLayout()
        options_main_layout.addLayout(hbox)
        hbox.addSpacing(30)
        world_area = QtWidgets.QRadioButton("World")
        self.initial_area.addButton(world_area)
        world_area.setChecked(True)  # default
        hbox.addWidget(world_area)
        hbox.addStretch()
        # CONUS
        hbox = QtWidgets.QHBoxLayout()
        options_main_layout.addLayout(hbox)
        hbox.addSpacing(30)
        conus_area = QtWidgets.QRadioButton("Contiguous United States")
        self.initial_area.addButton(conus_area)
        if conus_area.text() == initial_area_value:
            conus_area.setChecked(True)
        hbox.addWidget(conus_area)
        hbox.addStretch()
        # Alaska
        hbox = QtWidgets.QHBoxLayout()
        options_main_layout.addLayout(hbox)
        hbox.addSpacing(30)
        alaska_area = QtWidgets.QRadioButton("Alaska")
        # alaska_area.setDisabled(True)
        self.initial_area.addButton(alaska_area)
        if alaska_area.text() == initial_area_value:
            alaska_area.setChecked(True)
        hbox.addWidget(alaska_area)
        # Hawaii
        hbox = QtWidgets.QHBoxLayout()
        options_main_layout.addLayout(hbox)
        hbox.addSpacing(30)
        hawaii_area = QtWidgets.QRadioButton("Hawaii")
        self.initial_area.addButton(hawaii_area)
        if hawaii_area.text() == initial_area_value:
            hawaii_area.setChecked(True)
        hbox.addWidget(hawaii_area)
        hbox.addStretch()
        # noinspection PyUnresolvedReferences
        self.initial_area.buttonClicked.connect(self.on_initial_area_changed)

        options_main_layout.addStretch()

        # initialization
        casttime_estimator.setChecked(True)
        self._tabs.setTabEnabled(self.casttime_tab_idx, True)

        # data-based initialization
        self._monitor.lock_data()
        self.default_draft.setText("%s" % self._monitor.default_draft)
        self.avg_depth.setText("%s" % self._monitor.avg_depth)
        self.plot_analysis.setChecked(self._monitor.casttime.plotting_mode)
        self.initial_interval.setText("%s" % self._monitor.casttime.current_interval)
        self.minimum_interval.setText("%s" % self._monitor.casttime.minimum_interval)
        self.maximum_interval.setText("%s" % self._monitor.casttime.maximum_interval)
        self.half_swath_angle.setText("%s" % self._monitor.casttime.half_swath_angle)
        self.fixed_allowable_error.setText("%s" % self._monitor.casttime.fixed_allowable_error)
        self.variable_allowable_error.setText("%s" % self._monitor.casttime.variable_allowable_error)
        self._monitor.unlock_data()

    @QtCore.Slot()
    def on_active_estimator_changed(self, idx):
        button_label = idx.text()
        logger.debug("active estimator changed: %s" % button_label)

        if button_label == "None":

            self._tabs.setTabEnabled(self.casttime_tab_idx, False)
            self._monitor.disable_estimation()

        elif button_label == "CastTime":

            self._tabs.setTabEnabled(self.casttime_tab_idx, True)
            self._monitor.activate_casttime()

        else:
            raise RuntimeError("Unknown estimator: %s" % button_label)

    @QtCore.Slot()
    def on_default_draft_changed(self, _):
        logger.debug("Default draft changed")
        self._monitor.lock_data()
        self._monitor.casttime.default_draft = float(self.default_draft.text())
        self._monitor.unlock_data()

    @QtCore.Slot()
    def on_avg_depth_changed(self, _):
        logger.debug("Average depth changed")
        self._monitor.lock_data()
        self._monitor.casttime.avg_depth = float(self.avg_depth.text())
        self._monitor.unlock_data()

    @QtCore.Slot()
    def on_plot_analysis_changed(self, _):
        logger.debug("Plot analysis changed")
        self._monitor.lock_data()
        self._monitor.casttime.plotting_mode = self.plot_analysis.isChecked()
        self._monitor.unlock_data()

    @QtCore.Slot()
    def on_casttime_options_changed(self, _):
        logger.debug("CastTime options changed")

        self._monitor.lock_data()
        self._monitor.casttime.current_interval = float(self.initial_interval.text())
        self._monitor.casttime.minimum_interval = float(self.minimum_interval.text())
        self._monitor.casttime.maximum_interval = float(self.maximum_interval.text())
        self._monitor.casttime.half_swath_angle = float(self.half_swath_angle.text())
        self._monitor.casttime.fixed_allowable_error = float(self.fixed_allowable_error.text())
        self._monitor.casttime.variable_allowable_error = float(self.variable_allowable_error.text())
        self._monitor.unlock_data()

    @QtCore.Slot()
    def on_casttime_recalculate(self):
        logger.debug("CastTime recalculate")

        progress = QtProgress(parent=self)
        progress.start(title="Recalculation")

        self._monitor.lock_data()
        progress.update(value=20)
        self._monitor.casttime.recalculate()
        self._monitor.unlock_data()

        progress.update(value=80)
        self._monitor.lock_data()
        if self._monitor.casttime.plotting_mode:
            self._monitor.casttime.plotting_analysis(self._monitor.current_time)
        self._monitor.unlock_data()
        logger.debug("******")
        progress.end()
        logger.debug("**")

    @QtCore.Slot()
    def on_max_samples_changed(self):
        self.main_win.plotting_samples = self.max_samples.value()
        self.max_samples_label.setText("Plot latest %d samples:" % self.max_samples.value())
        logger.debug(self.main_win.plotting_samples)
        self.main_win.update_plot_data()

    @QtCore.Slot()
    def on_initial_area_changed(self, idx):
        self.main_win.set_initial_plot_area(idx.text())
