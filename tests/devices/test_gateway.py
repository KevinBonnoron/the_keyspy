"""Tests for TheKeysGateway, especially the resync+retry on code 38."""
import unittest

from flask import jsonify
from http_server_mock import HttpServerMock

from the_keyspy.devices.gateway import TheKeysGateway
from the_keyspy.errors import GatewayTimeInvalidError


GATEWAY_HOST = "127.0.0.1:5001"
IDENTIFIER = "identifier"
SHARE_CODE = "share_code"


def _ok_locker_status_payload():
    return {
        "status": "Door open",
        "code": 1,
        "id": 1,
        "version": 81,
        "position": 20,
        "rssi": 0,
        "battery": 7235,
    }


def _gateway_time_invalid_payload():
    return {
        "status": "ko",
        "code": 38,
        "cause": "Gateway time is invalid. Should resynchronize",
    }


class TestGatewayActionRetry(unittest.TestCase):
    def setUp(self) -> None:
        self.app = HttpServerMock(__name__)
        self.locker_status_calls = 0
        self.synchronize_calls = 0
        self.gateway = TheKeysGateway(1, GATEWAY_HOST)

    def _register_synchronize(self, payload=None):
        """Register the /synchronize endpoint; counts calls."""
        if payload is None:
            payload = {"status": "ok"}

        def synchronize():
            self.synchronize_calls += 1
            return jsonify(payload)

        self.app.add_url_rule(
            "/synchronize", "synchronize", view_func=synchronize, methods=["GET", "POST"]
        )

    def test_locker_status_nominal_no_retry(self):
        def locker_status():
            self.locker_status_calls += 1
            return jsonify(_ok_locker_status_payload())

        self._register_synchronize()
        self.app.add_url_rule(
            "/locker_status", None, view_func=locker_status, methods=["POST"]
        )

        with self.app.run("127.0.0.1", 5001):
            result = self.gateway.locker_status(IDENTIFIER, SHARE_CODE)

        self.assertEqual(result["code"], 1)
        self.assertEqual(self.locker_status_calls, 1)
        self.assertEqual(self.synchronize_calls, 0)

    def test_locker_status_code_38_resync_then_success(self):
        def locker_status():
            self.locker_status_calls += 1
            if self.locker_status_calls == 1:
                return jsonify(_gateway_time_invalid_payload())
            return jsonify(_ok_locker_status_payload())

        self._register_synchronize()
        self.app.add_url_rule(
            "/locker_status", None, view_func=locker_status, methods=["POST"]
        )

        with self.app.run("127.0.0.1", 5001):
            result = self.gateway.locker_status(IDENTIFIER, SHARE_CODE)

        self.assertEqual(result["code"], 1)
        self.assertEqual(self.locker_status_calls, 2)
        self.assertEqual(self.synchronize_calls, 1)

    def test_locker_status_code_38_persists_after_retry(self):
        def locker_status():
            self.locker_status_calls += 1
            return jsonify(_gateway_time_invalid_payload())

        self._register_synchronize()
        self.app.add_url_rule(
            "/locker_status", None, view_func=locker_status, methods=["POST"]
        )

        with self.app.run("127.0.0.1", 5001):
            with self.assertRaises(GatewayTimeInvalidError) as ctx:
                self.gateway.locker_status(IDENTIFIER, SHARE_CODE)

        self.assertEqual(ctx.exception.response_data["code"], 38)
        # Exactly one retry, no infinite loop
        self.assertEqual(self.locker_status_calls, 2)
        self.assertEqual(self.synchronize_calls, 1)
        # Backward compat with the previous RuntimeError contract
        self.assertIsInstance(ctx.exception, RuntimeError)

    def test_synchronize_returning_code_38_does_not_retry(self):
        """If /synchronize itself returns code 38, we must NOT recurse."""
        def synchronize():
            self.synchronize_calls += 1
            return jsonify(_gateway_time_invalid_payload())

        self.app.add_url_rule(
            "/synchronize", None, view_func=synchronize, methods=["GET", "POST"]
        )

        with self.app.run("127.0.0.1", 5001):
            with self.assertRaises(GatewayTimeInvalidError):
                self.gateway.synchronize()

        # Called exactly once — no retry on SYNCHRONIZE itself
        self.assertEqual(self.synchronize_calls, 1)
