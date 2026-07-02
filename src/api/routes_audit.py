"""Audit Ledger API routes — F-06."""

from fastapi import APIRouter, Depends, Query

from src.api.deps import require_role
from src.models.auth import UserRole
from src.models.domain import AuditEventType, EntityType
from src.services.audit_ledger import audit_ledger

router = APIRouter()


@router.get(
    "/audit/events",
    summary="Query audit events",
    description="Query audit events with optional filters (admin/system only).",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.SYSTEM))],
)
async def query_events(
    event_type: AuditEventType | None = Query(None, description="Filter by event type"),
    entity_type: EntityType | None = Query(None, description="Filter by entity type"),
    entity_id: str | None = Query(None, description="Filter by entity ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Query audit events."""
    events, total = audit_ledger.query_events(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "events": [e.model_dump() for e in events],
    }


@router.get(
    "/audit/events/{event_id}",
    summary="Get audit event",
    description="Get a single audit event by ID (admin/system only).",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.SYSTEM))],
)
async def get_event(event_id: str):
    """Get audit event by ID."""
    event = audit_ledger.get_event(event_id)
    if event is None:
        return {"error": "Event not found"}
    return event.model_dump()


@router.get(
    "/audit/verify",
    summary="Verify audit chain integrity",
    description="Verify the integrity of the audit event chain (admin/system only).",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.SYSTEM))],
)
async def verify_integrity():
    """Verify audit chain integrity."""
    return audit_ledger.verify_integrity()
