from __future__ import annotations

from collections import defaultdict, deque
from time import monotonic
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from src.common.config import SETTINGS
from src.common.errors import AnalysisError, AuthenticationError, AuthorizationError, DependencyUnavailable, RateLimitExceeded, ValidationRejected
from src.common.logging_utils import configure_service_logging
from src.gateway.service import GatewayService, GatewayUser


logger = configure_service_logging("gateway")
app = FastAPI(title="Phishing Gateway", version="1.0")
service = GatewayService()
rate_limit_cache: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def protect_request(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > SETTINGS.max_body_bytes:
                return JSONResponse(status_code=413, content={"detail": "Request too large"})
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid request"})

    client_ip = request.client.host if request.client else "unknown"
    bucket = rate_limit_cache[client_ip]
    now = monotonic()
    while bucket and now - bucket[0] > SETTINGS.rate_limit_window_seconds:
        bucket.popleft()
    if len(bucket) >= SETTINGS.rate_limit_requests:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    bucket.append(now)

    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled gateway exception")
        return JSONResponse(status_code=500, content={"detail": "Gateway error"})


@app.on_event("startup")
def startup() -> None:
    service.initialize()
    logger.info("Gateway database ready")


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "gateway",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "login": "/api/login",
            "reports": "/api/reports",
            "me": "/api/me",
        },
        "web_ui": SETTINGS.gateway_service_url.replace(":8000", ":8501"),
        "docs": "/docs",
    }


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "gateway"}


@app.post("/api/login")
def login(payload: dict[str, str]) -> dict[str, Any]:
    username = payload.get("username", "")
    password = payload.get("password", "")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    try:
        return service.login(username, password)
    except DependencyUnavailable:
        raise HTTPException(status_code=503, detail="Authentication backend unavailable")
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid credentials")



def get_current_user(authorization: str | None = Header(default=None)) -> GatewayUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.split(" ", 1)[1].strip()
    try:
        return service.current_user(token)
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication required")


@app.post("/api/reports")
def submit_report(payload: dict[str, Any], current_user: GatewayUser = Depends(get_current_user)) -> dict[str, Any]:
    try:
        return service.submit_report(current_user, payload)
    except ValidationRejected as exc:
        raise HTTPException(status_code=400, detail="Invalid report") from exc
    except DependencyUnavailable:
        raise HTTPException(status_code=503, detail="Analysis backend unavailable")
    except AnalysisError:
        raise HTTPException(status_code=502, detail="Analysis error")


@app.get("/api/reports")
def get_reports(current_user: GatewayUser = Depends(get_current_user)) -> dict[str, Any]:
    return {"items": service.list_user_reports(current_user)}


@app.get("/api/reports/{report_id}")
def get_report(report_id: str, current_user: GatewayUser = Depends(get_current_user)) -> dict[str, Any]:
    try:
        return service.get_report(current_user, report_id)
    except ValidationRejected as exc:
        raise HTTPException(status_code=404, detail="Report not found") from exc
    except AuthorizationError:
        raise HTTPException(status_code=403, detail="Forbidden")


@app.get("/api/me")
def me(current_user: GatewayUser = Depends(get_current_user)) -> dict[str, Any]:
    return {"id": current_user.user_id, "username": current_user.username, "role": current_user.role}
