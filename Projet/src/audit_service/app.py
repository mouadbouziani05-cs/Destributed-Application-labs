from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from src.audit_service.repository import initialize_audit_db, insert_event, list_events
from src.common.config import SETTINGS
from src.common.logging_utils import configure_service_logging
from src.common.validation import AuditEventInput


logger = configure_service_logging("audit_service")
app = FastAPI(title="Audit Service", version="1.0")


@app.middleware("http")
async def enforce_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > SETTINGS.max_body_bytes:
                return JSONResponse(status_code=413, content={"detail": "Request too large"})
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid request"})
    return await call_next(request)


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled audit service error")
    return JSONResponse(status_code=500, content={"detail": "Audit service error"})


@app.on_event("startup")
def startup() -> None:
    initialize_audit_db(SETTINGS.audit_db_path)
    logger.info("Audit database ready")


def _check_internal_token(internal_token: str | None) -> None:
    if internal_token != SETTINGS.internal_service_token:
        raise HTTPException(status_code=403, detail="Forbidden")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "audit"}


@app.post("/audit/events")
def receive_event(payload: AuditEventInput, x_internal_token: str | None = Header(default=None, alias="X-Internal-Token")) -> dict[str, Any]:
    _check_internal_token(x_internal_token)
    event = insert_event(SETTINGS.audit_db_path, payload.model_dump())
    logger.info("Audit event stored", extra={"event": "audit_stored", "details": {"action": event["action"], "service": event["service"]}})
    return {"status": "stored", "event": event}


@app.get("/audit/events")
def get_events(
    limit: int = 50,
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> dict[str, Any]:
    _check_internal_token(x_internal_token)
    safe_limit = max(1, min(limit, 200))
    return {"items": list_events(SETTINGS.audit_db_path, limit=safe_limit)}
