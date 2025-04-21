import time
import logging

from hyo2.ssm2.lib.soundspeed import SoundSpeedLibrary
from hyo2.sdm4.lib.monitor import SurveyDataMonitor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ssm = SoundSpeedLibrary()
monitor = SurveyDataMonitor(ssm=ssm)

monitor.start_monitor()
time.sleep(1)
monitor.pause_monitor()
time.sleep(1)
monitor.start_monitor()
time.sleep(1)
monitor.stop_monitor()

logger.debug(monitor)
