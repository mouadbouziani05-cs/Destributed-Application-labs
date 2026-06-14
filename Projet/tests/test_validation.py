import pytest
from pydantic import ValidationError

from src.common.errors import ValidationRejected
from src.common.validation import LoginRequest, ReportSubmissionInput


def test_invalid_sender_is_rejected() -> None:
    with pytest.raises(ValidationRejected):
        ReportSubmissionInput.model_validate(
            {
                "sender": "not-an-email",
                "subject": "Suspicious",
                "content": "Please confirm your account.",
                "attachments": [],
            }
        )


def test_invalid_attachment_is_rejected() -> None:
    with pytest.raises(ValidationRejected):
        ReportSubmissionInput.model_validate(
            {
                "sender": "user@example.com",
                "subject": "Suspicious",
                "content": "Open the file.",
                "attachments": ["bad/../../payload.exe"],
            }
        )


def test_login_request_requires_strong_password_length() -> None:
    with pytest.raises(ValidationError):
        LoginRequest.model_validate({"username": "alice", "password": "short"})
