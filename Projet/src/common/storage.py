from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Iterable, Any


def ensure_parent_dir(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def connect_sqlite(db_path: str) -> sqlite3.Connection:
    ensure_parent_dir(db_path)
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]
