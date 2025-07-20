from curses import meta
from .base import TheKeysDevice
import base64
import hmac
import time
import requests
from enum import Enum
from typing import Any, Optional

import logging

logger = logging.getLogger("the_keyspy.devices.gateway")


class Action(Enum):
    """All available actions"""

    OPEN = "open"
    CLOSE = "close"
    CALIBRATE = "calibrate"
    LOCKER_STATUS = "locker_status"
    SYNCHRONIZE_LOCKER = "synchronize_locker"
    UPDATE_LOCKER = "update_locker"
    STATUS = "status"
    UPDATE = "update"

    def __str__(self):
        return self.value


class TheKeysGateway(TheKeysDevice):
    """Gateway device implementation"""

    def __init__(self, id: int, host: str) -> None:
        super().__init__(id)
        self._host = host

    def open(self, identifier: str, share_code: str) -> bool:
        return self.action(Action.OPEN, identifier, share_code)["status"] == "ok"

    def close(self, identifier: str, share_code: str) -> bool:
        return self.action(Action.CLOSE, identifier, share_code)["status"] == "ok"

    def calibrate(self, identifier: str, share_code: str) -> bool:
        return self.action(Action.CALIBRATE, identifier, share_code)["status"] == "ok"

    def locker_status(self, identifier: str, share_code: str) -> Any:
        return self.action(Action.LOCKER_STATUS, identifier, share_code)

    def synchronize_locker(self, identifier: str) -> bool:
        return self.action(Action.SYNCHRONIZE_LOCKER, identifier)["status"] == "ok"

    def update_locker(self, identifier: str) -> bool:
        return self.action(Action.UPDATE_LOCKER, identifier)["status"] == "ok"

    def status(self) -> Any:
        return self.action(Action.STATUS)

    def update(self) -> Any:
        return self.action(Action.UPDATE)

    def action(self, action: Action, identifier: str = "", share_code: str = "") -> Any:
        data = {}
        if identifier != "":
            data["identifier"] = identifier

        if share_code != "":
            timestamp = str(int(time.time()))
            data["ts"] = timestamp
            data["hash"] = base64.b64encode(hmac.new(share_code.encode(
                "ascii"), timestamp.encode("ascii"), "sha256").digest())

        match action:
            case Action.OPEN:
                url = "open"
            case Action.CLOSE:
                url = "close"
            case Action.CALIBRATE:
                url = "calibrate"
            case Action.LOCKER_STATUS:
                url = "locker_status"
            case Action.SYNCHRONIZE_LOCKER:
                url = "locker/synchronize"
            case Action.UPDATE_LOCKER:
                url = "locker/update"
            case Action.UPDATE:
                url = "update"
            case Action.STATUS:
                url = "status"
            case _:
                url = "status"

        response_data = self.__http_request(url, data)
        if "status" not in response_data:
            response_data["status"] = "ok"

        if response_data["status"] == "ko":
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
