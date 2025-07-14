"""Test for Lock"""

from the_keyspy.devices.lock import TheKeysLock
from the_keyspy.devices.gateway import TheKeysGateway

import unittest


class TestLock(unittest.TestCase):
    def setUp(self) -> None:
        self.lock = TheKeysLock(1, TheKeysGateway(
            1, "0.0.0.0"), "home", "", "1234")

    def test_battery_level(self):
        self.lock._battery = 3600
        self.assertEqual(self.lock.battery_level, 0)
        self.lock._battery = 8000
        self.assertEqual(self.lock.battery_level, 100)
        self.lock._battery = 5800
        self.assertEqual(self.lock.battery_level, 50)
