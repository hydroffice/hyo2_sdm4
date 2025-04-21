import logging
from abc import ABCMeta
from enum import Enum

logger = logging.getLogger(__name__)


class EstimatorType(Enum):
    DISABLED = 0
    CAST_TIME = 1


class EstimationModes(Enum):
    UNKNOWN = 0
    RELAX = 1
    STEADY = 2
    PANIC = 3


class AbstractEstimator(metaclass=ABCMeta):

    def __init__(self):
        self._type = EstimatorType.DISABLED

    def __repr__(self):
        msg = "<%s>\n" % self.__class__.__name__

        msg += "  <type: %s>" % self._type

        return msg
