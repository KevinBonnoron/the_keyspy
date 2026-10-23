"""TheKeys gateway device implementation."""
import base64
import hmac
import logging
import time
from enum import Enum
from typing import Any, Optional, cast

import requests

from ..errors import (
    GatewayTimeInvalidError,
    GatewayUnreachableError,
    LockerSyncError,
)
from .base import TheKeysDevice

logger = logging.getLogger("the_keyspy.devices.gateway")

GATEWAY_TIME_INVALID_CODE = 38

# Codes returned when the gateway-to-lock BLE relay fails. Transient in
# practice (codes oscillate between runs), so we retry with backoff.
LOCKER_SYNC_ERROR_CODES = frozenset({1, 2, 3, 4, 5})

# Per-attempt backoffs in seconds; len defines the max retry count.
# Total worst-case sleep is sum(SYNC_BACKOFFS_SECONDS) before raising.
SYNC_BACKOFFS_SECONDS = (1, 2, 4)

# (connect, read) timeouts in seconds. The BLE relay makes "normal" calls take
# ~3s; 15s read leaves headroom without exceeding the typical 30s polling cycle.
GATEWAY_HTTP_TIMEOUT = (5, 15)


class Action(Enum):
    """All available actions"""

    STATUS = "status"
    UPDATE = "update"
    SYNCHRONIZE = "synchronize"

    LOCKER_OPEN = "locker_open"
    LOCKER_CLOSE = "locker_close"
    LOCKER_CALIBRATE = "locker_calibrate"
    LOCKER_STATUS = "locker_status"
    LOCKER_SYNCHRONIZE = "locker_synchronize"
    LOCKER_UPDATE = "locker_update"

    def __str__(self) -> str:
        return self.value


class TheKeysGateway(TheKeysDevice):
    """Gateway device implementation"""

    def __init__(self, id: int, host: str) -> None:
        super().__init__(id)
        self._host = host

    # Gateway actions
    def status(self) -> Any:
        return self.action(Action.STATUS)

    def update(self) -> bool:
        return cast(bool, self.action(Action.UPDATE)["status"] == "ok")

    def synchronize(self) -> bool:
        return cast(bool, self.action(Action.SYNCHRONIZE)["status"] == "ok")

    # Locker actions
    def locker_open(self, identifier: str, share_code: str) -> bool:
        return cast(bool, self.action(Action.LOCKER_OPEN, identifier, share_code)["status"] == "ok")

    def locker_close(self, identifier: str, share_code: str) -> bool:
        return cast(bool, self.action(Action.LOCKER_CLOSE, identifier, share_code)["status"] == "ok")

    def locker_calibrate(self, identifier: str, share_code: str) -> bool:
        return cast(bool, self.action(Action.LOCKER_CALIBRATE, identifier, share_code)["status"] == "ok")

    def locker_status(self, identifier: str, share_code: str) -> Any:
        return self.action(Action.LOCKER_STATUS, identifier, share_code)

    def locker_synchronize(self, identifier: str, share_code: str) -> bool:
        return cast(bool, self.action(Action.LOCKER_SYNCHRONIZE, identifier, share_code)["status"] == "ok")

    def locker_update(self, identifier: str, share_code: str) -> bool:
        return cast(bool, self.action(Action.LOCKER_UPDATE, identifier, share_code)["status"] == "ok")

    # Common actions
    def action(self, action: Action, identifier: str = "", share_code: str = "") -> Any:
        return self._action(action, identifier, share_code, sync_attempt=0, time_resynced=False)

    _ACTION_URLS: dict = {
        Action.STATUS: "status",
        Action.UPDATE: "update",
        Action.SYNCHRONIZE: "synchronize",
        Action.LOCKER_OPEN: "open",
        Action.LOCKER_CLOSE: "close",
        Action.LOCKER_CALIBRATE: "calibrate",
        Action.LOCKER_STATUS: "locker_status",
        Action.LOCKER_SYNCHRONIZE: "locker/synchronize",
        Action.LOCKER_UPDATE: "locker/update",
    }

    def _action(
        self,
        action: Action,
        identifier: str,
        share_code: str,
        sync_attempt: int,
        time_resynced: bool,
    ) -> Any:
        data: dict = {}
        if identifier != "":
            data["identifier"] = identifier

        if share_code != "":
            timestamp = str(int(time.time()))
            data["ts"] = timestamp
            data["hash"] = base64.b64encode(hmac.new(share_code.encode(
                "ascii"), timestamp.encode("ascii"), "sha256").digest())

        url = self._ACTION_URLS[action]
        if action is Action.UPDATE:
            data = {"fake": True}

        response_data = self.__http_request(url, data)
        if "status" not in response_data:
            response_data["status"] = "ok"

        if response_data["status"] != "ko":
            return response_data

        code = response_data.get("code")

        # Code 38: one-shot gateway resync, then retry the original request.
        if (
            code == GATEWAY_TIME_INVALID_CODE
            and action is not Action.SYNCHRONIZE
            and not time_resynced
        ):
            logger.warning(
                "Gateway time invalid (code %s); resynchronizing and retrying %s",
                GATEWAY_TIME_INVALID_CODE, action,
            )
            self.synchronize()
            return self._action(action, identifier, share_code,
                                sync_attempt=sync_attempt, time_resynced=True)

        # Codes 1-5: BLE relay failed to talk to the lock. Transient, retry
        # the same call with backoff (codes oscillate between runs in practice).
        if code in LOCKER_SYNC_ERROR_CODES and sync_attempt < len(SYNC_BACKOFFS_SECONDS):
            backoff = SYNC_BACKOFFS_SECONDS[sync_attempt]
            logger.warning(
                "Locker sync failed (code %s) on %s; retry %s/%s in %ss",
                code, action, sync_attempt + 1, len(SYNC_BACKOFFS_SECONDS), backoff,
            )
            time.sleep(backoff)
            return self._action(action, identifier, share_code,
                                sync_attempt=sync_attempt + 1, time_resynced=time_resynced)

        # No more retries available, raise a typed error.
        if code == GATEWAY_TIME_INVALID_CODE:
            raise GatewayTimeInvalidError(response_data)
        if code in LOCKER_SYNC_ERROR_CODES:
            raise LockerSyncError(code, response_data)
        raise RuntimeError(response_data)

    def __http_request(self, url: str, data: Optional[dict] = None) -> Any:
        method = "post" if data else "get"
        logger.debug("%s %s", method.upper(), url)
        full_url = f"http://{self._host}/{url}"
        try:
            with requests.Session() as session:
                if method == "post":
                    response = session.post(full_url, data=data, timeout=GATEWAY_HTTP_TIMEOUT)
                else:
                    response = session.get(full_url, timeout=GATEWAY_HTTP_TIMEOUT)
                logger.debug("response_data: %s", response.json())
                return response.json()
        except (requests.Timeout, requests.ConnectionError) as error:
            raise GatewayUnreachableError(self._host, error) from error
