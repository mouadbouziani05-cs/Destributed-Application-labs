from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import uuid

from src.common.config import SETTINGS
from src.common.errors import AnalysisError, AuthenticationError, AuthorizationError, DependencyUnavailable, ValidationRejected
from src.common.security import decode_access_token
from src.common.validation import AnalysisResult, ReportHistoryItem, ReportRecord, ReportSubmissionInput
from src.gateway.clients import AnalysisServiceClient, AuditServiceClient, AuthServiceClient
from src.gateway.repository import get_report, initialize_gateway_db, insert_report, list_reports


@dataclass
class GatewayUser:
    user_id: int
    username: str
    role: str


class GatewayService:
    def __init__(self) -> None:
        self.auth_client = AuthServiceClient(SETTINGS.auth_service_url)
        self.audit_client = AuditServiceClient(SETTINGS.audit_service_url)
        self.analysis_client = AnalysisServiceClient()

    def initialize(self) -> None:
        initialize_gateway_db(SETTINGS.gateway_db_path)

    def login(self, username: str, password: str) -> dict[str, Any]:
        response = self.auth_client.login(username, password)
        self._publish_audit(
            service="gateway",
            action="login_proxy",
            level="info",
            actor=username,
            message="User logged in through the gateway",
            metadata={"username": username},
        )
        return response

    def current_user(self, token: str) -> GatewayUser:
        claims = decode_access_token(token, secret=SETTINGS.jwt_secret, algorithm=SETTINGS.jwt_algorithm)
        return GatewayUser(user_id=int(claims["sub"]), username=str(claims["username"]), role=str(claims["role"]))

    def submit_report(self, user: GatewayUser, payload: dict[str, Any]) -> dict[str, Any]:
        request = ReportSubmissionInput.model_validate(payload)
        analysis = self.analysis_client.analyze(request.model_dump())
        self._validate_analysis_payload(analysis)
        report_id = str(uuid.uuid4())
        record = {
            "report_id": report_id,
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "sender": request.sender,
            "subject": request.subject,
            "content": request.content,
            "urls_detected": analysis["urls_detected"],
            "score": int(analysis["risk_score"]),
            "risk_level": analysis["risk_level"],
            "justification": analysis["justification"],
            "analysis": analysis,
        }
        saved = insert_report(SETTINGS.gateway_db_path, record)
        self._publish_audit(
            service="gateway",
            action="report_submitted",
            level="info",
            actor=user.username,
            message="Phishing report submitted",
            metadata={"report_id": report_id, "score": saved["score"], "risk_level": saved["risk_level"]},
        )
        return saved

    def list_user_reports(self, user: GatewayUser) -> list[dict[str, Any]]:
        if user.role == "admin":
            return list_reports(SETTINGS.gateway_db_path)
        return list_reports(SETTINGS.gateway_db_path, username=user.username)

    def get_report(self, user: GatewayUser, report_id: str) -> dict[str, Any]:
        report = get_report(SETTINGS.gateway_db_path, report_id)
        if report is None:
            raise ValidationRejected("Report not found")
        if user.role != "admin" and report["username"] != user.username:
            raise AuthorizationError("Forbidden")
        return report

    def _validate_analysis_payload(self, analysis: dict[str, Any]) -> None:
        try:
            AnalysisResult.model_validate(analysis)
        except Exception as exc:
            raise AnalysisError("Invalid analysis response") from exc

    def _publish_audit(self, *, service: str, action: str, level: str, actor: str | None, message: str, metadata: dict[str, Any]) -> None:
        event = {
            "service": service,
            "action": action,
            "level": level,
            "message": message,
            "actor": actor,
            "correlation_id": None,
            "metadata": metadata,
        }
        try:
            self.audit_client.publish_event(event)
        except Exception:
            return
