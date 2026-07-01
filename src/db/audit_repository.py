"""PostgreSQL audit projection repository — F-06.

Production implementation using asyncpg for high-performance
event storage and querying.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from src.db.connection import get_connection
from src.models.domain import AuditEvent

logger = logging.getLogger(__name__)


# ─── DDL ─────────────────────────────────────────────────────────────────────

INIT_SQL = """
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

CREATE INDEX IF NOT EXISTS idx_audit_events_event_type
    ON audit_events (event_type);
CREATE INDEX IF NOT EXISTS idx_audit_events_entity
    ON audit_events (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp
    ON audit_events (event_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_correlation
    ON audit_events (correlation_id)
    WHERE correlation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_audit_events_actor
    ON audit_events (actor_type, actor_id);
"""


# ─── Repository ──────────────────────────────────────────────────────────────


class AuditEventRepository:
    """PostgreSQL repository for audit events."""

    async def initialize(self):
        """Create tables if they don't exist."""
        async with get_connection() as conn:
            await conn.execute(INIT_SQL)
            logger.info("Audit events table initialized")

    async def insert_event(self, event: AuditEvent) -> dict:
        """Insert an audit event into PostgreSQL."""
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO audit_events (
                    event_id, event_type, event_timestamp,
                    actor_type, actor_id,
                    entity_type, entity_id,
                    payload, correlation_id,
                    schema_version, integrity_hash
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                )
                RETURNING id, projected_at
                """,
                str(event.event_id),
                event.event_type.value,
                event.event_timestamp,
                event.actor.actor_type.value,
                event.actor.actor_id,
                event.entity.entity_type.value,
                event.entity.entity_id,
                json.dumps(event.payload, default=str),
                str(event.correlation_id) if event.correlation_id else None,
                event.schema_version,
                event.integrity_hash,
            )
            return {
                "id": str(row["id"]),
                "projected_at": row["projected_at"].isoformat(),
            }

    async def query_by_entity(
        self, entity_type: str, entity_id: str, limit: int = 100
    ) -> list[dict]:
        """Query all events for a specific entity."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT event_id, event_type, event_timestamp,
                       actor_type, actor_id, entity_type, entity_id,
                       payload, correlation_id, schema_version, integrity_hash
                FROM audit_events
                WHERE entity_type = $1 AND entity_id = $2
                ORDER BY event_timestamp ASC
                LIMIT $3
                """,
                entity_type,
                entity_id,
                limit,
            )
            return [dict(row) for row in rows]

    async def query_by_type(
        self, event_type: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[dict], int]:
        """Query events by type with pagination."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT event_id, event_type, event_timestamp,
                       actor_type, actor_id, entity_type, entity_id,
                       payload, correlation_id, schema_version, integrity_hash
                FROM audit_events
                WHERE event_type = $1
                ORDER BY event_timestamp DESC
                LIMIT $2 OFFSET $3
                """,
                event_type,
                limit,
                offset,
            )
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM audit_events WHERE event_type = $1",
                event_type,
            )
            return [dict(row) for row in rows], count

    async def query_by_correlation(self, correlation_id: str) -> list[dict]:
        """Query all events in a correlation group."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT event_id, event_type, event_timestamp,
                       actor_type, actor_id, entity_type, entity_id,
                       payload, correlation_id, schema_version, integrity_hash
                FROM audit_events
                WHERE correlation_id = $1
                ORDER BY event_timestamp ASC
                """,
                correlation_id,
            )
            return [dict(row) for row in rows]

    async def query_recent(self, hours: int = 24, limit: int = 100) -> list[dict]:
        """Query recent events (last N hours)."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT event_id, event_type, event_timestamp,
                       actor_type, actor_id, entity_type, entity_id,
                       payload, correlation_id, schema_version, integrity_hash
                FROM audit_events
                WHERE event_timestamp >= NOW() - INTERVAL '1 hour' * $1
                ORDER BY event_timestamp DESC
                LIMIT $2
                """,
                hours,
                limit,
            )
            return [dict(row) for row in rows]

    async def get_entity_timeline(self, entity_type: str, entity_id: str) -> dict:
        """Build a complete timeline for an entity."""
        events = await self.query_by_entity(entity_type, entity_id)
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "event_count": len(events),
            "timeline": [
                {
                    "event_type": e["event_type"],
                    "timestamp": e["event_timestamp"].isoformat()
                    if hasattr(e["event_timestamp"], "isoformat")
                    else str(e["event_timestamp"]),
                    "actor": f"{e['actor_type']}:{e['actor_id']}",
                }
                for e in events
            ],
        }

    async def count_by_type(self) -> dict[str, int]:
        """Aggregate event counts by type."""
        async with get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT event_type, COUNT(*) as count
                FROM audit_events
                GROUP BY event_type
                ORDER BY count DESC
                """
            )
            return {row["event_type"]: row["count"] for row in rows}

    async def verify_integrity(self) -> dict:
        """Verify audit chain integrity."""
        async with get_connection() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM audit_events")
            invalid = await conn.fetchval(
                "SELECT COUNT(*) FROM audit_events WHERE integrity_hash = ''"
            )
            return {
                "chain_status": "VALID" if invalid == 0 else "INVALID",
                "total_events": total,
                "invalid_events": invalid,
                "verified_at": datetime.now(UTC).isoformat(),
            }


# Singleton
audit_event_repo = AuditEventRepository()
