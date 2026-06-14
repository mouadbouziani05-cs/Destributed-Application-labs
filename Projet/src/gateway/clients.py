from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import Pyro5.api
import Pyro5.errors
import requests

from src.common.config import SETTINGS
from src.common.errors import DependencyUnavailable
from src.common.resilience import CircuitBreaker, retry_call
from src.common.validation import AuditEventInput


@dataclass
class HttpServiceClient:
    base_url: str
    timeout_seconds: float = 4.0

    def __post_init__(self) -> None:
        self.session = requests.Session()

    def post_json(self, path: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        response = self.session.post(url, json=payload, headers=headers or {}, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()


class AuthServiceClient(HttpServiceClient):
    def login(self, username: str, password: str) -> dict[str, Any]:
        return self.post_json("/auth/login", {"username": username, "password": password})


class AuditServiceClient(HttpServiceClient):
    def publish_event(self, event: dict[str, Any]) -> dict[str, Any]:
        headers = {"X-Internal-Token": SETTINGS.internal_service_token}
        return self.post_json("/audit/events", event, headers=headers)


class AnalysisServiceClient:
    def __init__(self) -> None:
        self.breaker = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=20)
        self.uri = f"PYRO:phishing.analysis@{SETTINGS.analysis_service_host}:{SETTINGS.analysis_service_port}"
        self.timeout_seconds = 5.0

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        def invoke() -> dict[str, Any]:
            if not self.breaker.allow():
                raise DependencyUnavailable("Analysis service temporarily unavailable")
            try:
                with Pyro5.api.Proxy(self.uri) as proxy:
                    proxy._pyroTimeout = self.timeout_seconds
                    result = proxy.analyze_email(payload)
                    self.breaker.record_success()
                    return result
            except (Pyro5.errors.PyroError, OSError, TimeoutError) as exc:
                self.breaker.record_failure()
                raise DependencyUnavailable("Analysis service unavailable") from exc

        return retry_call(invoke, attempts=3, delay_seconds=0.25)
