import base64
import hmac
import time
import requests
from enum import Enum
from typing import Any


from .base import TheKeysDevice


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

        json = self.__http_post(url, data) if data else self.__http_get(url)
        if "status" not in json:
            json["status"] = "ok"

        if json["status"] == "ko":
            raise RuntimeError(json)

        return json

    def __http_post(self, url, data) -> Any:
        try:
            with requests.Session() as session:
                response = session.post(
                    f"http://{self._host}/{url}", data=data)
                return response.json()
        except ConnectionError as error:
            raise (error)

    def __http_get(self, url) -> Any:
        try:
            with requests.Session() as session:
                response = session.get(f"http://{self._host}/{url}")
                return response.json()
        except ConnectionError as error:
            raise (error)
