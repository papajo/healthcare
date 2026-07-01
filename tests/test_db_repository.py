"""Tests for PostgreSQL audit repository — F-06.

Uses a test database or mock to verify repository operations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.models.domain import ActorType, AuditActor, AuditEntity, AuditEvent, EntityType

# ─── Helpers ──────────────────────────────────────────────────────────────────


def make_audit_event(**overrides) -> AuditEvent:
    """Create a test audit event."""
    defaults = {
        "event_type": "SUBSIDY_CREATED",
        "actor": AuditActor(actor_type=ActorType.SYSTEM, actor_id="coordinator-001"),
        "entity": AuditEntity(entity_type=EntityType.SUBSIDY, entity_id=str(uuid4())),
        "payload": {"amount": 50000},
    }
    defaults.update(overrides)
    return AuditEvent(**defaults)


# ─── Unit Tests (mocked DB) ──────────────────────────────────────────────────


class TestAuditEventRepositoryUnit:
    """Test repository logic with mocked asyncpg connection."""

    @pytest.fixture
    def mock_conn(self):
        """Mock asyncpg connection."""
        conn = AsyncMock()
        return conn

    @pytest.mark.asyncio
    async def test_insert_event(self, mock_conn):
        """Should insert event and return projected metadata."""
        from src.db.audit_repository import AuditEventRepository

        repo = AuditEventRepository()
        event = make_audit_event()

        # Mock fetchrow return
        mock_conn.fetchrow = AsyncMock(
            return_value={"id": uuid4(), "projected_at": datetime.now(UTC)}
        )

        with patch(
            "src.db.audit_repository.get_connection"
        ) as mock_get_conn:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_get_conn.return_value = mock_ctx

            result = await repo.insert_event(event)

            assert "id" in result
            assert "projected_at" in result
            mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_by_entity(self, mock_conn):
        """Should return events for a given entity."""
        from src.db.audit_repository import AuditEventRepository

        repo = AuditEventRepository()

        now = datetime.now(UTC)
        mock_conn.fetch = AsyncMock(
            return_value=[
                {
                    "event_id": str(uuid4()),
                    "event_type": "SUBSIDY_CREATED",
                    "event_timestamp": now,
                    "actor_type": "SYSTEM",
                    "actor_id": "test",
                    "entity_type": "SUBSIDY",
                    "entity_id": "sub-123",
                    "payload": {},
                    "correlation_id": None,
                    "schema_version": "1.0.0",
                    "integrity_hash": "abc123",
                }
            ]
        )

        with patch(
            "src.db.audit_repository.get_connection"
        ) as mock_get_conn:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_get_conn.return_value = mock_ctx

            events = await repo.query_by_entity("SUBSIDY", "sub-123")

            assert len(events) == 1
            assert events[0]["event_type"] == "SUBSIDY_CREATED"

    @pytest.mark.asyncio
    async def test_query_by_type_with_pagination(self, mock_conn):
        """Should return events with count for pagination."""
        from src.db.audit_repository import AuditEventRepository

        repo = AuditEventRepository()
        now = datetime.now(UTC)

        mock_conn.fetch = AsyncMock(
            return_value=[
                {
                    "event_id": str(uuid4()),
                    "event_type": "SUBSIDY_SETTLED",
                    "event_timestamp": now,
                    "actor_type": "SYSTEM",
                    "actor_id": "test",
                    "entity_type": "SUBSIDY",
                    "entity_id": "sub-456",
                    "payload": {},
                    "correlation_id": None,
                    "schema_version": "1.0.0",
                    "integrity_hash": "def456",
                }
            ]
        )
        mock_conn.fetchval = AsyncMock(return_value=42)

        with patch(
            "src.db.audit_repository.get_connection"
        ) as mock_get_conn:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_get_conn.return_value = mock_ctx

            events, count = await repo.query_by_type("SUBSIDY_SETTLED")

            assert len(events) == 1
            assert count == 42

    @pytest.mark.asyncio
    async def test_verify_integrity_valid(self, mock_conn):
        """Should return VALID when no empty hashes."""
        from src.db.audit_repository import AuditEventRepository

        repo = AuditEventRepository()
        mock_conn.fetchval = AsyncMock(side_effect=[100, 0])

        with patch(
            "src.db.audit_repository.get_connection"
        ) as mock_get_conn:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_get_conn.return_value = mock_ctx

            result = await repo.verify_integrity()

            assert result["chain_status"] == "VALID"
            assert result["total_events"] == 100
            assert result["invalid_events"] == 0

    @pytest.mark.asyncio
    async def test_verify_integrity_invalid(self, mock_conn):
        """Should return INVALID when empty hashes exist."""
        from src.db.audit_repository import AuditEventRepository

        repo = AuditEventRepository()
        mock_conn.fetchval = AsyncMock(side_effect=[100, 3])

        with patch(
            "src.db.audit_repository.get_connection"
        ) as mock_get_conn:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_get_conn.return_value = mock_ctx

            result = await repo.verify_integrity()

            assert result["chain_status"] == "INVALID"
            assert result["invalid_events"] == 3

    @pytest.mark.asyncio
    async def test_count_by_type(self, mock_conn):
        """Should aggregate event counts."""
        from src.db.audit_repository import AuditEventRepository

        repo = AuditEventRepository()
        mock_conn.fetch = AsyncMock(
            return_value=[
                {"event_type": "SUBSIDY_CREATED", "count": 50},
                {"event_type": "SUBSIDY_SETTLED", "count": 45},
                {"event_type": "SUBSIDY_CANCELLED", "count": 5},
            ]
        )

        with patch(
            "src.db.audit_repository.get_connection"
        ) as mock_get_conn:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_get_conn.return_value = mock_ctx

            counts = await repo.count_by_type()

            assert counts["SUBSIDY_CREATED"] == 50
            assert counts["SUBSIDY_SETTLED"] == 45
            assert counts["SUBSIDY_CANCELLED"] == 5

    @pytest.mark.asyncio
    async def test_get_entity_timeline(self, mock_conn):
        """Should build timeline from entity events."""
        from src.db.audit_repository import AuditEventRepository

        repo = AuditEventRepository()
        now = datetime.now(UTC)

        mock_conn.fetch = AsyncMock(
            return_value=[
                {
                    "event_id": str(uuid4()),
                    "event_type": "SUBSIDY_CREATED",
                    "event_timestamp": now,
                    "actor_type": "SYSTEM",
                    "actor_id": "test",
                    "entity_type": "SUBSIDY",
                    "entity_id": "sub-789",
                    "payload": {},
                    "correlation_id": None,
                    "schema_version": "1.0.0",
                    "integrity_hash": "ghi789",
                },
                {
                    "event_id": str(uuid4()),
                    "event_type": "SUBSIDY_SETTLED",
                    "event_timestamp": now,
                    "actor_type": "SYSTEM",
                    "actor_id": "test",
                    "entity_type": "SUBSIDY",
                    "entity_id": "sub-789",
                    "payload": {},
                    "correlation_id": None,
                    "schema_version": "1.0.0",
                    "integrity_hash": "jkl012",
                },
            ]
        )

        with patch(
            "src.db.audit_repository.get_connection"
        ) as mock_get_conn:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_get_conn.return_value = mock_ctx

            timeline = await repo.get_entity_timeline("SUBSIDY", "sub-789")

            assert timeline["event_count"] == 2
            assert timeline["timeline"][0]["event_type"] == "SUBSIDY_CREATED"
            assert timeline["timeline"][1]["event_type"] == "SUBSIDY_SETTLED"


# ─── Migration Tests ─────────────────────────────────────────────────────────


class TestMigrations:
    """Test migration runner logic."""

    def test_migrations_list_has_versions(self):
        """All migrations have version numbers."""
        from src.db.migrations import MIGRATIONS

        versions = [m[0] for m in MIGRATIONS]
        assert len(versions) == len(set(versions)), "Duplicate migration versions"
        assert versions == sorted(versions), "Migrations must be in order"

    def test_migrations_have_sql(self):
        """All migrations have non-empty SQL."""
        from src.db.migrations import MIGRATIONS

        for version, description, sql in MIGRATIONS:
            assert sql.strip(), f"Migration {version} has empty SQL"
            assert description, f"Migration {version} has no description"
