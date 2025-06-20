"""Utility functions for PostgreSQL connections and DataFrame upserts."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Dict, Any, Iterable

import pandas as pd
import psycopg2
from psycopg2 import extras


@contextmanager
def get_pgsql_cxn(host: str, dbname: str, user: str, password: str, port: int = 5432) -> Generator[psycopg2.extensions.connection, None, None]:
    """Yield a PostgreSQL connection."""
    conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password, port=port)
    try:
        yield conn
    finally:
        conn.close()


def upsert_df(df: pd.DataFrame, schema: str, table_name: str, cxn: psycopg2.extensions.connection, conflict_fields: Iterable[str] | None = None) -> None:
    """Insert DataFrame rows into a table using ``ON CONFLICT DO NOTHING``.

    Parameters
    ----------
    df:
        Data to upsert.
    schema:
        Target schema name.
    table_name:
        Target table name.
    cxn:
        Open psycopg2 connection.
    conflict_fields:
        Optional list of column names to determine conflicts. If ``None`` the
        statement simply ignores conflicts.
    """

    if df.empty:
        return

    cols = list(df.columns)
    placeholders = ", ".join(["%s"] * len(cols))
    columns = ", ".join(cols)

    if conflict_fields:
        conflict = f"({', '.join(conflict_fields)})"
        query = (
            f"INSERT INTO {schema}.{table_name} ({columns}) "
            f"VALUES ({placeholders}) ON CONFLICT {conflict} DO NOTHING"
        )
    else:
        query = (
            f"INSERT INTO {schema}.{table_name} ({columns}) "
            f"VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        )

    values = [tuple(row) for row in df.to_numpy()]
    with cxn.cursor() as cur:
        extras.execute_batch(cur, query, values)
    cxn.commit()

