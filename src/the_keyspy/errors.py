"""Custom exception types raised by the_keyspy."""


class TheKeysApiError(Exception):
    """Base exception for TheKeysApi errors."""


class NoAccessoriesFoundError(TheKeysApiError):
    """Raised when no accessories are found for a lock."""


class NoGatewayAccessoryFoundError(TheKeysApiError):
    """Raised when no gateway accessory is found for a lock."""


class GatewayAccessoryNotFoundError(TheKeysApiError):
    """Raised when the gateway accessory could not be retrieved from the API."""


class NoGatewayIpFoundError(TheKeysApiError):
    """Raised when no gateway IP is found for a lock."""


class NoSharesFoundError(TheKeysApiError):
    """Raised when no shares are found for a lock."""


class NoUtilisateurFoundError(TheKeysApiError):
    """Raised when the user could not be retrieved from the API."""


class GatewayUnreachableError(TheKeysApiError):
    """Raised when the gateway cannot be reached (timeout or connection error).

    Wraps requests.Timeout and requests.ConnectionError so callers see a
    library-specific exception instead of leaking requests internals.
    """

    def __init__(self, host: str, original: Exception) -> None:
        super().__init__(f"Gateway {host} unreachable: {original}")
        self.host = host
        self.original = original


class GatewayTimeInvalidError(TheKeysApiError, RuntimeError):
    """Raised when the gateway clock is too far off and a resync+retry still fails.

    Inherits from RuntimeError to keep backward compatibility with callers that
    used to catch the raw RuntimeError raised by gateway.action().
    """

    def __init__(self, response_data: dict) -> None:
        super().__init__(response_data)
        self.response_data = response_data
