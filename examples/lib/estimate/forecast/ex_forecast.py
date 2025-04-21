import pyximport
pyximport.install()
import Cython.Compiler.Options
Cython.Compiler.Options.annotate = True

import logging
logger = logging.getLogger()

from hyo2.sdm4.lib.estimate.forecast.forecast import ForeCast

bfc = ForeCast()
logger.debug(bfc)
