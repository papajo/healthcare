"""Tests for Affordability Engine — F-02.

16 test cases covering:
- Income bracket validation
- Affordability tier calculations
- Urgency overrides
- Household size adjustments
- Edge cases (proof expiry, revocation, missing proof)
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.models.domain import (
    AffordabilityCalculationRequest,
    EligibilityProof,
    EligibilityStatus,
    EncounterClass,
    RevocationStatus,
    UrgencyLabel,
    VerificationAssuranceLevel,
)
from src.services.affordability_engine import calculate_affordability


def _make_proof(
    bracket: str = "IB-06",
    tier: str = "TIER-STANDARD",
    status: EligibilityStatus = EligibilityStatus.ELIGIBLE,
    revocation: RevocationStatus = RevocationStatus.ACTIVE,
    assurance: VerificationAssuranceLevel = VerificationAssuranceLevel.HIGH,
    valid_days: int = 30,
) -> EligibilityProof:
    """Helper to create an eligibility proof."""
    now = datetime.now(UTC)
    return EligibilityProof(
        proof_id=uuid4(),
        income_bracket_code=bracket,
        affordability_tier=tier,
        eligibility_status_normalized=status,
        verification_assurance_level=assurance,
        proof_valid_from=now - timedelta(days=1),
        proof_valid_to=now + timedelta(days=valid_days),
        revocation_status=revocation,
        patient_pseudo_id=uuid4(),
    )


def _make_request(
    estimated_total: int = 5_000_000,
    urgency: UrgencyLabel = UrgencyLabel.URGENT,
    proof: EligibilityProof | None = None,
    household: str | None = None,
) -> AffordabilityCalculationRequest:
    """Helper to create a calculation request."""
    return AffordabilityCalculationRequest(
        encounter_id="ENC-TEST-001",
        patient_pseudo_id=uuid4(),
        urgency_label=urgency,
        estimated_total_cents=estimated_total,
        encounter_class=EncounterClass.EMERGENCY,
        eligibility_proof=proof,
        household_size_band=household,
    )


# ─── Test 1: Basic tier calculation ─────────────────────────────────────────


def test_tier_standard_basic():
    """TIER-STANDARD with no urgency override = 10% annual midpoint."""
    proof = _make_proof(bracket="IB-06", tier="TIER-STANDARD")
    request = _make_request(estimated_total=5_000_000, proof=proof)
    result = calculate_affordability(request)

    # IB-06 midpoint = 12,500,000 * 0.10 = 1,250,000 / 4 = 312,500
    assert result.affordability_cap_cents == 312_500
    assert result.patient_responsibility_cents == 312_500
    assert result.subsidy_amount_cents == 5_000_000 - 312_500
    assert result.tier_applied.value == "TIER-STANDARD"
    assert result.urgency_override_applied is False


# ─── Test 2: CRITICAL tier ──────────────────────────────────────────────────


def test_tier_critical():
    """TIER-CRITICAL = 5% annual midpoint."""
    proof = _make_proof(bracket="IB-06", tier="TIER-CRITICAL")
    request = _make_request(estimated_total=10_000_000, proof=proof)
    result = calculate_affordability(request)

    # 12,500,000 * 0.05 = 625,000 / 4 = 156,250
    assert result.affordability_cap_cents == 156_250


# ─── Test 3: TIER-LOW ───────────────────────────────────────────────────────


def test_tier_low():
    """TIER-LOW = 8% annual midpoint."""
    proof = _make_proof(bracket="IB-03", tier="TIER-LOW")
    request = _make_request(estimated_total=8_000_000, proof=proof)
    result = calculate_affordability(request)

    # IB-03 midpoint = 4,000,000 * 0.08 = 320,000 / 4 = 80,000
    assert result.affordability_cap_cents == 80_000


# ─── Test 4: TIER-MODERATE ──────────────────────────────────────────────────


def test_tier_moderate():
    """TIER-MODERATE = 12% annual midpoint."""
    proof = _make_proof(bracket="IB-09", tier="TIER-MODERATE")
    request = _make_request(estimated_total=15_000_000, proof=proof)
    result = calculate_affordability(request)

    # IB-09 midpoint = 40,000,000 * 0.12 = 4,800,000 / 4 = 1,200,000
    assert result.affordability_cap_cents == 1_200_000


# ─── Test 5: Urgency override (CRITICAL) ────────────────────────────────────


def test_urgency_critical_override():
    """CRITICAL urgency applies 0.75 multiplier (25% additional protection)."""
    proof = _make_proof(bracket="IB-06", tier="TIER-STANDARD")
    request = _make_request(
        estimated_total=10_000_000,
        urgency=UrgencyLabel.CRITICAL,
        proof=proof,
    )
    result = calculate_affordability(request)

    # 12,500,000 * 0.10 = 1,250,000 / 4 = 312,500 * 0.75 = 234,375
    assert result.affordability_cap_cents == 234_375
    assert result.urgency_override_applied is True


# ─── Test 6: Non-CRITICAL urgency (no override) ────────────────────────────


def test_urgency_urgent_no_override():
    """URGENT label does not apply override."""
    proof = _make_proof(bracket="IB-06", tier="TIER-STANDARD")
    request = _make_request(
        estimated_total=10_000_000,
        urgency=UrgencyLabel.URGENT,
        proof=proof,
    )
    result = calculate_affordability(request)

    assert result.urgency_override_applied is False
    # 12,500,000 * 0.10 / 4 = 312,500
    assert result.affordability_cap_cents == 312_500


# ─── Test 7: Household size adjustment ──────────────────────────────────────


def test_household_size_adjustment():
    """Household size of 4 applies 1.15 factor."""
    proof = _make_proof(bracket="IB-06", tier="TIER-STANDARD")
    request = _make_request(
        estimated_total=10_000_000,
        urgency=UrgencyLabel.ROUTINE,
        proof=proof,
        household="HS-4",
    )
    result = calculate_affordability(request)

    # 12,500,000 * 0.10 = 1,250,000 * 1.15 = 1,437,500 / 4 = 359,375
    assert result.affordability_cap_cents == 359_375


# ─── Test 8: Single household ───────────────────────────────────────────────


def test_household_single():
    """Household size 1 applies 0.70 factor."""
    proof = _make_proof(bracket="IB-06", tier="TIER-STANDARD")
    request = _make_request(
        estimated_total=10_000_000,
        urgency=UrgencyLabel.ROUTINE,
        proof=proof,
        household="HS-1",
    )
    result = calculate_affordability(request)

    # 12,500,000 * 0.10 = 1,250,000 * 0.70 = 875,000 / 4 = 218,750
    assert result.affordability_cap_cents == 218_750


# ─── Test 9: No proof → TIER-UNVERIFIED ────────────────────────────────────


def test_no_proof_returns_unverified():
    """No eligibility proof → TIER-UNVERIFIED, patient pays full amount."""
    request = _make_request(estimated_total=5_000_000, proof=None)
    result = calculate_affordability(request)

    assert result.patient_responsibility_cents == 5_000_000
    assert result.subsidy_amount_cents == 0
    assert result.tier_applied.value == "TIER-UNVERIFIED"
    assert result.cap_rule_applied == "NO_PROOF_AVAILABLE"


# ─── Test 10: Expired proof ─────────────────────────────────────────────────


def test_expired_proof():
    """Expired proof is treated as no proof."""
    proof = _make_proof(valid_days=-1)  # Expired yesterday
    request = _make_request(estimated_total=5_000_000, proof=proof)
    result = calculate_affordability(request)

    assert result.tier_applied.value == "TIER-UNVERIFIED"
    assert result.patient_responsibility_cents == 5_000_000


# ─── Test 11: Revoked proof ─────────────────────────────────────────────────


def test_revoked_proof():
    """Revoked proof is treated as no proof."""
    proof = _make_proof(revocation=RevocationStatus.REVOKED)
    request = _make_request(estimated_total=5_000_000, proof=proof)
    result = calculate_affordability(request)

    assert result.tier_applied.value == "TIER-UNVERIFIED"
    assert result.subsidy_amount_cents == 0


# ─── Test 12: Patient pays less than cap ────────────────────────────────────


def test_patient_pays_less_than_cap():
    """When estimated total is less than cap, patient pays total."""
    proof = _make_proof(bracket="IB-06", tier="TIER-STANDARD")
    request = _make_request(
        estimated_total=100_000,  # $1,000 — way below cap
        proof=proof,
    )
    result = calculate_affordability(request)

    # Cap = 312,500 but estimated total is only 100,000
    assert result.patient_responsibility_cents == 100_000
    assert result.subsidy_amount_cents == 0


# ─── Test 13: All income brackets are supported ────────────────────────────


def test_all_income_brackets():
    """All 12 income brackets are valid inputs."""
    for bracket_id in [
        "IB-01", "IB-02", "IB-03", "IB-04", "IB-05", "IB-06",
        "IB-07", "IB-08", "IB-09", "IB-10", "IB-11", "IB-12",
    ]:
        proof = _make_proof(bracket=bracket_id, tier="TIER-STANDARD")
        request = _make_request(estimated_total=1_000_000, proof=proof)
        result = calculate_affordability(request)
        assert result.affordability_cap_cents >= 0


# ─── Test 14: Low income bracket gets smaller cap ──────────────────────────


def test_low_income_smaller_cap():
    """IB-01 (lowest income) gets a smaller cap than IB-12."""
    proof_low = _make_proof(bracket="IB-01", tier="TIER-STANDARD")
    request_low = _make_request(proof=proof_low)
    result_low = calculate_affordability(request_low)

    proof_high = _make_proof(bracket="IB-12", tier="TIER-STANDARD")
    request_high = _make_request(proof=proof_high)
    result_high = calculate_affordability(request_high)

    assert result_low.affordability_cap_cents < result_high.affordability_cap_cents


# ─── Test 15: Idempotency — same inputs, same outputs ──────────────────────


def test_idempotency():
    """Deterministic: same inputs always produce same outputs."""
    proof = _make_proof(bracket="IB-06", tier="TIER-STANDARD")
    request = _make_request(estimated_total=5_000_000, proof=proof)

    result1 = calculate_affordability(request)
    result2 = calculate_affordability(request)

    assert result1.affordability_cap_cents == result2.affordability_cap_cents
    assert result1.patient_responsibility_cents == result2.patient_responsibility_cents
    assert result1.subsidy_amount_cents == result2.subsidy_amount_cents
    assert result1.tier_applied == result2.tier_applied


# ─── Test 16: Confidence level from verification assurance ──────────────────


def test_confidence_levels():
    """Confidence maps from verification assurance level."""
    for assurance, expected_confidence in [
        (VerificationAssuranceLevel.VERY_HIGH, "HIGH"),
        (VerificationAssuranceLevel.HIGH, "HIGH"),
        (VerificationAssuranceLevel.MODERATE, "MODERATE"),
        (VerificationAssuranceLevel.LOW, "LOW"),
    ]:
        proof = _make_proof(assurance=assurance)
        request = _make_request(proof=proof)
        result = calculate_affordability(request)
        assert result.confidence_level.value == expected_confidence
