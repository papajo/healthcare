"""Audit Ledger Service — F-06

Provides immutable, append-only event storage with cryptographic integrity.

Features:
- HMAC-SHA256 signing of every event
- Hash chain linking (each event's hash includes the previous event's hash)
- Monotonic timestamp validation
- Full chain verification (hash chain + HMAC signatures)

In production, this writes to Amazon QLDB. Here we use an in-memory
store for development and testing, with the same API surface.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from uuid import uuid4

from src.config.settings import settings
from src.models.domain import (
    ActorType,
    AuditActor,
    AuditEntity,
    AuditEvent,
    AuditEventType,
    EntityType,
)


class AuditLedger:
    """In-memory audit ledger with cryptographic chain integrity.

    In production, replace with QLDB client.
    """

    def __init__(self, signing_key: str | None = None) -> None:
        self._events: list[AuditEvent] = []
        self._last_digest: str = ""
        self._signing_key = (signing_key or settings.audit_signing_key).encode()
        self._last_timestamp: datetime | None = None

    # ── Signing ───────────────────────────────────────────────────────────

    def _sign(self, data: str) -> str:
        """Compute HMAC-SHA256 signature."""
        return hmac.new(self._signing_key, data.encode(), hashlib.sha256).hexdigest()

    def _compute_chain_hash(self, event_data: dict, previous_hash: str) -> str:
        """Compute hash for an event, including the previous hash for chain linking."""
        chain_input = {
            **event_data,
            "previous_hash": previous_hash,
        }
        payload_str = json.dumps(chain_input, sort_keys=True, default=str)
        return hashlib.sha256(payload_str.encode()).hexdigest()

    # ── Write ─────────────────────────────────────────────────────────────

    def write_event(
        self,
        event_type: AuditEventType | str,
        actor_type: ActorType | str,
        actor_id: str,
        entity_type: EntityType | str,
        entity_id: str,
        payload: dict | None = None,
        correlation_id: uuid4 | None = None,
    ) -> AuditEvent:
        """Write an immutable, signed audit event to the ledger."""
        # Resolve string enums to enum objects
        if isinstance(event_type, str):
            valid = event_type in AuditEventType.__members__.values()
            event_type = (
                AuditEventType(event_type) if valid
                else AuditEventType.SUBSIDY_CREATED
            )
        if isinstance(actor_type, str):
            valid = actor_type in ActorType.__members__.values()
            actor_type = (
                ActorType(actor_type) if valid
                else ActorType.SYSTEM
            )
        if isinstance(entity_type, str):
            valid = entity_type in EntityType.__members__.values()
            entity_type = (
                EntityType(entity_type) if valid
                else EntityType.SYSTEM
            )

        now = datetime.now(UTC)

        # Monotonic timestamp enforcement
        if self._last_timestamp is not None and now <= self._last_timestamp:
            # Advance by 1 microsecond to maintain strict monotonicity
            now = self._last_timestamp.replace(
                microsecond=min(self._last_timestamp.microsecond + 1, 999999)
            )
        self._last_timestamp = now

        event = AuditEvent(
            event_type=event_type,
            event_timestamp=now,
            actor=AuditActor(actor_type=actor_type, actor_id=actor_id),
            entity=AuditEntity(entity_type=entity_type, entity_id=entity_id),
            payload=payload or {},
            correlation_id=correlation_id,
        )

        # Build canonical event data for hashing
        event_data = {
            "event_id": str(event.event_id),
            "event_type": event.event_type.value,
            "event_timestamp": event.event_timestamp.isoformat(),
            "actor": {
                "type": event.actor.actor_type.value,
                "id": event.actor.actor_id,
            },
            "entity": {
                "type": event.entity.entity_type.value,
                "id": event.entity.entity_id,
            },
            "payload": event.payload,
            "schema_version": event.schema_version,
        }

        # Compute chain hash (includes previous event's hash)
        event.integrity_hash = self._compute_chain_hash(event_data, self._last_digest)
        self._last_digest = event.integrity_hash

        # Compute HMAC signature
        event_signature = self._sign(event.integrity_hash)
        event.payload["_signature"] = event_signature

        self._events.append(event)
        return event

    # ── Query ─────────────────────────────────────────────────────────────

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

    # ── Integrity Verification ────────────────────────────────────────────

    def verify_integrity(self) -> dict:
        """Verify the full audit chain integrity.

        Checks:
        1. Every event has a non-empty integrity hash
        2. Hash chain links are valid (each event's previous_hash matches the prior event)
        3. HMAC signatures are valid
        4. Timestamps are strictly monotonic
        """
        invalid_events = []
        broken_chain_events = []
        bad_signature_events = []
        timestamp_violations = []
        prev_hash = ""
        prev_timestamp: datetime | None = None

        for _i, event in enumerate(self._events):
            event_id = str(event.event_id)

            # 1. Hash exists
            if not event.integrity_hash:
                invalid_events.append(event_id)
                continue

            # 2. Verify hash chain link
            event_data = {
                "event_id": str(event.event_id),
                "event_type": event.event_type.value,
                "event_timestamp": event.event_timestamp.isoformat(),
                "actor": {
                    "type": event.actor.actor_type.value,
                    "id": event.actor.actor_id,
                },
                "entity": {
                    "type": event.entity.entity_type.value,
                    "id": event.entity.entity_id,
                },
                "payload": {k: v for k, v in event.payload.items() if k != "_signature"},
                "schema_version": event.schema_version,
            }
            expected_hash = self._compute_chain_hash(event_data, prev_hash)
            if event.integrity_hash != expected_hash:
                broken_chain_events.append(event_id)

            # 3. Verify HMAC signature
            signature = event.payload.get("_signature", "")
            expected_signature = self._sign(event.integrity_hash)
            if not hmac.compare_digest(signature, expected_signature):
                bad_signature_events.append(event_id)

            # 4. Monotonic timestamps
            if prev_timestamp is not None and event.event_timestamp <= prev_timestamp:
                timestamp_violations.append(event_id)

            prev_hash = event.integrity_hash
            prev_timestamp = event.event_timestamp

        all_valid = (
            not invalid_events
            and not broken_chain_events
            and not bad_signature_events
            and not timestamp_violations
        )

        return {
            "chain_status": "VALID" if all_valid else "COMPROMISED",
            "total_events": len(self._events),
            "invalid_events": invalid_events,
            "broken_chain_events": broken_chain_events,
            "bad_signature_events": bad_signature_events,
            "timestamp_violations": timestamp_violations,
            "verified_at": datetime.now(UTC).isoformat(),
        }

    def get_event_count(self) -> int:
        """Get total number of events in the ledger."""
        return len(self._events)


# Singleton instance for the application
audit_ledger = AuditLedger()
