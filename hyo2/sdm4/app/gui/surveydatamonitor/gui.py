import logging
import sys
import traceback

from PySide6 import QtCore, QtWidgets

from hyo2.abc2.app.app_style.app_style import AppStyle
from hyo2.abc2.lib.logging import set_logging
from hyo2.sdm4.app.gui.surveydatamonitor.mainwin import MainWin

set_logging(ns_list=["hyo2.abc2", "hyo2.ssm2", "hyo2.sdm4"])
logger = logging.getLogger(__name__)


def qt_custom_handler(error_type, error_context, message):
    logger.info("Qt error: %s [%s] -> %s" % (str(error_type), str(error_context), message))

    for line in traceback.format_stack():
        logger.debug("- %s" % line.strip())


QtCore.qInstallMessageHandler(qt_custom_handler)


def gui():
    """Create the application and show the Sound Speed Manager gui"""

    logger.debug("Init app ...")
    app = QtWidgets.QApplication(sys.argv)
    AppStyle.apply(app=app)

    logger.debug("Init main win ...")
    main = MainWin()
    main.show()

    sys.exit(app.exec())
