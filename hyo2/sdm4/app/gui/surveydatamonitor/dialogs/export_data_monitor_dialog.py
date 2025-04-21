import logging
from typing import Optional, TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from hyo2.ssm2.app.gui.soundspeedmanager.dialogs.dialog import AbstractDialog

if TYPE_CHECKING:
    from hyo2.ssm2.lib.soundspeed import SoundSpeedLibrary
    from hyo2.sdm4.lib.monitor import SurveyDataMonitor

logger = logging.getLogger(__name__)


class ExportDataMonitorDialog(AbstractDialog):

    def __init__(self, main_win: QtWidgets.QWidget, lib: 'SoundSpeedLibrary', monitor: 'SurveyDataMonitor',
                 parent: Optional[QtWidgets.QWidget] = None):
        AbstractDialog.__init__(self, main_win=main_win, lib=lib, parent=parent)
        self._monitor = monitor

        # the list of selected writers passed to the library
        self.selected_writers = list()

        self.setWindowTitle("Survey Data Monitor")
        self.setMinimumWidth(160)

        settings = QtCore.QSettings()

        # outline ui
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        # label
        hbox = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(hbox)
        hbox.addStretch()
        label = QtWidgets.QLabel("Select output formats:")
        hbox.addWidget(label)
        hbox.addStretch()
        # buttons
        hbox = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(hbox)
        hbox.addStretch()
        # - fmt layout
        self.fmtLayout = QtWidgets.QHBoxLayout()
        hbox.addLayout(self.fmtLayout)
        # -- left
        self.leftButtonBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Orientation.Vertical)
        self.leftButtonBox.setFixedWidth(100)
        self.fmtLayout.addWidget(self.leftButtonBox)
        # -- right
        self.rightButtonBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Orientation.Vertical)
        self.rightButtonBox.setFixedWidth(100)
        self.fmtLayout.addWidget(self.rightButtonBox)
        hbox.addStretch()
        # add buttons (retrieving name, description and extension from the library)
        for idx, name in enumerate(["shapefile", "kml", "csv", "geotiff"]):

            btn = QtWidgets.QPushButton("%s" % name)
            btn.setCheckable(True)
            btn.setToolTip("Select %s format" % name)

            btn_settings = settings.value("export_monitor_%s" % name)
            if btn_settings is None:
                settings.setValue("export_monitor_%s" % name, False)
            if settings.value("export_monitor_%s" % name) == 'true':
                btn.setChecked(True)
                self.selected_writers.append(name)

            if (idx % 2) == 0:
                self.leftButtonBox.addButton(btn, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
            else:
                self.rightButtonBox.addButton(btn, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)

        # noinspection PyUnresolvedReferences
        self.leftButtonBox.clicked.connect(self.on_select_writer_btn)
        # noinspection PyUnresolvedReferences
        self.rightButtonBox.clicked.connect(self.on_select_writer_btn)

        self.mainLayout.addSpacing(16)

        # option for opening the output folder
        export_open_folder = settings.value("export_open_folder")
        if export_open_folder is None:
            settings.setValue("export_open_folder", True)
        hbox = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(hbox)
        hbox.addStretch()
        self.openFolder = QtWidgets.QCheckBox('Open output folder', self)
        self.openFolder.setChecked(settings.value("export_open_folder") == 'true')
        hbox.addWidget(self.openFolder)
        hbox.addStretch()

        # export
        hbox = QtWidgets.QHBoxLayout()
        self.mainLayout.addLayout(hbox)
        hbox.addStretch()
        btn = QtWidgets.QPushButton("Export data")
        btn.setMinimumHeight(32)
        hbox.addWidget(btn)
        # noinspection PyUnresolvedReferences
        btn.clicked.connect(self.on_export_data_btn)
        hbox.addStretch()

    def on_select_writer_btn(self, btn):
        """Update the list of writers to pass to the library"""
        name = btn.text()
        logger.debug("%s -> %s" % (name, btn.isChecked()))

        settings = QtCore.QSettings()

        if btn.isChecked():
            self.selected_writers.append(name)
            settings.setValue("export_monitor_%s" % name, True)

        else:
            settings.setValue("export_monitor_%s" % name, False)
            if name in self.selected_writers:
                self.selected_writers.remove(name)

    def on_export_data_btn(self):
        logger.debug("export profile clicked")

        if len(self.selected_writers) == 0:
            msg = "Select output formats before data export!"
            # noinspection PyCallByClass,PyTypeChecker
            QtWidgets.QMessageBox.warning(self, "Export warning", msg, QtWidgets.QMessageBox.StandardButton.Ok)
            return

        settings = QtCore.QSettings()

        # actually do the export
        self.progress.start()
        token = 80 / (len(self.selected_writers) + 1)
        try:
            for writer in self.selected_writers:
                self.progress.add(token, "Writing %s format" % writer)
                logger.debug(writer)

                if writer == "shapefile":
                    self._monitor.export_surface_speed_points_shapefile()

                elif writer == "kml":
                    self._monitor.export_surface_speed_points_kml()

                elif writer == "csv":
                    self._monitor.export_surface_speed_points_csv()

                elif writer == "geotiff":
                    self._monitor.export_surface_speed_points_geotiff()

                else:
                    raise RuntimeError("Unknown writer: %s" % writer)

        except Exception as e:
            self.progress.end()
            msg = "Issue in exporting the data.\nReason: %s" % e
            # noinspection PyCallByClass,PyTypeChecker
            QtWidgets.QMessageBox.critical(self, "Export error", msg, QtWidgets.QMessageBox.StandardButton.Ok)
            return

        # opening the output folder
        export_open_folder = self.openFolder.isChecked()
        settings.setValue("export_open_folder", export_open_folder)
        if export_open_folder:
            self._monitor.open_output_folder()  # open the output folder
            self.progress.end()

        else:
            self.progress.end()
            msg = "Data successfully exported!"
            # noinspection PyCallByClass
            QtWidgets.QMessageBox.information(self, "Survey Data Monitor", msg, QtWidgets.QMessageBox.StandardButton.Ok)

        self.accept()
