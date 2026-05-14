from .base import TheKeysDevice
import base64
import hmac
import time
import requests
from enum import Enum
from typing import Any, Optional

import logging

from ..errors import GatewayTimeInvalidError

logger = logging.getLogger("the_keyspy.devices.gateway")

GATEWAY_TIME_INVALID_CODE = 38


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

    def __str__(self):
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
        return self.action(Action.UPDATE)["status"] == "ok"

    def synchronize(self) -> bool:
        return self.action(Action.SYNCHRONIZE)["status"] == "ok"

    # Locker actions
    def locker_open(self, identifier: str, share_code: str) -> bool:
        return self.action(Action.LOCKER_OPEN, identifier, share_code)["status"] == "ok"

    def locker_close(self, identifier: str, share_code: str) -> bool:
        return self.action(Action.LOCKER_CLOSE, identifier, share_code)["status"] == "ok"

    def locker_calibrate(self, identifier: str, share_code: str) -> bool:
        return self.action(Action.LOCKER_CALIBRATE, identifier, share_code)["status"] == "ok"

    def locker_status(self, identifier: str, share_code: str) -> Any:
        return self.action(Action.LOCKER_STATUS, identifier, share_code)

    def locker_synchronize(self, identifier: str, share_code: str) -> bool:
        return self.action(Action.LOCKER_SYNCHRONIZE, identifier, share_code)["status"] == "ok"

    def locker_update(self, identifier: str, share_code: str) -> bool:
        return self.action(Action.LOCKER_UPDATE, identifier, share_code)["status"] == "ok"

    # Common actions
    def action(self, action: Action, identifier: str = "", share_code: str = "") -> Any:
        return self._action(action, identifier, share_code, retried=False)

    def _action(self, action: Action, identifier: str, share_code: str, retried: bool) -> Any:
        data: dict = {}
        if identifier != "":
            data["identifier"] = identifier

        if share_code != "":
            timestamp = str(int(time.time()))
            data["ts"] = timestamp
            data["hash"] = base64.b64encode(hmac.new(share_code.encode(
                "ascii"), timestamp.encode("ascii"), "sha256").digest())

        url = "status"
        match action:
            case Action.STATUS:
                url = "status"
            case Action.UPDATE:
                url = "update"
                data = {"fake": True}
            case Action.SYNCHRONIZE:
                url = "synchronize"
            case Action.LOCKER_OPEN:
                url = "open"
            case Action.LOCKER_CLOSE:
                url = "close"
            case Action.LOCKER_CALIBRATE:
                url = "calibrate"
            case Action.LOCKER_STATUS:
                url = "locker_status"
            case Action.LOCKER_SYNCHRONIZE:
                url = "locker/synchronize"
            case Action.LOCKER_UPDATE:
                url = "locker/update"

        response_data = self.__http_request(url, data)
        if "status" not in response_data:
            response_data["status"] = "ok"

        if response_data["status"] == "ko":
            if (
                response_data.get("code") == GATEWAY_TIME_INVALID_CODE
                and action is not Action.SYNCHRONIZE
                and not retried
            ):
                logger.warning(
                    "Gateway time invalid (code %s); resynchronizing and retrying %s",
                    GATEWAY_TIME_INVALID_CODE, action,
                )
                self.synchronize()
                retry_response = self._action(action, identifier, share_code, retried=True)
                return retry_response

            if response_data.get("code") == GATEWAY_TIME_INVALID_CODE:
                raise GatewayTimeInvalidError(response_data)
            raise RuntimeError(response_data)

        return response_data

    def __http_request(self, url: str, data: Optional[dict] = None) -> Any:
        method = "post" if data else "get"
        logger.debug("%s %s", method.upper(), url)
        try:
            with requests.Session() as session:
                full_url = f"http://{self._host}/{url}"
                response = session.post(
                    full_url, data=data) if method == "post" else session.get(full_url)
                logger.debug("response_data: %s", response.json())
                return response.json()
        except ConnectionError as error:
            raise error
