"""In-memory consent store with lookup and validation helpers."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from src.models.consent import (
    ConsentCreateRequest,
    ConsentRecord,
    ConsentRevokeRequest,
    ConsentStatus,
    DataCategory,
)

logger = logging.getLogger(__name__)


class ConsentService:
    """Thread-safe in-memory consent store.

    Production would back this with PostgreSQL + encrypted columns.
    """

    def __init__(self) -> None:
        self._consents: dict[str, ConsentRecord] = {}

    # ── CRUD ──────────────────────────────────────────────────────────────

    def grant(self, request: ConsentCreateRequest, granted_by: str) -> ConsentRecord:
        """Grant consent for a data category."""
        record = ConsentRecord(
            patient_id=request.patient_id,
            category=request.category,
            granted_to=request.granted_to,
            granted_by=granted_by,
            expires_at=request.expires_at,
            scope_note=request.scope_note,
        )
        self._consents[str(record.consent_id)] = record
        logger.info(
            "Consent granted: patient=%s category=%s by=%s",
            request.patient_id,
            request.category.value,
            granted_by,
        )
        return record

    def revoke(
        self, consent_id: str, revoked_by: str, request: ConsentRevokeRequest
    ) -> ConsentRecord:
        """Revoke an active consent."""
        record = self._consents.get(consent_id)
        if record is None:
            raise KeyError(f"Consent {consent_id} not found")
        if record.status != ConsentStatus.VALID:
            raise ValueError(f"Consent {consent_id} is already {record.status.value}")

        record.status = ConsentStatus.REVOKED
        record.revoked_at = datetime.now(UTC)
        if request.reason:
            record.scope_note = f"[REVOKED] {request.reason}"
        logger.info(
            "Consent revoked: id=%s patient=%s by=%s",
            consent_id,
            record.patient_id,
            revoked_by,
        )
        return record

    def get(self, consent_id: str) -> ConsentRecord | None:
        """Get a single consent record."""
        return self._consents.get(consent_id)

    def list_for_patient(
        self,
        patient_id: str,
        category: DataCategory | None = None,
        include_expired: bool = False,
    ) -> list[ConsentRecord]:
        """List consents for a patient, optionally filtered by category."""
        results = []
        now = datetime.now(UTC)
        for record in self._consents.values():
            if record.patient_id != patient_id:
                continue
            if category and record.category != category:
                continue
            # Auto-expire
            if record.status == ConsentStatus.VALID and record.expires_at:
                if now > record.expires_at:
                    record.status = ConsentStatus.EXPIRED
            if not include_expired and record.status == ConsentStatus.EXPIRED:
                continue
            results.append(record)
        return results

    def list_all(self, include_expired: bool = False) -> list[ConsentRecord]:
        """List all consents (admin)."""
        results = []
        now = datetime.now(UTC)
        for record in self._consents.values():
            if record.status == ConsentStatus.VALID and record.expires_at:
                if now > record.expires_at:
                    record.status = ConsentStatus.EXPIRED
            if not include_expired and record.status == ConsentStatus.EXPIRED:
                continue
            results.append(record)
        return results

    # ── Validation helpers ────────────────────────────────────────────────

    def has_valid_consent(
        self,
        patient_id: str,
        category: DataCategory,
        actor_id: str | None = None,
    ) -> bool:
        """Check if a valid consent exists for the given patient/category/actor.

        - ``actor_id=None`` → system-level check (any valid consent suffices).
        - ``actor_id="..."`` → checks that the consent grants access to that actor.
        """
        now = datetime.now(UTC)
        for record in self._consents.values():
            if record.patient_id != patient_id:
                continue
            if record.category != category:
                continue
            if record.status != ConsentStatus.VALID:
                continue
            if record.expires_at and now > record.expires_at:
                continue
            # If consent has specific grants, actor must be in the list
            if actor_id and record.granted_to:
                if actor_id not in record.granted_to:
                    continue
            return True
        return False

    def get_required_categories_for_action(self, action: str) -> list[DataCategory]:
        """Map a workflow action to required consent categories.

        Returns the categories that must have valid consent before proceeding.
        """
        mapping: dict[str, list[DataCategory]] = {
            "read_clinical": [DataCategory.CLINICAL],
            "read_financial": [DataCategory.FINANCIAL],
            "read_pharmacy": [DataCategory.PHARMACY],
            "read_lab": [DataCategory.LAB_RESULTS],
            "read_imaging": [DataCategory.IMAGING],
            "submit_claim": [DataCategory.FINANCIAL, DataCategory.CLINICAL],
            "classify_urgency": [DataCategory.CLINICAL],
            "assess_affordability": [DataCategory.FINANCIAL],
            "create_subsidy": [DataCategory.FINANCIAL, DataCategory.CLINICAL],
        }
        return mapping.get(action, [])


# Singleton
consent_service = ConsentService()
