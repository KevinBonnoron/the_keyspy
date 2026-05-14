"""Tests for TheKeysGateway, especially the resync+retry on code 38."""
import unittest
from unittest.mock import MagicMock, patch

import requests
from flask import jsonify
from http_server_mock import HttpServerMock

from the_keyspy.devices.gateway import GATEWAY_HTTP_TIMEOUT, TheKeysGateway
from the_keyspy.errors import GatewayTimeInvalidError, GatewayUnreachableError

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

    def test_timeout_raises_gateway_unreachable(self) -> None:
        """A request timing out must surface as GatewayUnreachableError."""
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.post.side_effect = requests.Timeout("read timed out")

        with patch("the_keyspy.devices.gateway.requests.Session", return_value=mock_session):
            with self.assertRaises(GatewayUnreachableError) as ctx:
                self.gateway.locker_status(IDENTIFIER, SHARE_CODE)

        self.assertIsInstance(ctx.exception.original, requests.Timeout)
        self.assertEqual(ctx.exception.host, GATEWAY_HOST)

    def test_connection_refused_raises_gateway_unreachable(self) -> None:
        """Connection errors must surface as GatewayUnreachableError, not raw requests errors."""
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.post.side_effect = requests.ConnectionError("Connection refused")

        with patch("the_keyspy.devices.gateway.requests.Session", return_value=mock_session):
            with self.assertRaises(GatewayUnreachableError) as ctx:
                self.gateway.locker_status(IDENTIFIER, SHARE_CODE)

        self.assertIsInstance(ctx.exception.original, requests.ConnectionError)

    def test_http_request_passes_timeout_kwarg(self) -> None:
        """Nominal flow must forward timeout= to requests so it cannot hang forever."""
        mock_response = MagicMock()
        mock_response.json.return_value = _ok_locker_status_payload()
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.post.return_value = mock_response

        with patch("the_keyspy.devices.gateway.requests.Session", return_value=mock_session):
            self.gateway.locker_status(IDENTIFIER, SHARE_CODE)

        mock_session.post.assert_called_once()
        _, kwargs = mock_session.post.call_args
        self.assertEqual(kwargs.get("timeout"), GATEWAY_HTTP_TIMEOUT)

    def test_timeout_does_not_trigger_code_38_retry(self) -> None:
        """A timeout must not engage the code-38 resync path (which would double the wait)."""
        mock_response = MagicMock()
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        # First call (locker_status) times out; if a retry were triggered, the
        # second call would be /synchronize. We assert below it never happens.
        mock_session.post.side_effect = requests.Timeout("read timed out")
        mock_session.get.return_value = mock_response

        with patch("the_keyspy.devices.gateway.requests.Session", return_value=mock_session):
            with self.assertRaises(GatewayUnreachableError):
                self.gateway.locker_status(IDENTIFIER, SHARE_CODE)

        # Exactly one HTTP call total: the failing locker_status. No synchronize.
        self.assertEqual(mock_session.post.call_count, 1)
        self.assertEqual(mock_session.get.call_count, 0)

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
