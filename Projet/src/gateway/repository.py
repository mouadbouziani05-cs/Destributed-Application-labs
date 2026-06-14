from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import json

from src.common.storage import connect_sqlite, row_to_dict, rows_to_dicts


SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    report_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    sender TEXT NOT NULL,
    subject TEXT NOT NULL,
    content TEXT NOT NULL,
    urls_json TEXT NOT NULL,
    score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    justification TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


def initialize_gateway_db(db_path: str) -> None:
    with connect_sqlite(db_path) as connection:
        connection.execute(SCHEMA)
        connection.commit()


def insert_report(db_path: str, report: dict[str, Any]) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    with connect_sqlite(db_path) as connection:
        connection.execute(
            """
            INSERT INTO reports
            (report_id, user_id, username, role, sender, subject, content, urls_json, score, risk_level, justification, analysis_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report["report_id"],
                report["user_id"],
                report["username"],
                report["role"],
                report["sender"],
                report["subject"],
                report["content"],
                json.dumps(report["urls_detected"], ensure_ascii=True),
                report["score"],
                report["risk_level"],
                report["justification"],
                json.dumps(report["analysis"], ensure_ascii=True),
                created_at,
            ),
        )
        connection.commit()
        return get_report(db_path, report["report_id"])


def list_reports(db_path: str, username: str | None = None) -> list[dict[str, Any]]:
    with connect_sqlite(db_path) as connection:
        if username:
            rows = connection.execute(
                "SELECT * FROM reports WHERE username = ? ORDER BY created_at DESC",
                (username,),
            ).fetchall()
        else:
            rows = connection.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
        return [_deserialize_report(item) for item in rows_to_dicts(rows)]


def get_report(db_path: str, report_id: str) -> dict[str, Any] | None:
    with connect_sqlite(db_path) as connection:
        row = connection.execute("SELECT * FROM reports WHERE report_id = ?", (report_id,)).fetchone()
        return _deserialize_report(row_to_dict(row))


def _deserialize_report(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    payload = dict(row)
    payload["urls_detected"] = json.loads(payload.pop("urls_json") or "[]")
    payload["analysis"] = json.loads(payload.pop("analysis_json") or "{}")
    return payload
