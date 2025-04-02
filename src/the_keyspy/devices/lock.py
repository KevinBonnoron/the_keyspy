"""The Keys lock device implementation"""
from typing import Any

from .base import TheKeysDevice
from .gateway import TheKeysGateway

OPENED = "Door open"
CLOSED = "Door closed"
JAMMED = "Door jammed"
UNKNOWN = ""


def _map(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


class TheKeysLock(TheKeysDevice):
    """Lock device implementation"""

    def __init__(self, id: int, gateway: TheKeysGateway, name: str, identifier: str, share_code: str) -> None:
        super().__init__(id)
        self._gateway = gateway
        self._name = name
        self._identifier = identifier
        self._share_code = share_code

        self._status = UNKNOWN
        self._code = 0
        self._version = 0
        self._position = 0
        self._rssi = 0
        self._battery = 0

    def open(self) -> bool:
        """Open this lock"""
        result = self._gateway.open(self._identifier, self._share_code)
        if result:
            self._status = OPENED
        else:
            self._status = JAMMED

        return result

    def close(self) -> bool:
        """Close this lock"""
        result = self._gateway.close(self._identifier, self._share_code)
        if result:
            self._status = CLOSED
        else:
            self._status = JAMMED

        return result

    def calibrate(self) -> bool:
        """Calibrate this lock"""
        return self._gateway.calibrate(self._identifier, self._share_code)

    def status(self) -> Any:
        """Return this lock status"""
        return self._gateway.locker_status(self._identifier, self._share_code)

    def synchronize(self) -> Any:
        return self._gateway.synchronize_locker(self._identifier)

    def update(self) -> Any:
        return self._gateway.update_locker(self._identifier)

    def retrieve_infos(self) -> None:
        json = self.status()
        if json["status"] == "ko":
            return

        self._status = json["status"]
        self._code = json["code"]
        self._version = json["version"]
        self._position = json["position"]
        self._rssi = json["rssi"]
        self._battery = json["battery"]

    @property
    def name(self) -> str:
        """This lock name"""
        return self._name

    @property
    def is_unlocked(self) -> bool:
        """Is this lock unlocked"""
        return self._status == OPENED

    @property
    def is_locked(self) -> bool:
        """Is this lock locked"""
        return self._status == CLOSED

    @property
    def is_jammed(self) -> bool:
        """Is this lock jammed"""
        return self._status == JAMMED

    @property
    def battery_level(self) -> int:
        """The battery percentage"""
        return _map(self._battery, 3600, 8000, 0, 100)
