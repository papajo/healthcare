"""Affordability Engine — F-02

Calculates the maximum out-of-pocket cost a patient is responsible for,
given their verified eligibility proof, urgency classification, and billing context.

Core formula:
    patient_responsibility = MIN(estimated_total, affordability_cap)
    subsidy_amount = estimated_total - patient_responsibility

Where affordability_cap is derived from:
    income_bracket.midpoint × tier_multiplier ÷ frequency_divisor × urgency_override
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

from src.config.settings import settings
from src.models.domain import (
    AffordabilityCalculationRequest,
    AffordabilityCalculationResponse,
    AffordabilityTier,
    ConfidenceLevel,
    EligibilityStatus,
    RevocationStatus,
    UrgencyLabel,
)

# ─── Reference Tables ────────────────────────────────────────────────────────

INCOME_BRACKETS: dict[str, dict[str, int]] = {
    "IB-01": {"min": 0, "max": 1_500_000, "midpoint": 750_000},
    "IB-02": {"min": 1_500_001, "max": 3_000_000, "midpoint": 2_250_000},
    "IB-03": {"min": 3_000_001, "max": 5_000_000, "midpoint": 4_000_000},
    "IB-04": {"min": 5_000_001, "max": 7_500_000, "midpoint": 6_250_000},
    "IB-05": {"min": 7_500_001, "max": 10_000_000, "midpoint": 8_750_000},
    "IB-06": {"min": 10_000_001, "max": 15_000_000, "midpoint": 12_500_000},
    "IB-07": {"min": 15_000_001, "max": 20_000_000, "midpoint": 17_500_000},
    "IB-08": {"min": 20_000_001, "max": 30_000_000, "midpoint": 25_000_000},
    "IB-09": {"min": 30_000_001, "max": 50_000_000, "midpoint": 40_000_000},
    "IB-10": {"min": 50_000_001, "max": 75_000_000, "midpoint": 62_500_000},
    "IB-11": {"min": 75_000_001, "max": 100_000_000, "midpoint": 87_500_000},
    "IB-12": {"min": 100_000_001, "max": 150_000_000, "midpoint": 150_000_000},
}

TIER_MULTIPLIERS: dict[str, float] = {
    AffordabilityTier.TIER_CRITICAL.value: 0.05,
    AffordabilityTier.TIER_LOW.value: 0.08,
    AffordabilityTier.TIER_STANDARD.value: 0.10,
    AffordabilityTier.TIER_MODERATE.value: 0.12,
    AffordabilityTier.TIER_UNVERIFIED.value: 1.00,
}

HOUSEHOLD_FACTORS: dict[str, float] = {
    "HS-1": 0.70,  # Single person
    "HS-2": 0.85,  # 2-person household
    "HS-3": 1.00,  # 3-person household (baseline)
    "HS-4": 1.15,  # 4-person household
    "HS-5": 1.30,  # 5+ person household
}

CONFIDENCE_MAPPING: dict[str, ConfidenceLevel] = {
    "VERY_HIGH": ConfidenceLevel.HIGH,
    "HIGH": ConfidenceLevel.HIGH,
    "MODERATE": ConfidenceLevel.MODERATE,
    "LOW": ConfidenceLevel.LOW,
}


# ─── Core Calculation ────────────────────────────────────────────────────────


def _is_proof_valid(proof, now: datetime) -> bool:
    """Check if an eligibility proof is currently valid."""
    if proof is None:
        return False
    if proof.revocation_status != RevocationStatus.ACTIVE:
        return False
    if proof.eligibility_status_normalized not in (
        EligibilityStatus.ELIGIBLE,
        EligibilityStatus.CONDITIONALLY_ELIGIBLE,
    ):
        return False
    if now < proof.proof_valid_from or now > proof.proof_valid_to:
        return False
    return True


def _determine_confidence(proof) -> ConfidenceLevel:
    """Map verification assurance level to confidence level."""
    return CONFIDENCE_MAPPING.get(proof.verification_assurance_level.value, ConfidenceLevel.LOW)


def _build_rule_description(tier: AffordabilityTier, urgency_override: bool) -> str:
    """Build human-readable description of the applied cap rule."""
    parts = [f"Cap based on {tier.value}"]
    if urgency_override:
        parts.append("with CRITICAL urgency override (25% additional protection)")
    return "; ".join(parts)


def calculate_affordability(
    request: AffordabilityCalculationRequest,
) -> AffordabilityCalculationResponse:
    """Calculate the patient's affordability cap and subsidy amount.
    
    This is a deterministic, stateless, idempotent function.
    Same inputs always produce the same output.
    """
    now = datetime.now(UTC)

    # Step 1: Check proof validity
    proof = request.eligibility_proof
    if not _is_proof_valid(proof, now):
        return _unverified_result(request, now)

    # Step 2: Get income bracket
    bracket = INCOME_BRACKETS.get(proof.income_bracket_code)
    if bracket is None:
        raise ValueError(f"Unknown income bracket: {proof.income_bracket_code}")

    annual_income_cents = bracket["midpoint"]

    # Step 3: Determine tier and multiplier
    try:
        tier = AffordabilityTier(proof.affordability_tier)
    except ValueError as err:
        raise ValueError(
            f"Unknown affordability tier: {proof.affordability_tier}"
        ) from err

    base_multiplier = TIER_MULTIPLIERS[tier.value]

    # Step 4: Calculate base cap
    base_cap_cents = math.floor(annual_income_cents * base_multiplier)

    # Step 5: Apply household size adjustment
    if request.household_size_band and request.household_size_band in HOUSEHOLD_FACTORS:
        hh_factor = HOUSEHOLD_FACTORS[request.household_size_band]
        base_cap_cents = math.floor(base_cap_cents * hh_factor)

    # Step 6: Apply per-encounter frequency limit
    per_encounter_cap = math.floor(base_cap_cents / settings.encounter_frequency_divisor)

    # Step 7: Apply urgency override
    urgency_override = False
    if request.urgency_label == UrgencyLabel.CRITICAL:
        per_encounter_cap = math.floor(per_encounter_cap * settings.critical_urgency_multiplier)
        urgency_override = True

    # Step 8: Calculate final patient responsibility
    patient_responsibility = min(request.estimated_total_cents, per_encounter_cap)

    # Step 9: Calculate subsidy
    subsidy = request.estimated_total_cents - patient_responsibility

    # Step 10: Determine confidence
    confidence = _determine_confidence(proof)

    return AffordabilityCalculationResponse(
        request_id=request.request_id,
        affordability_cap_cents=per_encounter_cap,
        patient_responsibility_cents=patient_responsibility,
        subsidy_amount_cents=subsidy,
        cap_rule_applied=_build_rule_description(tier, urgency_override),
        tier_applied=tier,
        urgency_override_applied=urgency_override,
        confidence_level=confidence,
        computed_at=now,
    )


def _unverified_result(
    request: AffordabilityCalculationRequest, now: datetime
) -> AffordabilityCalculationResponse:
    """Return result for unverified/invalid proof — no cap applied."""
    return AffordabilityCalculationResponse(
        request_id=request.request_id,
        affordability_cap_cents=request.estimated_total_cents,
        patient_responsibility_cents=request.estimated_total_cents,
        subsidy_amount_cents=0,
        cap_rule_applied="NO_PROOF_AVAILABLE",
        tier_applied=AffordabilityTier.TIER_UNVERIFIED,
        urgency_override_applied=False,
        confidence_level=ConfidenceLevel.LOW,
        computed_at=now,
    )
