"""Test for TheKeyApi"""
from unittest import TestCase

from the_keyspy import TheKeyApi


class TheKeyApiTest(TestCase):
    """The KeysApi test class"""

    def test(self):
        controller = TheKeyApi('http://192.168.1.84', '')
        controller.retrieve_lock()
