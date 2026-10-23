"""Internal helpers shared by the API client and devices."""
from typing import Any

import requests

from .errors import InvalidResponseError


def parse_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except requests.JSONDecodeError as error:
        raise InvalidResponseError(response.url, response.status_code, response.text) from error
