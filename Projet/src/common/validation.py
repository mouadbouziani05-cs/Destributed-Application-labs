from __future__ import annotations

from typing import Any
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.common.errors import ValidationRejected


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
URL_RE = re.compile(r'https?://[^\s<>"]+', re.IGNORECASE)
ATTACHMENT_RE = re.compile(r"^[A-Za-z0-9_. -]{1,120}$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LoginRequest(StrictModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class ReportSubmissionInput(StrictModel):
    sender: str = Field(min_length=5, max_length=254)
    subject: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=10000)
    attachments: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("sender")
    @classmethod
    def validate_sender(cls, value: str) -> str:
        if not EMAIL_RE.match(value):
            raise ValidationRejected("Invalid sender address")
        return value.lower()

    @field_validator("attachments")
    @classmethod
    def validate_attachments(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in values:
            candidate = item.strip()
            if not candidate:
                continue
            if len(candidate) > 120 or not ATTACHMENT_RE.match(candidate):
                raise ValidationRejected("Invalid attachment name")
            cleaned.append(candidate)
        return cleaned

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 10000:
            raise ValidationRejected("Content too large")
        return value


class AuditEventInput(StrictModel):
    service: str = Field(min_length=2, max_length=32)
    action: str = Field(min_length=2, max_length=64)
    level: str = Field(min_length=3, max_length=16)
    message: str = Field(min_length=1, max_length=200)
    actor: str | None = Field(default=None, max_length=64)
    correlation_id: str | None = Field(default=None, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"debug", "info", "warning", "error", "critical"}:
            raise ValidationRejected("Invalid level")
        return normalized


class AnalysisResult(StrictModel):
    risk_score: int = Field(ge=0, le=100)
    risk_level: str = Field(min_length=3, max_length=16)
    justification: str = Field(min_length=1, max_length=5000)
    urls_detected: list[str] = Field(default_factory=list)
    signals: list[dict[str, Any]] = Field(default_factory=list)
    analysis_version: str = Field(default="1.0", min_length=1, max_length=12)


class ReportRecord(StrictModel):
    report_id: str
    sender: str
    subject: str
    content: str
    urls_detected: list[str]
    created_at: str
    username: str
    score: int
    risk_level: str
    justification: str


class ReportHistoryItem(StrictModel):
    report_id: str
    sender: str
    subject: str
    created_at: str
    score: int
    risk_level: str
    username: str


def normalize_max_body_size(content_length: str | None, max_bytes: int) -> None:
    if content_length is None:
        return
    try:
        if int(content_length) > max_bytes:
            raise ValidationRejected("Request too large")
    except ValueError as exc:
        raise ValidationRejected("Invalid content length") from exc
