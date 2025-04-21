import pyximport
pyximport.install()
import Cython.Compiler.Options
Cython.Compiler.Options.annotate = True

import logging

from hyo2.sdm4.lib.monitor import SurveyDataMonitor
from hyo2.ssm2.lib.soundspeed import SoundSpeedLibrary

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ssm = SoundSpeedLibrary()
monitor = SurveyDataMonitor(ssm=ssm)

# data = [1500, 1480, 1488, 1493, 1501]
# data = [1500, 1500, 1500, 1500, 1500]

# data = [1, 2, 3, 3, 4, 4, 4, 5, 5.5, 6, 6, 6.5, 7, 7, 7.5, 8, 9, 12, 52, 90]

# data = [1500, 1480, 1488, 1493, 1501, 1500, 1480, 1488, 1493, 1501, 1500, 1480, 1488, 1493, 1501,
#         1500, 1480, 1488, 1493, 1501, 1500, 1480, 1488, 1493, 1501, 1500, 1480, 1488, 1493, 1501]

data = [1510, 1499, 1496, 1496, 1500, 1500.3, 1498, 1498, 1499, 1500, 1500, 1499, 1498, 1497.5, 1500,
        1510, 1499, 1496, 1496, 1500, 1500, 1498, 1498.8, 1499, 1500, 1500, 1499, 1498, 1497.5, 1500]


min_plot_value, max_plot_value = monitor.calc_plot_good_range(data=data)
logger.debug("min: %s, max: %s" % (min_plot_value, max_plot_value))
