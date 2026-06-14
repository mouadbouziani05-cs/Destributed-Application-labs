from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


@dataclass(frozen=True)
class Settings:
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_exp_minutes: int = int(os.getenv("JWT_EXP_MINUTES", "30"))
    internal_service_token: str = os.getenv("INTERNAL_SERVICE_TOKEN", "internal-dev-token")
    max_body_bytes: int = int(os.getenv("MAX_BODY_BYTES", "65536"))
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
    audit_service_url: str = os.getenv("AUDIT_SERVICE_URL", "http://127.0.0.1:8002")
    gateway_service_url: str = os.getenv("GATEWAY_SERVICE_URL", "http://127.0.0.1:8000")
    analysis_service_host: str = os.getenv("ANALYSIS_SERVICE_HOST", "127.0.0.1")
    analysis_service_port: int = int(os.getenv("ANALYSIS_SERVICE_PORT", "9090"))
    auth_db_path: str = str(DATA_DIR / "auth.db")
    gateway_db_path: str = str(DATA_DIR / "gateway.db")
    audit_db_path: str = str(DATA_DIR / "audit.db")


SETTINGS = Settings()
