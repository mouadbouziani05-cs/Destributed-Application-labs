from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import json

from src.common.storage import connect_sqlite, row_to_dict, rows_to_dicts


SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    service TEXT NOT NULL,
    action TEXT NOT NULL,
    level TEXT NOT NULL,
    actor TEXT,
    correlation_id TEXT,
    message TEXT NOT NULL,
    metadata_json TEXT NOT NULL
)
"""


def initialize_audit_db(db_path: str) -> None:
    with connect_sqlite(db_path) as connection:
        connection.execute(SCHEMA)
        connection.commit()


def insert_event(db_path: str, event: dict[str, Any]) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    metadata_json = json.dumps(event.get("metadata", {}), ensure_ascii=True)
    with connect_sqlite(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO audit_events
            (created_at, service, action, level, actor, correlation_id, message, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                event["service"],
                event["action"],
                event["level"],
                event.get("actor"),
                event.get("correlation_id"),
                event["message"],
                metadata_json,
            ),
        )
        connection.commit()
        return get_event_by_id(db_path, int(cursor.lastrowid))


def get_event_by_id(db_path: str, event_id: int) -> dict[str, Any] | None:
    with connect_sqlite(db_path) as connection:
        row = connection.execute("SELECT * FROM audit_events WHERE id = ?", (event_id,)).fetchone()
        return _deserialize_event(row_to_dict(row))


def list_events(db_path: str, limit: int = 50) -> list[dict[str, Any]]:
    with connect_sqlite(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM audit_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_deserialize_event(item) for item in rows_to_dicts(rows)]


def _deserialize_event(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    payload = dict(row)
    payload["metadata"] = json.loads(payload.pop("metadata_json") or "{}")
    return payload
