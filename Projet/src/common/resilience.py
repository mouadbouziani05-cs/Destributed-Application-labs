from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic, sleep
from typing import Callable, Iterable, TypeVar

from src.common.errors import DependencyUnavailable


T = TypeVar("T")


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout_seconds: int = 20
    failure_count: int = 0
    opened_at: float | None = None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        elapsed = monotonic() - self.opened_at
        if elapsed >= self.recovery_timeout_seconds:
            self.failure_count = 0
            self.opened_at = None
            return True
        return False

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.opened_at = monotonic()


def retry_call(
    func: Callable[[], T],
    *,
    attempts: int = 3,
    delay_seconds: float = 0.25,
    retry_on: tuple[type[Exception], ...] = (DependencyUnavailable, TimeoutError, OSError),
) -> T:
    last_error: Exception | None = None
    for index in range(1, attempts + 1):
        try:
            return func()
        except retry_on as exc:
            last_error = exc
            if index < attempts:
                sleep(delay_seconds * index)
    assert last_error is not None
    raise last_error
