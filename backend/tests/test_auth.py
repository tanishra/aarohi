import time
from datetime import timedelta

import jwt

from core.auth import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    verify_password,
    get_password_hash,
)


def test_password_hashing():
    password = "my-secure-password-123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert isinstance(hashed, str)


def test_password_verification_correct():
    password = "my-secure-password-123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True


def test_password_verification_wrong():
    hashed = get_password_hash("correct-password")
    assert verify_password("wrong-password", hashed) is False


def test_password_verification_empty():
    hashed = get_password_hash("password")
    assert verify_password("", hashed) is False


def test_create_access_token_contains_sub():
    token = create_access_token(data={"sub": "clinic-123"})
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "clinic-123"


def test_create_access_token_with_expiry():
    token = create_access_token(
        data={"sub": "clinic-123"},
        expires_delta=timedelta(hours=1),
    )
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "clinic-123"
    assert "exp" in decoded


def test_token_default_expiry_minutes():
    token = create_access_token(data={"sub": "clinic-123"})
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert "exp" in decoded


def test_token_expired():
    token = create_access_token(
        data={"sub": "clinic-123"},
        expires_delta=timedelta(seconds=-1),
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def test_tampered_token_rejected():
    token = create_access_token(data={"sub": "clinic-123"})
    tampered = token + "x"
    with pytest.raises(jwt.InvalidTokenError):
        jwt.decode(tampered, SECRET_KEY, algorithms=[ALGORITHM])


def test_wrong_secret_rejected():
    token = create_access_token(data={"sub": "clinic-123"})
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, "wrong-secret", algorithms=[ALGORITHM])


def test_multiple_tokens_unique():
    token1 = create_access_token(
        data={"sub": "clinic-123"},
        expires_delta=timedelta(minutes=15),
    )
    token2 = create_access_token(
        data={"sub": "clinic-123"},
        expires_delta=timedelta(minutes=30),
    )
    assert token1 != token2


def test_extra_claims_preserved():
    token = create_access_token(data={"sub": "clinic-123", "role": "admin"})
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["role"] == "admin"


import pytest
