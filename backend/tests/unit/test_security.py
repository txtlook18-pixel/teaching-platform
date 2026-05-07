from datetime import timedelta
import pytest
from jose import jwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)
from app.config import settings


def test_hash_password_is_not_plaintext():
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert len(hashed) > 20


def test_verify_password_correct():
    hashed = hash_password("correct")
    assert verify_password("correct", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False


def test_create_access_token_returns_string():
    token = create_access_token({"sub": "user-123"})
    assert isinstance(token, str)
    assert len(token) > 10


def test_decode_token_returns_subject():
    token = create_access_token({"sub": "user-abc"})
    result = decode_token(token)
    assert result == "user-abc"


def test_decode_token_invalid_returns_none():
    assert decode_token("not.a.valid.token") is None


def test_decode_token_tampered_returns_none():
    token = create_access_token({"sub": "user-1"})
    tampered = token[:-5] + "XXXXX"
    assert decode_token(tampered) is None


def test_token_contains_exp_claim():
    token = create_access_token({"sub": "user-1"})
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    assert "exp" in payload


def test_token_expired_returns_none():
    token = create_access_token({"sub": "user-1"}, expires_delta=timedelta(seconds=-1))
    assert decode_token(token) is None


def test_create_token_custom_expiry():
    token = create_access_token({"sub": "user-1"}, expires_delta=timedelta(hours=2))
    result = decode_token(token)
    assert result == "user-1"