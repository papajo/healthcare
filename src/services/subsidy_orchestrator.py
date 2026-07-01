"""Subsidy Orchestrator Service — F-03

Manages the lifecycle of subsidy payments from the platform to providers.
In production, this runs through Temporal.io workflows. Here we implement
the core state machine for development and testing.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from src.models.domain import (
    PaymentMethod,
    SubsidyCreationRequest,
    SubsidyResponse,
    SubsidyStatus,
)

# ─── Payment Method Selection ────────────────────────────────────────────────

WIRE_THRESHOLD_CENTS = 10_000_000  # $100,000
STABLECOIN_THRESHOLD_CENTS = 50_000_000  # $500,000


def _determine_payment_method(subsidy_amount_cents: int) -> PaymentMethod:
    """Select the appropriate payment rail based on amount."""
    if subsidy_amount_cents >= STABLECOIN_THRESHOLD_CENTS:
        return PaymentMethod.STABLECOIN
    if subsidy_amount_cents >= WIRE_THRESHOLD_CENTS:
        return PaymentMethod.WIRE
    return PaymentMethod.ACH


# ─── Subsidy Store (in-memory for dev) ───────────────────────────────────────


class SubsidyStore:
    """In-memory subsidy store for development.
    
    In production, replace with PostgreSQL + Temporal.
    """

    def __init__(self) -> None:
        self._subsidies: dict[str, SubsidyResponse] = {}

    def create_subsidy(self, request: SubsidyCreationRequest) -> SubsidyResponse:
        """Create a new subsidy record."""
        payment_method = _determine_payment_method(request.subsidy_amount_cents)

        subsidy = SubsidyResponse(
            encounter_id=request.encounter_id,
            patient_pseudo_id=request.patient_pseudo_id,
            provider_org_id=request.provider_org_id,
            subsidy_amount_cents=request.subsidy_amount_cents,
            subsidy_status=SubsidyStatus.PENDING,
            payment_method=payment_method,
        )

        self._subsidies[str(subsidy.subsidy_id)] = subsidy
        return subsidy

    def get_subsidy(self, subsidy_id: str) -> SubsidyResponse | None:
        """Get a subsidy by ID."""
        return self._subsidies.get(subsidy_id)

    def list_subsidies(
        self,
        encounter_id: str | None = None,
        patient_pseudo_id: str | None = None,
        status: SubsidyStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SubsidyResponse], int]:
        """List subsidies with optional filters."""
        filtered = list(self._subsidies.values())

        if encounter_id is not None:
            filtered = [s for s in filtered if s.encounter_id == encounter_id]
        if patient_pseudo_id is not None:
            filtered = [s for s in filtered if str(s.patient_pseudo_id) == patient_pseudo_id]
        if status is not None:
            filtered = [s for s in filtered if s.subsidy_status == status]

        total = len(filtered)
        return filtered[offset : offset + limit], total

    def cancel_subsidy(self, subsidy_id: str, reason: str) -> SubsidyResponse | None:
        """Cancel a pending subsidy."""
        subsidy = self._subsidies.get(subsidy_id)
        if subsidy is None:
            return None

        if subsidy.subsidy_status not in (SubsidyStatus.PENDING, SubsidyStatus.VALIDATING):
            raise ValueError(
                f"Cannot cancel subsidy in status {subsidy.subsidy_status.value}"
            )

        subsidy.subsidy_status = SubsidyStatus.CANCELLED
        return subsidy

    def settle_subsidy(self, subsidy_id: str) -> SubsidyResponse | None:
        """Settle a subsidy (simulate successful payment)."""
        subsidy = self._subsidies.get(subsidy_id)
        if subsidy is None:
            return None

        subsidy.subsidy_status = SubsidyStatus.SETTLED
        subsidy.settled_at = datetime.now(UTC)
        subsidy.payment_reference = f"pay-{uuid4().hex[:12]}"
        return subsidy

    def get_reconciliation(self, date: str) -> dict:
        """Get daily reconciliation summary."""
        all_subsidies = list(self._subsidies.values())

        total_created = len(all_subsidies)
        total_settled = sum(1 for s in all_subsidies if s.subsidy_status == SubsidyStatus.SETTLED)
        total_failed = sum(1 for s in all_subsidies if s.subsidy_status == SubsidyStatus.FAILED)
        total_pending = sum(
            1
            for s in all_subsidies
            if s.subsidy_status in (SubsidyStatus.PENDING, SubsidyStatus.PROCESSING)
        )
        total_amount_settled = sum(
            s.subsidy_amount_cents
            for s in all_subsidies
            if s.subsidy_status == SubsidyStatus.SETTLED
        )

        return {
            "reconciliation_date": date,
            "total_created": total_created,
            "total_settled": total_settled,
            "total_failed": total_failed,
            "total_pending": total_pending,
            "total_amount_settled_cents": total_amount_settled,
            "mismatches": [],
        }


# Singleton instance for the application
subsidy_store = SubsidyStore()
