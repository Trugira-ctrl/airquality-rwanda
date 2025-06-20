"""Placeholder for REMA extraction."""

from __future__ import annotations

from typing import Any, Dict, List


def extract_rema_data() -> List[Dict[str, Any]]:
    """Return REMA readings.

    REMA data access typically requires VPN connectivity. For now this function
    simply returns an empty list so that the pipeline can run without raising
    import errors.
    """

    return []


def extract_rema() -> List[Dict[str, Any]]:
    """Backward compatible wrapper."""
    return extract_rema_data()

