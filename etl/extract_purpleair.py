"""Functions to fetch data from the PurpleAir API."""

from __future__ import annotations

import time
from typing import Any, Dict, List

import requests

from config import Config


def _fetch_multi_sensor(
    sensor_ids: List[int],
    read_keys: List[str],
    fields: str,
    *,
    max_retries: int = 5,
) -> List[Dict[str, Any]]:
    """Call the PurpleAir multi-sensor endpoint and return parsed rows."""

    if len(sensor_ids) != len(read_keys):
        raise ValueError("sensor_ids and read_keys must be the same length")

    url = Config.PURPLEAIR_BASE_URL
    headers = {"X-API-Key": Config.PURPLEAIR_API_KEY}
    params = {
        "show_only": ",".join(str(s) for s in sensor_ids),
        "read_keys": ",".join(read_keys),
        "fields": fields,
    }

    delay = 0.5
    for attempt in range(max_retries):
        time.sleep(delay)
        resp = requests.get(url, headers=headers, params=params, timeout=Config.REQUEST_TIMEOUT)

        if resp.status_code == 429:
            delay *= 2
            continue

        if resp.status_code >= 400:
            resp.raise_for_status()

        data = resp.json()
        field_names = data.get("fields", [])
        rows = [dict(zip(field_names, row)) for row in data.get("data", [])]
        return rows

    # If we exhausted retries on 429
    resp = requests.get(url, headers=headers, params=params, timeout=Config.REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    field_names = data.get("fields", [])
    return [dict(zip(field_names, row)) for row in data.get("data", [])]


def extract_purpleair_data() -> List[Dict[str, Any]]:
    """Retrieve sensor data from the PurpleAir API.

    The function queries the list of sensors defined in the configuration and
    returns a list of dictionaries with sensor field values.
    """

    sensors = Config.get_private_sensors()
    if not sensors:
        raise ValueError("No PurpleAir sensors configured")

    sensor_ids = [int(sid) for sid in sensors.keys()]
    read_keys = list(sensors.values())
    fields = ",".join(Config.PURPLEAIR_FIELDS)

    return _fetch_multi_sensor(sensor_ids, read_keys, fields)


def extract_purpleair() -> List[Dict[str, Any]]:
    """Backward compatible wrapper."""
    return extract_purpleair_data()

