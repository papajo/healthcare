"""Subsidy Orchestrator API routes — F-03."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import require_role
from src.models.auth import UserRole
from src.models.domain import (
    ActorType,
    AuditEventType,
    EntityType,
    SubsidyCreationRequest,
    SubsidyResponse,
)
from src.services.audit_ledger import audit_ledger
from src.services.subsidy_orchestrator import subsidy_store

router = APIRouter()


@router.post(
    "/subsidies",
    response_model=SubsidyResponse,
    summary="Create a subsidy record",
    description="Create a new subsidy record and initiate payment workflow.",
    dependencies=[Depends(require_role(UserRole.CLINICIAN, UserRole.NURSE, UserRole.ADMIN))],
)
async def create_subsidy(request: SubsidyCreationRequest):
    """Create a subsidy record."""
    subsidy = subsidy_store.create_subsidy(request)

    # Emit audit event
    audit_ledger.write_event(
        event_type=AuditEventType.SUBSIDY_CREATED,
        actor_type=ActorType.SYSTEM,
        actor_id="subsidy-orchestrator",
        entity_type=EntityType.SUBSIDY,
        entity_id=str(subsidy.subsidy_id),
        payload={
            "encounter_id": subsidy.encounter_id,
            "patient_pseudo_id": str(subsidy.patient_pseudo_id),
            "provider_org_id": str(subsidy.provider_org_id),
            "subsidy_amount_cents": subsidy.subsidy_amount_cents,
            "payment_method": subsidy.payment_method.value if subsidy.payment_method else None,
        },
    )

    return subsidy


@router.get(
    "/subsidies/{subsidy_id}",
    response_model=SubsidyResponse,
    summary="Get subsidy status",
    description="Get the current status of a subsidy.",
    dependencies=[Depends(require_role(UserRole.CLINICIAN, UserRole.NURSE, UserRole.ADMIN))],
)
async def get_subsidy(subsidy_id: UUID):
    """Get subsidy by ID."""
    subsidy = subsidy_store.get_subsidy(str(subsidy_id))
    if subsidy is None:
        raise HTTPException(status_code=404, detail="Subsidy not found")
    return subsidy


@router.post(
    "/subsidies/{subsidy_id}/settle",
    response_model=SubsidyResponse,
    summary="Settle a subsidy",
    description="Mark a subsidy as settled after successful payment.",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def settle_subsidy(subsidy_id: UUID):
    """Settle a subsidy."""
    subsidy = subsidy_store.settle_subsidy(str(subsidy_id))
    if subsidy is None:
        raise HTTPException(status_code=404, detail="Subsidy not found")

    audit_ledger.write_event(
        event_type=AuditEventType.SUBSIDY_SETTLED,
        actor_type=ActorType.SYSTEM,
        actor_id="payment-processor",
        entity_type=EntityType.SUBSIDY,
        entity_id=str(subsidy.subsidy_id),
        payload={
            "payment_reference": subsidy.payment_reference,
            "settlement_time": subsidy.settled_at.isoformat(),
        },
    )

    return subsidy


@router.post(
    "/subsidies/{subsidy_id}/cancel",
    response_model=SubsidyResponse,
    summary="Cancel a subsidy",
    description="Cancel a pending subsidy.",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def cancel_subsidy(subsidy_id: UUID, reason: str = "cancelled"):
    """Cancel a pending subsidy."""
    subsidy = subsidy_store.cancel_subsidy(str(subsidy_id), reason)
    if subsidy is None:
        raise HTTPException(status_code=404, detail="Subsidy not found")

    audit_ledger.write_event(
        event_type=AuditEventType.SUBSIDY_CANCELLED,
        actor_type=ActorType.OPERATOR,
        actor_id="system-operator",
        entity_type=EntityType.SUBSIDY,
        entity_id=str(subsidy.subsidy_id),
        payload={"reason": reason},
    )

    return subsidy
