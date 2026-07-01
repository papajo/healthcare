"""Audit Ledger Service — F-06

Provides immutable, append-only event storage for compliance.
In production, this writes to Amazon QLDB. Here we use an in-memory
store for development and testing, with the same API surface.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from src.models.domain import (
    ActorType,
    AuditActor,
    AuditEntity,
    AuditEvent,
    AuditEventType,
    EntityType,
)


class AuditLedger:
    """In-memory audit ledger for development.
    
    In production, replace with QLDB client.
    """

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._last_digest: str = ""

    def write_event(
        self,
        event_type: AuditEventType,
        actor_type: ActorType,
        actor_id: str,
        entity_type: EntityType,
        entity_id: str,
        payload: dict | None = None,
        correlation_id: uuid4 | None = None,
    ) -> AuditEvent:
        """Write an immutable audit event to the ledger."""
        event = AuditEvent(
            event_type=event_type,
            actor=AuditActor(actor_type=actor_type, actor_id=actor_id),
            entity=AuditEntity(entity_type=entity_type, entity_id=entity_id),
            payload=payload or {},
            correlation_id=correlation_id,
        )

        # Compute integrity hash (SHA-256 of payload + metadata)
        hash_input = json.dumps(
            {
                "event_type": event.event_type.value,
                "event_timestamp": event.event_timestamp.isoformat(),
                "actor": {"type": event.actor.actor_type.value, "id": event.actor.actor_id},
                "entity": {"type": event.entity.entity_type.value, "id": event.entity.entity_id},
                "payload": event.payload,
            },
            sort_keys=True,
            default=str,
        )
        event.integrity_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        self._events.append(event)
        return event

    def query_events(
        self,
        event_type: AuditEventType | None = None,
        entity_type: EntityType | None = None,
        entity_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditEvent], int]:
        """Query audit events with optional filters."""
        filtered = self._events

        if event_type is not None:
            filtered = [e for e in filtered if e.event_type == event_type]
        if entity_type is not None:
            filtered = [e for e in filtered if e.entity.entity_type == entity_type]
        if entity_id is not None:
            filtered = [e for e in filtered if e.entity.entity_id == entity_id]

        total = len(filtered)
        return filtered[offset : offset + limit], total

    def get_event(self, event_id: str) -> AuditEvent | None:
        """Get a single audit event by ID."""
        for event in self._events:
            if str(event.event_id) == event_id:
                return event
        return None

    def verify_integrity(self) -> dict:
        """Verify the integrity of the audit chain.
        
        In production, this queries QLDB's ledger digest.
        Here we verify that all events have non-empty integrity hashes.
        """
        invalid_events = []
        for event in self._events:
            if not event.integrity_hash:
                invalid_events.append(str(event.event_id))

        return {
            "chain_status": "VALID" if not invalid_events else "INVALID",
            "total_events": len(self._events),
            "invalid_events": invalid_events,
            "verified_at": datetime.now(UTC).isoformat(),
        }

    def get_event_count(self) -> int:
        """Get total number of events in the ledger."""
        return len(self._events)


# Singleton instance for the application
audit_ledger = AuditLedger()
