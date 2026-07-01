"""Claims Service — in-memory claim store with lifecycle management.

Handles the full claim lifecycle:
DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED/PARTIAL/DENIED → SETTLED
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from src.models.domain import (
    ClaimCreateRequest,
    ClaimResponse,
    ClaimStatus,
    ClaimStatusUpdate,
)

logger = logging.getLogger(__name__)


class ClaimStore:
    """In-memory claim store."""

    def __init__(self):
        self._claims: dict[str, ClaimResponse] = {}

    def create_claim(self, request: ClaimCreateRequest) -> ClaimResponse:
        """Create a new claim from a request."""
        claim_id = uuid4()

        total_charged = sum(item.total_cents for item in request.line_items)

        claim = ClaimResponse(
            claim_id=claim_id,
            encounter_id=request.encounter_id,
            patient_pseudo_id=request.patient_pseudo_id,
            provider_org_id=request.provider_org_id,
            payer_id=request.payer_id,
            claim_type=request.claim_type,
            claim_status=ClaimStatus.DRAFT,
            service_date=request.service_date,
            line_items=request.line_items,
            diagnosis_codes=request.diagnosis_codes,
            total_charged_cents=total_charged,
            notes=request.notes,
        )

        self._claims[str(claim_id)] = claim
        logger.info("Claim created: %s (total: %d cents)", claim_id, total_charged)
        return claim

    def get_claim(self, claim_id: str) -> ClaimResponse | None:
        """Get a claim by ID."""
        return self._claims.get(claim_id)

    def list_claims(
        self,
        patient_pseudo_id: str | None = None,
        provider_org_id: str | None = None,
        claim_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ClaimResponse], int]:
        """List claims with optional filters."""
        results = list(self._claims.values())

        if patient_pseudo_id:
            results = [c for c in results if str(c.patient_pseudo_id) == patient_pseudo_id]
        if provider_org_id:
            results = [c for c in results if str(c.provider_org_id) == provider_org_id]
        if claim_status:
            results = [c for c in results if c.claim_status.value == claim_status]

        total = len(results)
        results = sorted(results, key=lambda c: c.created_at, reverse=True)
        results = results[offset : offset + limit]
        return results, total

    def update_status(self, claim_id: str, update: ClaimStatusUpdate) -> ClaimResponse | None:
        """Update claim status and optional financial fields."""
        claim = self._claims.get(claim_id)
        if claim is None:
            return None

        claim.claim_status = update.claim_status
        claim.updated_at = datetime.now(UTC)

        if update.insurance_responsibility_cents is not None:
            claim.insurance_responsibility_cents = update.insurance_responsibility_cents
        if update.patient_responsibility_cents is not None:
            claim.patient_responsibility_cents = update.patient_responsibility_cents
        if update.notes is not None:
            claim.notes = update.notes

        if update.claim_status == ClaimStatus.SETTLED:
            claim.settled_at = datetime.now(UTC)
            # Auto-calculate subsidy if not set
            if claim.subsidy_applied_cents == 0:
                claim.subsidy_applied_cents = max(
                    0,
                    claim.total_charged_cents
                    - claim.insurance_responsibility_cents
                    - claim.patient_responsibility_cents,
                )

        logger.info("Claim %s status → %s", claim_id, update.claim_status.value)
        return claim

    def submit_claim(self, claim_id: str) -> ClaimResponse | None:
        """Submit a draft claim for review."""
        return self.update_status(
            claim_id,
            ClaimStatusUpdate(claim_status=ClaimStatus.SUBMITTED),
        )

    def settle_claim(self, claim_id: str) -> ClaimResponse | None:
        """Mark a claim as settled."""
        return self.update_status(
            claim_id,
            ClaimStatusUpdate(claim_status=ClaimStatus.SETTLED),
        )

    def void_claim(self, claim_id: str) -> ClaimResponse | None:
        """Void a claim."""
        return self.update_status(
            claim_id,
            ClaimStatusUpdate(claim_status=ClaimStatus.VOIDED),
        )

    def get_summary(self) -> dict:
        """Get aggregate claim statistics."""
        claims = list(self._claims.values())
        total = len(claims)
        by_status = {}
        total_charged = 0
        total_insurance = 0
        total_patient = 0
        total_subsidy = 0

        for c in claims:
            status = c.claim_status.value
            by_status[status] = by_status.get(status, 0) + 1
            total_charged += c.total_charged_cents
            total_insurance += c.insurance_responsibility_cents
            total_patient += c.patient_responsibility_cents
            total_subsidy += c.subsidy_applied_cents

        return {
            "total_claims": total,
            "by_status": by_status,
            "total_charged_cents": total_charged,
            "total_insurance_responsibility_cents": total_insurance,
            "total_patient_responsibility_cents": total_patient,
            "total_subsidy_applied_cents": total_subsidy,
        }


# Singleton
claim_store = ClaimStore()
