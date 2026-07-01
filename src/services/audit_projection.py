"""PostgreSQL projection for audit events — F-06.

In production, QLDB is the source of truth. This projection provides
operational queries against a PostgreSQL read model. Events flow from
QLDB → DynamoDB Streams → Lambda → PostgreSQL (projection pattern).

This module provides the schema DDL and query interface.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

# ─── Projection Schema ───────────────────────────────────────────────────────


class AuditEventRow(BaseModel):
    """Row in the PostgreSQL audit_events projection table."""

    id: uuid4 = Field(default_factory=uuid4)
    event_id: str
    event_type: str
    event_timestamp: datetime
    actor_type: str
    actor_id: str
    entity_type: str
    entity_id: str
    payload: dict = Field(default_factory=dict)
    correlation_id: str | None = None
    schema_version: str = "1.0.0"
    integrity_hash: str = ""
    projected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ─── DDL (for reference / migration tools) ──────────────────────────────────

AUDIT_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS audit_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id            VARCHAR(64) UNIQUE NOT NULL,
    event_type          VARCHAR(64) NOT NULL,
    event_timestamp     TIMESTAMPTZ NOT NULL,
    actor_type          VARCHAR(32) NOT NULL,
    actor_id            VARCHAR(128) NOT NULL,
    entity_type         VARCHAR(32) NOT NULL,
    entity_id           VARCHAR(128) NOT NULL,
    payload             JSONB NOT NULL DEFAULT '{}',
    correlation_id      VARCHAR(64),
    schema_version      VARCHAR(16) NOT NULL DEFAULT '1.0.0',
    integrity_hash      VARCHAR(64) NOT NULL,
    projected_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_audit_events_event_type ON audit_events (event_type);
CREATE INDEX IF NOT EXISTS idx_audit_events_entity ON audit_events (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events (event_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_correlation
    ON audit_events (correlation_id)
    WHERE correlation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_audit_events_actor ON audit_events (actor_type, actor_id);

-- Daily digest verification table
CREATE TABLE IF NOT EXISTS audit_daily_digests (
    digest_date     DATE PRIMARY KEY,
    event_count     INTEGER NOT NULL,
    first_event_id  VARCHAR(64) NOT NULL,
    last_event_id   VARCHAR(64) NOT NULL,
    computed_hash   VARCHAR(64) NOT NULL,
    verified_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


# ─── Projection Writer (in-memory for dev) ──────────────────────────────────


class AuditProjection:
    """In-memory projection for development.
    
    In production, this writes to PostgreSQL via async driver (asyncpg).
    """

    def __init__(self) -> None:
        self._rows: list[AuditEventRow] = []

    def project_event(self, event_dict: dict) -> AuditEventRow:
        """Project an audit event into the read model."""
        # Convert UUID objects to strings
        event_id = event_dict.get("event_id", str(uuid4()))
        correlation_id = event_dict.get("correlation_id")

        row = AuditEventRow(
            event_id=str(event_id),
            event_type=event_dict.get("event_type", "UNKNOWN"),
            event_timestamp=event_dict.get("event_timestamp", datetime.now(UTC)),
            actor_type=event_dict.get("actor", {}).get("actor_type", "SYSTEM"),
            actor_id=event_dict.get("actor", {}).get("actor_id", "unknown"),
            entity_type=event_dict.get("entity", {}).get("entity_type", "SYSTEM"),
            entity_id=event_dict.get("entity", {}).get("entity_id", "unknown"),
            payload=event_dict.get("payload", {}),
            correlation_id=str(correlation_id) if correlation_id else None,
            schema_version=event_dict.get("schema_version", "1.0.0"),
            integrity_hash=event_dict.get("integrity_hash", ""),
        )
        self._rows.append(row)
        return row

    def query_by_entity(
        self, entity_type: str, entity_id: str, limit: int = 100
    ) -> list[AuditEventRow]:
        """Query all events for a specific entity (full lifecycle trace)."""
        return [
            row
            for row in self._rows
            if row.entity_type == entity_type and row.entity_id == entity_id
        ][:limit]

    def query_by_type(
        self, event_type: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[AuditEventRow], int]:
        """Query events by type with pagination."""
        filtered = [row for row in self._rows if row.event_type == event_type]
        return filtered[offset : offset + limit], len(filtered)

    def query_by_correlation(self, correlation_id: str) -> list[AuditEventRow]:
        """Query all events in a correlation group (e.g., one encounter flow)."""
        return [
            row for row in self._rows if row.correlation_id == correlation_id
        ]

    def query_recent(self, hours: int = 24, limit: int = 100) -> list[AuditEventRow]:
        """Query recent events (last N hours)."""
        now = datetime.now(UTC)
        cutoff = now.replace(hour=max(0, now.hour - hours))
        return [
            row for row in self._rows if row.event_timestamp >= cutoff
        ][:limit]

    def get_entity_timeline(self, entity_type: str, entity_id: str) -> dict:
        """Build a complete timeline for an entity (for compliance review)."""
        events = self.query_by_entity(entity_type, entity_id)
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "event_count": len(events),
            "timeline": [
                {
                    "event_type": e.event_type,
                    "timestamp": e.event_timestamp.isoformat(),
                    "actor": f"{e.actor_type}:{e.actor_id}",
                }
                for e in events
            ],
        }

    def count_by_type(self) -> dict[str, int]:
        """Aggregate event counts by type."""
        counts: dict[str, int] = {}
        for row in self._rows:
            counts[row.event_type] = counts.get(row.event_type, 0) + 1
        return counts


# Singleton
audit_projection = AuditProjection()
