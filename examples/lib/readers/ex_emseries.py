import pyximport
pyximport.install()
import Cython.Compiler.Options
Cython.Compiler.Options.annotate = True

import logging
import os

from hyo2.abc2.lib.testing import Testing
from hyo2.sdm4.lib.readers.emseries import EmSeries

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
testing = Testing(root_folder=data_folder)

all_files = testing.download_test_files(".all")
kng = EmSeries(file_input=all_files[0])
logger.debug(kng)
