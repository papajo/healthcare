"""Database migration runner.

Runs DDL scripts to initialize or migrate the database schema.
"""

from __future__ import annotations

import logging

from src.db.connection import get_connection

logger = logging.getLogger(__name__)


# ─── Migration Scripts ───────────────────────────────────────────────────────

MIGRATIONS = [
    # (version, description, sql)
    (
        1,
        "Create audit_events table",
        """
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
        """,
    ),
    (
        2,
        "Create audit_events indexes",
        """
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
        """,
    ),
    (
        3,
        "Create migration tracking table",
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
    ),
    (
        4,
        "Create subsidy_records table",
        """
        CREATE TABLE IF NOT EXISTS subsidy_records (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            subsidy_id              VARCHAR(64) UNIQUE NOT NULL,
            encounter_id            VARCHAR(64) NOT NULL,
            patient_pseudo_id       VARCHAR(64) NOT NULL,
            provider_org_id         VARCHAR(64) NOT NULL,
            subsidy_amount_cents    BIGINT NOT NULL,
            subsidy_status          VARCHAR(32) NOT NULL DEFAULT 'PENDING',
            payment_method          VARCHAR(16),
            payment_reference       VARCHAR(128),
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            settled_at              TIMESTAMPTZ,
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_subsidy_encounter
            ON subsidy_records (encounter_id);
        CREATE INDEX IF NOT EXISTS idx_subsidy_patient
            ON subsidy_records (patient_pseudo_id);
        CREATE INDEX IF NOT EXISTS idx_subsidy_status
            ON subsidy_records (subsidy_status);
        """,
    ),
]


# ─── Migration Runner ────────────────────────────────────────────────────────


async def run_migrations():
    """Run all pending migrations."""
    async with get_connection() as conn:
        # Ensure migration table exists
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version     INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )

        # Get applied migrations
        applied = await conn.fetch(
            "SELECT version FROM schema_migrations ORDER BY version"
        )
        applied_versions = {row["version"] for row in applied}

        # Run pending migrations
        for version, description, sql in MIGRATIONS:
            if version not in applied_versions:
                logger.info("Running migration %d: %s", version, description)
                await conn.execute(sql)
                await conn.execute(
                    """
                    INSERT INTO schema_migrations (version, description)
                    VALUES ($1, $2)
                    """,
                    version,
                    description,
                )
                logger.info("Migration %d applied successfully", version)

        logger.info("All migrations up to date")
