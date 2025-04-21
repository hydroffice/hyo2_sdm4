import logging
import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets

from hyo2.sdm4.app.gui.surveydatamonitor import app_info
from hyo2.sdm4.app.gui.surveydatamonitor.widgets.monitor import SurveyDataMonitor
from hyo2.ssm2.lib.soundspeed import SoundSpeedLibrary

logger = logging.getLogger(__name__)


class MainWin(QtWidgets.QMainWindow):

    # noinspection PyUnresolvedReferences
    def __init__(self):
        super(MainWin, self).__init__()
        self._ssm = SoundSpeedLibrary()

        logger.info("* > APP: initializing ...")

        # set the application name and the version
        self.name = app_info.app_name
        self.version = app_info.app_version
        self.setWindowTitle('%s v.%s' % (self.name, self.version))
        # noinspection PyArgumentList
        _app = QtCore.QCoreApplication.instance()
        _app.setApplicationName('%s' % self.name)
        _app.setOrganizationName("HydrOffice")
        _app.setOrganizationDomain("hydroffice.org")

        # set the minimum and the initial size
        self.setMinimumSize(640, 480)
        self.resize(980, 760)

        # set icons
        icon_info = QtCore.QFileInfo(app_info.app_icon_path)
        self.setWindowIcon(QtGui.QIcon(icon_info.absoluteFilePath()))
        if (sys.platform == 'win32') or (os.name == "nt"):  # is_windows()
            try:
                # This is needed to display the app icon on the taskbar on Windows 7
                import ctypes
                app_id = '%s v.%s' % (self.name, self.version)
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            except AttributeError as e:
                logger.debug("Unable to change app icon: %s" % e)

        # menu

        self.menu = self.menuBar()
        self.monitor_menu = self.menu.addMenu("Monitor")

        self._sdm_widget = SurveyDataMonitor(main_win=self, lib=self._ssm)
        self.setCentralWidget(self._sdm_widget)

    def closeEvent(self, event):
        logger.debug("closing")
        self._ssm.close()
        self._sdm_widget.stop_plotting()
        super().closeEvent(event)
