from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from src.auth_service.repository import (
    count_users,
    get_user_by_id,
    get_user_by_username,
    initialize_auth_db,
)
from src.common.config import SETTINGS
from src.common.errors import AuthenticationError, ValidationRejected
from src.common.logging_utils import configure_service_logging
from src.common.security import create_access_token, decode_access_token, token_preview, verify_password
from src.common.storage import connect_sqlite
from src.common.validation import LoginRequest


logger = configure_service_logging("auth_service")
app = FastAPI(title="Auth Service", version="1.0")


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


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(_: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"detail": str(exc) or "Authentication failed"})


@app.exception_handler(ValidationRejected)
async def validation_error_handler(_: Request, exc: ValidationRejected):
    return JSONResponse(status_code=400, content={"detail": str(exc) or "Invalid request"})


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled auth service error")
    return JSONResponse(status_code=500, content={"detail": "Authentication service error"})


@app.on_event("startup")
def startup() -> None:
    initialize_auth_db(SETTINGS.auth_db_path)
    logger.info("Auth database ready")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "auth"}


@app.post("/auth/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    user = get_user_by_username(SETTINGS.auth_db_path, payload.username)
    if not user or not verify_password(payload.password, user["password_hash"]):
        logger.warning("Authentication failed", extra={"event": "login_failed", "actor": payload.username})
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        user_id=int(user["id"]),
        username=user["username"],
        role=user["role"],
        secret=SETTINGS.jwt_secret,
        algorithm=SETTINGS.jwt_algorithm,
        expires_minutes=SETTINGS.jwt_exp_minutes,
    )
    logger.info(
        "Login successful",
        extra={"event": "login_success", "actor": user["username"], "details": {"token_preview": token_preview(token)}},
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        },
    }


@app.post("/auth/verify")
def verify_token(payload: dict[str, str]) -> dict[str, Any]:
    token = payload.get("token", "")
    claims = decode_access_token(token, secret=SETTINGS.jwt_secret, algorithm=SETTINGS.jwt_algorithm)
    user = get_user_by_id(SETTINGS.auth_db_path, int(claims["sub"]))
    if not user:
        raise AuthenticationError("Unknown user")
    return {
        "valid": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        },
        "claims": {
            "sub": claims["sub"],
            "username": claims["username"],
            "role": claims["role"],
            "exp": claims["exp"],
        },
    }


@app.get("/auth/users/count")
def user_count() -> dict[str, int]:
    return {"total": count_users(SETTINGS.auth_db_path)}
