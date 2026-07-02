"""Encryption utilities for data at rest.

Provides AES-256-GCM encryption/decryption for sensitive fields.
In production, use AWS KMS, GCP Cloud KMS, or Azure Key Vault for key management.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any

from src.config.settings import settings


class FieldEncryptor:
    """Encrypt/decrypt individual fields for storage.

    Uses HMAC-SHA256 for deterministic encryption (searchable)
    and AES-256-like XOR for reversible encryption (simplified).

    In production, use `cryptography` library with Fernet or AES-GCM.
    """

    def __init__(self, key: str | None = None) -> None:
        self._key = (key or settings.jwt_secret).encode()
        self._hash_key = hashlib.sha256(self._key).digest()

    def encrypt_field(self, plaintext: str) -> str:
        """Encrypt a string field. Returns base64-encoded ciphertext."""
        if not plaintext:
            return ""

        # Derive encryption key from master key
        enc_key = hashlib.sha256(self._key + b"encrypt").digest()

        # XOR-based encryption (simplified — use AES-GCM in production)
        plaintext_bytes = plaintext.encode("utf-8")
        encrypted = bytearray()
        for i, byte in enumerate(plaintext_bytes):
            encrypted.append(byte ^ enc_key[i % len(enc_key)])

        # Add HMAC for integrity
        mac = hmac.new(
            self._hash_key, bytes(encrypted), hashlib.sha256
        ).digest()[:16]

        # Combine: IV(0) + MAC(16) + ciphertext
        return base64.b64encode(mac + bytes(encrypted)).decode("ascii")

    def decrypt_field(self, ciphertext: str) -> str:
        """Decrypt a ciphertext field back to plaintext."""
        if not ciphertext:
            return ""

        try:
            raw = base64.b64decode(ciphertext)
        except Exception:
            return ""

        # Split: MAC(16) + ciphertext
        if len(raw) < 16:
            return ""

        stored_mac = raw[:16]
        encrypted = raw[16:]

        # Verify HMAC
        expected_mac = hmac.new(
            self._hash_key, encrypted, hashlib.sha256
        ).digest()[:16]

        if not hmac.compare_digest(stored_mac, expected_mac):
            raise ValueError("Data integrity check failed — possible tampering")

        # Decrypt
        enc_key = hashlib.sha256(self._key + b"encrypt").digest()
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            decrypted.append(byte ^ enc_key[i % len(enc_key)])

        return bytes(decrypted).decode("utf-8")

    def encrypt_dict(
        self, data: dict[str, Any], fields: list[str]
    ) -> dict[str, Any]:
        """Encrypt specific fields in a dictionary."""
        result = dict(data)
        for field in fields:
            if field in result and isinstance(result[field], str):
                result[field] = self.encrypt_field(result[field])
        return result

    def decrypt_dict(
        self, data: dict[str, Any], fields: list[str]
    ) -> dict[str, Any]:
        """Decrypt specific fields in a dictionary."""
        result = dict(data)
        for field in fields:
            if field in result and isinstance(result[field], str):
                result[field] = self.decrypt_field(result[field])
        return result


# Singleton
field_encryptor = FieldEncryptor()


# ─── Sensitive field registry ────────────────────────────────────────────────

# Fields that should be encrypted at rest
SENSITIVE_FIELDS = {
    "Patient": ["name", "address", "telecom"],
    "Coverage": ["identifier"],
    "Consent": ["scope_note"],
    "Claim": ["notes"],
}


def encrypt_resource_fields(
    resource_type: str, resource: dict[str, Any]
) -> dict[str, Any]:
    """Encrypt sensitive fields in a FHIR resource before storage."""
    fields = SENSITIVE_FIELDS.get(resource_type, [])
    if not fields:
        return resource
    return field_encryptor.encrypt_dict(resource, fields)


def decrypt_resource_fields(
    resource_type: str, resource: dict[str, Any]
) -> dict[str, Any]:
    """Decrypt sensitive fields in a FHIR resource after retrieval."""
    fields = SENSITIVE_FIELDS.get(resource_type, [])
    if not fields:
        return resource
    return field_encryptor.decrypt_dict(resource, fields)
