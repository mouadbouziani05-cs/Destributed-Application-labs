from __future__ import annotations

import os

import bootstrap  # noqa: F401

from src.auth_service.repository import create_user_from_password, initialize_auth_db, get_user_by_username
from src.audit_service.repository import initialize_audit_db
from src.common.config import SETTINGS
from src.gateway.repository import initialize_gateway_db


DEFAULT_USERS = [
    ("admin", os.getenv("DEMO_ADMIN_PASSWORD", "Admin!2345"), "admin"),
    ("analyst", os.getenv("DEMO_USER_PASSWORD", "User!2345"), "user"),
]


def ensure_user(username: str, password: str, role: str) -> None:
    existing = get_user_by_username(SETTINGS.auth_db_path, username)
    if existing is None:
        create_user_from_password(SETTINGS.auth_db_path, username, password, role)
        print(f"Created user: {username} ({role})")
    else:
        print(f"User already exists: {username}")


if __name__ == "__main__":
    initialize_auth_db(SETTINGS.auth_db_path)
    initialize_gateway_db(SETTINGS.gateway_db_path)
    initialize_audit_db(SETTINGS.audit_db_path)
    for username, password, role in DEFAULT_USERS:
        ensure_user(username, password, role)
    print("Demo data initialized")
