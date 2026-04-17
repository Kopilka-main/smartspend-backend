import pytest
from pydantic import ValidationError

from src.app.schemas.auth import RegisterRequest


def test_register_request_accepts_valid_payload() -> None:
    req = RegisterRequest(
        email="user@example.com",
        password="longenough1",
        display_name="Test User",
    )
    assert req.email == "user@example.com"
    assert req.display_name == "Test User"


def test_register_request_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="user@example.com",
            password="short",
            display_name="Test",
        )


def test_register_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="not-an-email",
            password="longenough1",
            display_name="Test",
        )
