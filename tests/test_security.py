import uuid
from datetime import UTC, datetime, timedelta

from jose import jwt

from src.app.core.security import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify() -> None:
    hashed = hash_password("supersecret123")
    assert verify_password("supersecret123", hashed)


def test_password_verify_returns_false_for_wrong_password() -> None:
    hashed = hash_password("correct-password")
    assert not verify_password("wrong-password", hashed)


def test_password_hashes_are_unique_for_same_input() -> None:
    assert hash_password("identical") != hash_password("identical")


def test_access_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    payload = decode_token(create_access_token(user_id))
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_refresh_token_contains_jti_and_correct_type() -> None:
    user_id = uuid.uuid4()
    payload = decode_token(create_refresh_token(user_id))
    assert payload is not None
    assert payload["type"] == "refresh"
    assert payload["sub"] == str(user_id)
    assert payload.get("jti")


def test_decode_tampered_token_returns_none() -> None:
    token = create_access_token(uuid.uuid4())
    tampered = token[:-6] + "XXXXXX"
    assert decode_token(tampered) is None


def test_decode_token_signed_with_wrong_secret_returns_none() -> None:
    payload = {
        "sub": str(uuid.uuid4()),
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "type": "access",
    }
    foreign = jwt.encode(payload, "definitely-not-our-secret-key-32chars", algorithm=ALGORITHM)
    assert decode_token(foreign) is None
