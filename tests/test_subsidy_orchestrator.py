"""Tests for Subsidy Orchestrator Service — F-03."""

from uuid import uuid4

import pytest

from src.models.domain import (
    PaymentMethod,
    SubsidyCreationRequest,
    SubsidyStatus,
)
from src.services.subsidy_orchestrator import SubsidyStore


@pytest.fixture
def store():
    """Create a fresh subsidy store for each test."""
    return SubsidyStore()


def _make_request(
    amount: int = 500_000,
    encounter_id: str = "ENC-TEST-001",
) -> SubsidyCreationRequest:
    """Helper to create a subsidy request."""
    return SubsidyCreationRequest(
        encounter_id=encounter_id,
        patient_pseudo_id=uuid4(),
        provider_org_id=uuid4(),
        subsidy_amount_cents=amount,
    )


def test_create_subsidy(store):
    """Subsidy can be created with PENDING status."""
    request = _make_request()
    subsidy = store.create_subsidy(request)

    assert subsidy.subsidy_status == SubsidyStatus.PENDING
    assert subsidy.subsidy_amount_cents == 500_000
    assert subsidy.payment_method == PaymentMethod.ACH


def test_ach_payment_for_small_amount(store):
    """ACH is used for amounts under $100,000."""
    request = _make_request(amount=500_000)
    subsidy = store.create_subsidy(request)
    assert subsidy.payment_method == PaymentMethod.ACH


def test_wire_payment(store):
    """Wire is used for amounts between $100,000 and $500,000."""
    request = _make_request(amount=15_000_000)  # $150,000
    subsidy = store.create_subsidy(request)
    assert subsidy.payment_method == PaymentMethod.WIRE


def test_stablecoin_payment(store):
    """Stablecoin is used for amounts over $500,000."""
    request = _make_request(amount=600_000_000)
    subsidy = store.create_subsidy(request)
    assert subsidy.payment_method == PaymentMethod.STABLECOIN


def test_get_subsidy(store):
    """Subsidy can be retrieved by ID."""
    request = _make_request()
    created = store.create_subsidy(request)

    retrieved = store.get_subsidy(str(created.subsidy_id))
    assert retrieved is not None
    assert retrieved.subsidy_id == created.subsidy_id


def test_settle_subsidy(store):
    """Subsidy can be settled."""
    request = _make_request()
    created = store.create_subsidy(request)

    settled = store.settle_subsidy(str(created.subsidy_id))
    assert settled is not None
    assert settled.subsidy_status == SubsidyStatus.SETTLED
    assert settled.settled_at is not None
    assert settled.payment_reference is not None


def test_cancel_pending_subsidy(store):
    """Pending subsidy can be cancelled."""
    request = _make_request()
    created = store.create_subsidy(request)

    cancelled = store.cancel_subsidy(str(created.subsidy_id), "no longer needed")
    assert cancelled.subsidy_status == SubsidyStatus.CANCELLED


def test_cancel_settled_subsidy_fails(store):
    """Settled subsidy cannot be cancelled."""
    request = _make_request()
    created = store.create_subsidy(request)
    store.settle_subsidy(str(created.subsidy_id))

    with pytest.raises(ValueError, match="Cannot cancel"):
        store.cancel_subsidy(str(created.subsidy_id), "too late")


def test_list_subsidies(store):
    """Subsidies can be listed."""
    store.create_subsidy(_make_request(encounter_id="ENC-001"))
    store.create_subsidy(_make_request(encounter_id="ENC-001"))
    store.create_subsidy(_make_request(encounter_id="ENC-002"))

    events, total = store.list_subsidies(encounter_id="ENC-001")
    assert total == 2


def test_daily_reconciliation(store):
    """Reconciliation summary is accurate."""
    store.create_subsidy(_make_request(amount=100_000))
    s2 = store.create_subsidy(_make_request(amount=200_000))
    store.settle_subsidy(str(s2.subsidy_id))

    summary = store.get_reconciliation("2026-07-01")
    assert summary["total_created"] == 2
    assert summary["total_settled"] == 1
    assert summary["total_amount_settled_cents"] == 200_000
