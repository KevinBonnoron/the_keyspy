"""TheKeys devices"""
import base64
import hmac
import time
from enum import Enum
from typing import Any

import requests


class Action(Enum):
    """All available actions"""
    OPEN = "open"
    CLOSE = "close"
    STATUS = "locker_status"


class TheKeysDevice:
    """Base class for all TheKeys devices"""

    def __init__(self, name: str, host: str, identifier: str, share_code: str) -> None:
        self.name = name
        self.host = host
        self.identifier = identifier
        self.share_code = share_code

    def update(self) -> None:
        """TODO"""

    def action(self, action: Action) -> Any:
        """Execute action on the device"""
        timestamp = str(int(time.time()))
        hash = base64.b64encode(hmac.new(self.share_code.encode("ascii"), timestamp.encode("ascii"), "sha256").digest())

        response = requests.post(
            f"{self.host}/{action.value}",
            data={"hash": hash, "identifier": self.identifier, "ts": timestamp},
        )
        return response.json()
