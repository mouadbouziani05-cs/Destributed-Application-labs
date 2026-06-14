from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": self.service_name,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("event", "correlation_id", "actor", "details"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_service_logging(service_name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(service_name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(service_name))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
