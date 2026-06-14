from __future__ import annotations


class ServiceError(Exception):
    """Base class for domain errors that should be handled safely."""


class ValidationRejected(ServiceError):
    """Raised when a request does not satisfy strict input rules."""


class AuthenticationError(ServiceError):
    """Raised when credentials or tokens are invalid."""


class AuthorizationError(ServiceError):
    """Raised when a user does not have the required role or scope."""


class DependencyUnavailable(ServiceError):
    """Raised when an internal dependency is temporarily unreachable."""


class AnalysisError(ServiceError):
    """Raised when the heuristic engine cannot produce a result."""


class RateLimitExceeded(ServiceError):
    """Raised when a caller exceeds the configured request budget."""
