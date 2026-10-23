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


class LockerSyncError(TheKeysApiError, RuntimeError):
    """Raised when the gateway repeatedly fails to talk to the lock over BLE.

    Covers codes 1-5 returned by the gateway when the gateway-to-lock BLE
    relay fails (lock not detected, BLE timeout, sync data invalid, etc.).
    Inherits from RuntimeError for backward compatibility with callers that
    used to catch the raw RuntimeError raised by gateway.action().
    """

    # Codes 1-4 come from the official TheKeys KB; code 5 is observed in
    # practice on transient BLE failures and treated the same way.
    MESSAGES = {
        1: "Lock not detected",
        2: "Lock not compatible",
        3: "Invalid synchronization data",
        4: "Error during synchronization",
        5: "Synchronization error (BLE transient)",
    }

    def __init__(self, code: int, response_data: dict) -> None:
        description = self.MESSAGES.get(code, f"Unknown sync error code {code}")
        super().__init__(f"Locker sync failed (code {code}): {description}")
        self.code = code
        self.response_data = response_data

