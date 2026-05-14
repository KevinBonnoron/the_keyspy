"""Base class for TheKeys devices."""


class TheKeysDevice:
    """Common attributes shared by all TheKeys devices (gateways, locks, ...)."""

    def __init__(self, id: int) -> None:
        self._id = id

    @property
    def id(self) -> int:
        """Device identifier."""
        return self._id
