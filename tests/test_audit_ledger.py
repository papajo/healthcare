"""Tests for Audit Ledger Service — F-06."""


import pytest

from src.models.domain import (
    ActorType,
    AuditEventType,
    EntityType,
)
from src.services.audit_ledger import AuditLedger


@pytest.fixture
def ledger():
    """Create a fresh audit ledger for each test."""
    return AuditLedger()


def test_write_event(ledger):
    """Audit event can be written and retrieved."""
    event = ledger.write_event(
        event_type=AuditEventType.ENCOUNTER_INGESTED,
        actor_type=ActorType.PROVIDER_EHR,
        actor_id="ehr-001",
        entity_type=EntityType.ENCOUNTER,
        entity_id="enc-123",
    )
    assert event.event_type == AuditEventType.ENCOUNTER_INGESTED
    assert event.integrity_hash != ""


def test_integrity_hash_is_sha256(ledger):
    """Integrity hash is a valid SHA-256 hex string."""
    event = ledger.write_event(
        event_type=AuditEventType.ENCOUNTER_INGESTED,
        actor_type=ActorType.SYSTEM,
        actor_id="sys",
        entity_type=EntityType.ENCOUNTER,
        entity_id="e1",
    )
    assert len(event.integrity_hash) == 64  # SHA-256 hex = 64 chars


def test_query_events_filters_by_type(ledger):
    """Events can be filtered by event type."""
    ledger.write_event(
        event_type=AuditEventType.ENCOUNTER_INGESTED,
        actor_type=ActorType.SYSTEM,
        actor_id="sys",
        entity_type=EntityType.ENCOUNTER,
        entity_id="e1",
    )
    ledger.write_event(
        event_type=AuditEventType.SUBSIDY_CREATED,
        actor_type=ActorType.SYSTEM,
        actor_id="sys",
        entity_type=EntityType.SUBSIDY,
        entity_id="s1",
    )

    events, total = ledger.query_events(event_type=AuditEventType.ENCOUNTER_INGESTED)
    assert total == 1
    assert events[0].event_type == AuditEventType.ENCOUNTER_INGESTED


def test_query_events_filters_by_entity(ledger):
    """Events can be filtered by entity type and ID."""
    ledger.write_event(
        event_type=AuditEventType.ENCOUNTER_INGESTED,
        actor_type=ActorType.SYSTEM,
        actor_id="sys",
        entity_type=EntityType.ENCOUNTER,
        entity_id="enc-001",
    )
    ledger.write_event(
        event_type=AuditEventType.URGENCY_CLASSIFIED,
        actor_type=ActorType.SYSTEM,
        actor_id="sys",
        entity_type=EntityType.ENCOUNTER,
        entity_id="enc-001",
    )
    ledger.write_event(
        event_type=AuditEventType.ENCOUNTER_INGESTED,
        actor_type=ActorType.SYSTEM,
        actor_id="sys",
        entity_type=EntityType.ENCOUNTER,
        entity_id="enc-002",
    )

    events, total = ledger.query_events(entity_id="enc-001")
    assert total == 2


def test_verify_integrity_valid(ledger):
    """Chain verification returns VALID when all events have hashes."""
    ledger.write_event(
        event_type=AuditEventType.ENCOUNTER_INGESTED,
        actor_type=ActorType.SYSTEM,
        actor_id="sys",
        entity_type=EntityType.ENCOUNTER,
        entity_id="e1",
    )
    ledger.write_event(
        event_type=AuditEventType.SUBSIDY_SETTLED,
        actor_type=ActorType.SYSTEM,
        actor_id="sys",
        entity_type=EntityType.SUBSIDY,
        entity_id="s1",
    )

    result = ledger.verify_integrity()
    assert result["chain_status"] == "VALID"
    assert result["total_events"] == 2


def test_event_count(ledger):
    """Event count tracks total events."""
    assert ledger.get_event_count() == 0
    ledger.write_event(
        event_type=AuditEventType.ENCOUNTER_INGESTED,
        actor_type=ActorType.SYSTEM,
        actor_id="sys",
        entity_type=EntityType.ENCOUNTER,
        entity_id="e1",
    )
    assert ledger.get_event_count() == 1


def test_get_event_by_id(ledger):
    """Events can be retrieved by ID."""
    event = ledger.write_event(
        event_type=AuditEventType.ENCOUNTER_INGESTED,
        actor_type=ActorType.SYSTEM,
        actor_id="sys",
        entity_type=EntityType.ENCOUNTER,
        entity_id="e1",
    )
    retrieved = ledger.get_event(str(event.event_id))
    assert retrieved is not None
    assert retrieved.event_type == AuditEventType.ENCOUNTER_INGESTED
