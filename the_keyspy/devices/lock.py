"""The Keys lock device implementation"""
import logging
from . import Action, TheKeysDevice

OPENED = "Door open"
CLOSED = "Door closed"
JAMMED = "Door jammed"
UNKNOWED = ""

_LOGGER = logging.getLogger(__name__)


class TheKeysLock(TheKeysDevice):
    """The Keys lock device implementation"""

    def __init__(self, name: str, host: str, identifier: str, share_code: str) -> None:
        super().__init__(
            name=name, host=host, identifier=identifier, share_code=share_code
        )
        self.locker_status = UNKNOWED
        self.__retrieve_lock_status()

    def lock(self) -> None:
        """Lock this lock"""
        response = self.action(Action.CLOSE)
        if response["status"] == "ok":
            self.locker_status = CLOSED
        else:
            self.locker_status = JAMMED

        return response["status"] == "ok"

    def unlock(self) -> None:
        """Unlock this lock"""
        response = self.action(Action.OPEN)
        if response["status"] == "ok":
            self.locker_status = OPENED
        else:
            self.locker_status = JAMMED

        return response["status"] == "ok"

    def update(self) -> None:
        """Update the lock status"""
        self.__retrieve_lock_status()

    @property
    def is_unlocked(self) -> bool:
        """Is this lock unlocked"""
        return self.locker_status == OPENED

    @property
    def is_locked(self) -> bool:
        """Is this lock locked"""
        return self.locker_status == CLOSED

    @property
    def is_jammed(self) -> bool:
        """Is this lock jammed"""
        return self.locker_status == JAMMED

    def __retrieve_lock_status(self) -> None:
        try:
            self.locker_status = self.action(Action.STATUS)["status"]
        except ConnectionError as error:
            _LOGGER.error(error)
