"""Data quality validation helpers for the ETL pipeline."""

from __future__ import annotations

from typing import Iterable, List

import pandas as pd

# Columns that must be present and non-null
REQUIRED_COLUMNS = [
    "sensor_id",
    "time_stamp",
]

# Numeric columns that should not contain negative values
NON_NEGATIVE_COLUMNS = [
    "pm1_0_atm",
    "pm2_5_atm",
    "pm10_0_atm",
]


def validate_dataframe(df: pd.DataFrame) -> List[str]:
    """Validate a dataframe and return a list of issues found."""
    errors: List[str] = []

    if df.empty:
        return errors

    # Required columns
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
        elif df[col].isnull().any():
            errors.append(f"Null values found in column: {col}")

    # Negative value checks
    for col in NON_NEGATIVE_COLUMNS:
        if col in df.columns and (df[col] < 0).any():
            errors.append(f"Negative values found in column: {col}")

    # Duplicate records check
    if "sensor_id" in df.columns and "time_stamp" in df.columns:
        dupes = df.duplicated(subset=["sensor_id", "time_stamp"]).sum()
        if dupes > 0:
            errors.append(f"{dupes} duplicate sensor/time_stamp rows")

    return errors
