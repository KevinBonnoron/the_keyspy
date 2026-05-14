class TheKeysApiError(Exception):
    """Base exception for TheKeysApi errors."""
    pass


class NoAccessoriesFoundError(TheKeysApiError):
    """Raised when no accessories are found for a lock."""
    pass


class NoGatewayAccessoryFoundError(TheKeysApiError):
    """Raised when no gateway accessory is found for a lock."""
    pass


class GatewayAccessoryNotFoundError(TheKeysApiError):
    """Raised when the gateway accessory could not be retrieved from the API."""
    pass


class NoGatewayIpFoundError(TheKeysApiError):
    """Raised when no gateway IP is found for a lock."""
    pass


class NoSharesFoundError(TheKeysApiError):
    """Raised when no shares are found for a lock."""
    pass


class NoUtilisateurFoundError(TheKeysApiError):
    """Raised when the user could not be retrieved from the API."""
    pass


class GatewayTimeInvalidError(TheKeysApiError, RuntimeError):
    """Raised when the gateway clock is too far off and a resync+retry still fails.

    Inherits from RuntimeError to keep backward compatibility with callers that
    used to catch the raw RuntimeError raised by gateway.action().
    """

    def __init__(self, response_data: dict) -> None:
        super().__init__(response_data)
        self.response_data = response_data
