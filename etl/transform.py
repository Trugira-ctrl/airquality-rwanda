"""Data transformation helpers for the ETL pipeline."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

import pandas as pd


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Replace dots in column names with underscores."""
    df = df.copy()
    df.columns = [c.replace(".", "_") for c in df.columns]
    return df


def transform_purpleair_data(api_data: Dict[str, Any] | List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert PurpleAir API payload into a normalized DataFrame."""

    if not api_data:
        return pd.DataFrame()

    if isinstance(api_data, dict) and "data" in api_data and "fields" in api_data:
        df = pd.DataFrame(api_data["data"], columns=api_data["fields"])
    else:
        df = pd.DataFrame(api_data)

    df = _normalize_columns(df)

    if "last_seen" in df.columns:
        df["time_stamp"] = pd.to_datetime(df["last_seen"], unit="s", utc=True)
        df.drop(columns=["last_seen"], inplace=True)

    return df


def transform_rema_data(api_data: Iterable[Dict[str, Any]]) -> pd.DataFrame:
    """Convert REMA API payload into a DataFrame.

    The exact structure of the REMA API is currently unknown, so this function
    performs minimal processing and simply returns ``pd.DataFrame(api_data)``.
    """

    if not api_data:
        return pd.DataFrame()
    return pd.DataFrame(api_data)


def transform(data: Iterable[Dict[str, Any]], source: str) -> pd.DataFrame:
    """Backward compatible generic entry point."""

    if source.lower() == "purpleair":
        return transform_purpleair_data(data)
    if source.lower() == "rema":
        return transform_rema_data(data)
    raise ValueError(f"Unknown source '{source}'")

