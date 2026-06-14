from __future__ import annotations

import bootstrap  # noqa: F401

import uvicorn

from src.auth_service.app import app


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
