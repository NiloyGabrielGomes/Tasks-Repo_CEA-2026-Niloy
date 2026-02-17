"""
Tests for the authentication module (app.auth).

Run with:
    cd backend
    python -m pytest tests/test_auth.py -v
"""

import sys
import os

# Ensure the backend package is importable when running from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    validate_password_strength,
    is_token_expired,
    get_token_expiry,
)


# ===========================
# Password Hashing Tests
# ===========================

def test_hash_password_returns_hash():
    hashed = hash_password("test_password_123")
    assert hashed is not None
    assert hashed != "test_password_123"


def test_verify_password_correct():
    password = "test_password_123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)


def test_verify_password_incorrect():
    hashed = hash_password("correct_password")
    assert not verify_password("wrong_password", hashed)


# ===========================
# JWT Token Tests
# ===========================

def test_create_and_verify_token():
    token_data = {
        "sub": "test@test.com",
        "user_id": "test-123",
        "role": "Employee",
    }
    token = create_access_token(token_data)
    assert token is not None

    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "test@test.com"
    assert payload["user_id"] == "test-123"
    assert payload["role"] == "Employee"


def test_verify_token_invalid():
    payload = verify_token("invalid.token.string")
    assert payload is None


# ===========================
# Password Strength Validation Tests
# ===========================

def test_password_too_short():
    valid, error = validate_password_strength("short")
    assert not valid
    assert "at least 6 characters" in error


def test_password_valid_length():
    valid, error = validate_password_strength("long_enough_password")
    assert valid
    assert error == ""


def test_password_exactly_six_chars():
    valid, error = validate_password_strength("abcdef")
    assert valid
    assert error == ""


# ===========================
# Token Expiry Tests
# ===========================

def test_fresh_token_not_expired():
    token = create_access_token({"sub": "test@test.com"})
    assert not is_token_expired(token)


def test_get_token_expiry_returns_datetime():
    token = create_access_token({"sub": "test@test.com"})
    expiry = get_token_expiry(token)
    assert expiry is not None


def test_invalid_token_is_expired():
    assert is_token_expired("bad.token.value")


def test_invalid_token_expiry_is_none():
    assert get_token_expiry("bad.token.value") is None
