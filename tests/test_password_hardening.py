"""
tests/test_password_hardening.py

Unit tests for PBKDF2-HMAC-SHA256 password hashing hardening,
legacy hash verification, and automatic rehash migration.
"""

import base64
import hashlib
import os
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    needs_rehash,
    DEFAULT_PBKDF2_ITERATIONS,
    LEGACY_PBKDF2_ITERATIONS,
)


def test_hash_format_and_algorithm():
    password = "CorrectHorseBatteryStaple123!"
    pw_hash = hash_password(password)

    parts = pw_hash.split("$")
    assert len(parts) == 4, f"Expected 4 parts in versioned hash, got {len(parts)}"
    assert parts[0] == "pbkdf2_sha256"
    assert int(parts[1]) == DEFAULT_PBKDF2_ITERATIONS
    assert len(parts[2]) == 32  # 16 bytes salt hex
    assert len(parts[3]) > 0  # base64 encoded digest

    assert verify_password(password, pw_hash) is True
    assert verify_password("WrongPassword123!", pw_hash) is False
    assert needs_rehash(pw_hash) is False


def test_legacy_two_part_hash_compatibility():
    password = "LegacyPasswordToVerify"
    legacy_salt = os.urandom(16).hex()
    legacy_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        legacy_salt.encode("utf-8"),
        LEGACY_PBKDF2_ITERATIONS,
    )
    legacy_b64 = base64.b64encode(legacy_digest).decode("ascii")
    legacy_hash = f"{legacy_salt}${legacy_b64}"

    # Verify backward compatibility
    assert verify_password(password, legacy_hash) is True
    assert verify_password("IncorrectGuess", legacy_hash) is False

    # Verify needs_rehash flags legacy hashes
    assert needs_rehash(legacy_hash) is True


def test_needs_rehash_iteration_upgrade():
    password = "UpgradeIterationTest"
    old_salt = os.urandom(16).hex()
    old_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        old_salt.encode("utf-8"),
        300000,
    )
    old_b64 = base64.b64encode(old_digest).decode("ascii")
    old_hash = f"pbkdf2_sha256$300000${old_salt}${old_b64}"

    assert verify_password(password, old_hash) is True
    assert needs_rehash(old_hash) is True

    # Current hash does not need rehash
    current_hash = hash_password(password)
    assert needs_rehash(current_hash) is False


def test_empty_or_malformed_hash():
    assert verify_password("test", "") is False
    assert verify_password("test", "malformed") is False
    assert verify_password("test", "a$b$c") is False
    assert needs_rehash("") is False
    assert needs_rehash("malformed") is True
    assert needs_rehash("oauth:google:12345") is False
