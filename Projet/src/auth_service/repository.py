from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.common.security import hash_password
from src.common.storage import connect_sqlite, row_to_dict, rows_to_dicts


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'admin')),
    created_at TEXT NOT NULL
)
"""


def initialize_auth_db(db_path: str) -> None:
    with connect_sqlite(db_path) as connection:
        connection.execute(SCHEMA)
        connection.commit()


def create_user(db_path: str, username: str, password_hash: str, role: str) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    with connect_sqlite(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (username.lower(), password_hash, role, created_at),
        )
        connection.commit()
        return get_user_by_id(db_path, int(cursor.lastrowid))


def create_user_from_password(db_path: str, username: str, password: str, role: str) -> dict[str, Any]:
    return create_user(db_path, username, hash_password(password), role)


def get_user_by_username(db_path: str, username: str) -> dict[str, Any] | None:
    with connect_sqlite(db_path) as connection:
        row = connection.execute(
            "SELECT id, username, password_hash, role, created_at FROM users WHERE username = ?",
            (username.lower(),),
        ).fetchone()
        return row_to_dict(row)


def get_user_by_id(db_path: str, user_id: int) -> dict[str, Any] | None:
    with connect_sqlite(db_path) as connection:
        row = connection.execute(
            "SELECT id, username, password_hash, role, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return row_to_dict(row)


def list_users(db_path: str) -> list[dict[str, Any]]:
    with connect_sqlite(db_path) as connection:
        rows = connection.execute(
            "SELECT id, username, password_hash, role, created_at FROM users ORDER BY id ASC"
        ).fetchall()
        return rows_to_dicts(rows)


def count_users(db_path: str) -> int:
    with connect_sqlite(db_path) as connection:
        row = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()
        return int(row["total"]) if row else 0
