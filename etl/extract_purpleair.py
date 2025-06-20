"""Functions to fetch data from the PurpleAir API."""

from __future__ import annotations

import requests
from typing import Any, Dict

from config import Config


def extract_purpleair_data() -> Dict[str, Any]:
    """Retrieve sensor data from the PurpleAir API.

    The function queries the list of sensors defined in the configuration and
    returns the raw JSON payload from the API. Network errors are not suppressed
    so that callers can handle them appropriately.
    """

    sensors = Config.get_private_sensors()
    if not sensors:
        raise ValueError("No PurpleAir sensors configured")

    headers = {"X-API-Key": Config.PURPLEAIR_API_KEY}
    params = {
        "show": ",".join(sensors.keys()),
        "fields": ",".join(Config.PURPLEAIR_FIELDS),
    }

    resp = requests.get(
        Config.PURPLEAIR_BASE_URL,
        headers=headers,
        params=params,
        timeout=Config.REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def extract_purpleair() -> Dict[str, Any]:
    """Backward compatible wrapper."""
    return extract_purpleair_data()

