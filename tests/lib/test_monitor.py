import unittest

from hyo2.sdm4.lib.monitor import SurveyDataMonitor
from hyo2.ssm2.lib.soundspeed import SoundSpeedLibrary


class TestSurveyDataMonitor(unittest.TestCase):

    def test_init(self):
        ssm = SoundSpeedLibrary()
        sdm = SurveyDataMonitor(ssm=ssm)


def suite():
    s = unittest.TestSuite()
    s.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSurveyDataMonitor))
    return s
