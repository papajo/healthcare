"""Subsidy Orchestrator API routes — F-03."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import CurrentUser, require_role
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

# ─── Subsidy Programs ────────────────────────────────────────────────────────

SUBSIDY_PROGRAMS = [
    {
        "program_id": "medicaid-state",
        "name": "State Medicaid",
        "source": "STATE",
        "min_income_fpl_percent": 0,
        "max_income_fpl_percent": 138,
        "max_assistance_usd": 50000,
        "priority": 1,
        "description": (
            "Joint federal and state program providing "
            "health coverage for low-income individuals."
        ),
    },
    {
        "program_id": "chip-state",
        "name": "CHIP (State Children's Health Insurance Program)",
        "source": "STATE",
        "min_income_fpl_percent": 200,
        "max_income_fpl_percent": 300,
        "max_assistance_usd": 25000,
        "priority": 2,
        "description": (
            "Health coverage for children in families "
            "with incomes too high for Medicaid."
        ),
    },
    {
        "program_id": "hospital-financial-assistance",
        "name": "Hospital Financial Assistance (Charity Care)",
        "source": "HOSPITAL",
        "min_income_fpl_percent": 0,
        "max_income_fpl_percent": 400,
        "max_assistance_usd": 75000,
        "priority": 3,
        "description": "Nonprofit hospitals must provide financial assistance under the ACA.",
    },
    {
        "program_id": "state-charity-care",
        "name": "State Charity Care Program",
        "source": "STATE",
        "min_income_fpl_percent": 0,
        "max_income_fpl_percent": 400,
        "max_assistance_usd": 40000,
        "priority": 4,
        "description": "State-funded program providing medical debt relief.",
    },
    {
        "program_id": "npo-grant-local",
        "name": "Local NPO Medical Grants",
        "source": "NPO",
        "min_income_fpl_percent": 0,
        "max_income_fpl_percent": 300,
        "max_assistance_usd": 15000,
        "priority": 5,
        "description": "Local nonprofit organizations providing medical grants.",
    },
    {
        "program_id": "npo-grant-national",
        "name": "National NPO Medical Grants",
        "source": "NPO",
        "min_income_fpl_percent": 0,
        "max_income_fpl_percent": 400,
        "max_assistance_usd": 20000,
        "priority": 6,
        "description": "National nonprofit organizations providing medical grants.",
    },
    {
        "program_id": "insurance-gap",
        "name": "Insurance Payment Gap Assistance",
        "source": "INSURANCE",
        "min_income_fpl_percent": 0,
        "max_income_fpl_percent": 999,
        "max_assistance_usd": 10000,
        "priority": 7,
        "description": "Assistance with insurance deductible and out-of-pocket maximum gaps.",
    },
]


@router.get(
    "/subsidies/programs",
    summary="List subsidy programs",
    description="List all available subsidy programs with eligibility criteria.",
)
async def list_subsidy_programs(
    user: CurrentUser,
    source: str | None = Query(
        default=None,
        description="Filter by source: STATE, HOSPITAL, NPO, INSURANCE",
    ),
):
    """List available subsidy programs."""
    programs = SUBSIDY_PROGRAMS
    if source:
        programs = [p for p in programs if p["source"] == source.upper()]
    return {"programs": programs, "total": len(programs)}


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
