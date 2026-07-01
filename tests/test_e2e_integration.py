"""End-to-end integration test: F-04 → F-01 → F-02 → F-03 → F-06.

Simulates the complete patient encounter flow:
1. F-04: Provider submits encounter data
2. F-01: Urgency classifier determines urgency (simulated)
3. F-02: Affordability engine calculates patient cap
4. F-03: Subsidy orchestrator creates and settles subsidy
5. F-06: Audit ledger records every event
"""

import asyncio
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from src.models.domain import (
    ActorType,
    AffordabilityCalculationRequest,
    AuditEventType,
    EligibilityProof,
    EligibilityStatus,
    EncounterClass,
    EntityType,
    RevocationStatus,
    SubsidyStatus,
    UrgencyLabel,
    VerificationAssuranceLevel,
)
from src.services.affordability_engine import calculate_affordability
from src.services.audit_ledger import AuditLedger
from src.services.audit_projection import AuditProjection
from src.services.subsidy_orchestrator import SubsidyStore
from src.services.temporal_workflows import SubsidyWorkflowExecutor


@pytest.fixture
def audit_ledger():
    return AuditLedger()


@pytest.fixture
def subsidy_store():
    return SubsidyStore()


@pytest.fixture
def projection():
    return AuditProjection()


@pytest.fixture
def workflow_executor():
    return SubsidyWorkflowExecutor(max_retries=2, timeout_seconds=3600)


def _create_eligibility_proof(
    patient_id: str,
    bracket: str = "IB-06",
    tier: str = "TIER-STANDARD",
) -> EligibilityProof:
    """Create a valid eligibility proof for testing."""
    now = datetime.now(UTC)
    return EligibilityProof(
        proof_id=uuid4(),
        income_bracket_code=bracket,
        affordability_tier=tier,
        eligibility_status_normalized=EligibilityStatus.ELIGIBLE,
        verification_assurance_level=VerificationAssuranceLevel.HIGH,
        proof_valid_from=now - timedelta(days=1),
        proof_valid_to=now + timedelta(days=30),
        revocation_status=RevocationStatus.ACTIVE,
        patient_pseudo_id=uuid4(),
    )


# ─── Test: Full Encounter Flow ──────────────────────────────────────────────


def test_full_encounter_flow(
    audit_ledger, subsidy_store, projection, workflow_executor
):
    """Simulate a complete patient encounter from submission to settlement."""
    encounter_id = f"ENC-E2E-{uuid4().hex[:8]}"
    patient_id = str(uuid4())
    provider_id = str(uuid4())
    correlation_id = uuid4()

    print(f"\n{'='*60}")
    print(f"FULL ENCOUNTER FLOW: {encounter_id}")
    print(f"{'='*60}")

    # ── Step 1: F-04 — Provider submits encounter ──────────────────────────
    print("\n[Step 1] F-04: Provider submits encounter")
    encounter_data = {
        "encounter_id": encounter_id,
        "patient_pseudo_id": patient_id,
        "provider_org_id": provider_id,
        "encounter_class": "EMERGENCY",
        "chief_complaint": "Chest pain, shortness of breath",
        "estimated_total_cents": 15_000_000,  # $150,000
        "submitted_at": datetime.now(UTC).isoformat(),
    }

    audit_ledger.write_event(
        event_type=AuditEventType.ENCOUNTER_INGESTED,
        actor_type=ActorType.PROVIDER_EHR,
        actor_id=f"ehr:{provider_id}",
        entity_type=EntityType.ENCOUNTER,
        entity_id=encounter_id,
        payload=encounter_data,
        correlation_id=correlation_id,
    )
    print(f"  ✓ Encounter ingested: {encounter_id}")

    # ── Step 2: F-01 — Urgency classification (real classifier) ───────────
    print("\n[Step 2] F-01: Urgency classification")
    from src.models.f04_request import (
        AcuityLevel,
        AgeBracket,
        ArrivalMode,
        ClinicalContext,
        ClinicalFlag,
        EHRVendor,
        EncounterClass,
        EncounterInfo,
        EncounterStatus,
        F04EncounterRequest,
        FacilityType,
        PatientInfo,
        PresentingProblem,
        ProviderInfo,
        SexAtBirth,
        Vitals,
    )
    from src.services.urgency_classifier import UrgencyClassifier

    f04_request = F04EncounterRequest(
        request_id=uuid4(),
        provider=ProviderInfo(
            provider_organization_id=uuid4(),
            facility_id="FAC-001",
            facility_type=FacilityType.ACUTE_CARE_HOSPITAL,
            ehr_vendor=EHRVendor.EPIC,
        ),
        encounter=EncounterInfo(
            encounter_id=encounter_id,
            encounter_class=EncounterClass.EMERGENCY,
            encounter_status=EncounterStatus.IN_TRIAGE,
            arrival_mode=ArrivalMode.EMS_GROUND,
            occurred_at=datetime.now(UTC),
            service_date=date.today(),
            acuity_level=AcuityLevel.ESI_2,
        ),
        patient=PatientInfo(
            patient_pseudo_id=uuid4(),
            age_bracket=AgeBracket.AGE_50_64,
            sex_at_birth=SexAtBirth.M,
        ),
        clinical_context=ClinicalContext(
            presenting_problem=PresentingProblem(
                chief_complaint_code="29857009",  # Chest pain
                chief_complaint_text="Chest pain with shortness of breath",
                symptom_onset_hours=2.0,
            ),
            vitals=Vitals(
                heart_rate_bpm=110,
                respiratory_rate_bpm=24,
                spo2_percent=93.0,
                temperature_c=37.2,
                systolic_bp_mmhg=95,
                diastolic_bp_mmhg=60,
            ),
            clinical_flags=[ClinicalFlag.CHEST_PAIN, ClinicalFlag.SHORTNESS_OF_BREATH],
        ),
    )

    classifier = UrgencyClassifier()
    urgency_result = classifier.classify(f04_request)
    urgency_label = urgency_result.urgency_label

    audit_ledger.write_event(
        event_type=AuditEventType.URGENCY_CLASSIFIED,
        actor_type=ActorType.SYSTEM,
        actor_id=f"urgency-classifier-{urgency_result.classification_path}",
        entity_type=EntityType.ENCOUNTER,
        entity_id=encounter_id,
        payload={
            "urgency_label": urgency_result.urgency_label.value,
            "confidence": urgency_result.confidence,
            "triggered_evidence": urgency_result.triggered_evidence,
            "rationale_summary": urgency_result.rationale_summary,
            "classification_path": urgency_result.classification_path,
        },
        correlation_id=correlation_id,
    )
    print(f"  ✓ Urgency: {urgency_label.value} (confidence: {urgency_result.confidence:.2f})")
    print(f"  ✓ Path: {urgency_result.classification_path}")
    print(f"  ✓ Evidence: {urgency_result.triggered_evidence[:3]}")

    # ── Step 3: F-02 — Affordability calculation ──────────────────────────
    print("\n[Step 3] F-02: Affordability calculation")
    proof = _create_eligibility_proof(patient_id)
    affordability_request = AffordabilityCalculationRequest(
        encounter_id=encounter_id,
        patient_pseudo_id=uuid4(),
        urgency_label=urgency_label,
        estimated_total_cents=encounter_data["estimated_total_cents"],
        encounter_class=EncounterClass.EMERGENCY,
        eligibility_proof=proof,
    )

    affordability_result = calculate_affordability(affordability_request)

    est_total = encounter_data["estimated_total_cents"] / 100
    pat_resp = affordability_result.patient_responsibility_cents / 100
    subsidy_amt = affordability_result.subsidy_amount_cents / 100

    print(f"  ✓ Estimated total: ${est_total:,.2f}")
    print(f"  ✓ Patient responsibility: ${pat_resp:,.2f}")
    print(f"  ✓ Subsidy amount: ${subsidy_amt:,.2f}")
    print(f"  ✓ Tier applied: {affordability_result.tier_applied.value}")
    print(f"  ✓ Urgency override: {affordability_result.urgency_override_applied}")

    audit_ledger.write_event(
        event_type=AuditEventType.AFFORDABILITY_DECISION_COMPUTED,
        actor_type=ActorType.SYSTEM,
        actor_id="affordability-engine",
        entity_type=EntityType.AFFORDABILITY_DECISION,
        entity_id=str(affordability_request.request_id),
        payload={
            "encounter_id": encounter_id,
            "patient_pseudo_id": patient_id,
            "estimated_total_cents": encounter_data["estimated_total_cents"],
            "patient_responsibility_cents": affordability_result.patient_responsibility_cents,
            "subsidy_amount_cents": affordability_result.subsidy_amount_cents,
            "tier_applied": affordability_result.tier_applied.value,
            "urgency_override_applied": affordability_result.urgency_override_applied,
        },
        correlation_id=correlation_id,
    )

    # ── Step 4: F-03 — Subsidy creation and settlement ────────────────────
    print("\n[Step 4] F-03: Subsidy creation and workflow")
    from src.models.domain import SubsidyCreationRequest

    subsidy_request = SubsidyCreationRequest(
        encounter_id=encounter_id,
        patient_pseudo_id=uuid4(),
        provider_org_id=uuid4(),
        proof_id=proof.proof_id,
        urgency_label=urgency_label,
        estimated_total_cents=encounter_data["estimated_total_cents"],
        affordability_cap_cents=affordability_result.affordability_cap_cents,
        patient_responsibility_cents=affordability_result.patient_responsibility_cents,
        subsidy_amount_cents=affordability_result.subsidy_amount_cents,
        tier_applied=affordability_result.tier_applied.value,
    )

    subsidy = subsidy_store.create_subsidy(subsidy_request)

    audit_ledger.write_event(
        event_type=AuditEventType.SUBSIDY_CREATED,
        actor_type=ActorType.SYSTEM,
        actor_id="subsidy-orchestrator",
        entity_type=EntityType.SUBSIDY,
        entity_id=str(subsidy.subsidy_id),
        payload={
            "encounter_id": encounter_id,
            "subsidy_amount_cents": subsidy.subsidy_amount_cents,
            "payment_method": subsidy.payment_method.value if subsidy.payment_method else None,
        },
        correlation_id=correlation_id,
    )
    print(f"  ✓ Subsidy created: {subsidy.subsidy_id}")
    print(f"  ✓ Payment method: {subsidy.payment_method.value}")

    # Execute workflow (simulated Temporal)
    print("\n  Executing Temporal workflow...")
    workflow_result = asyncio.run(
        workflow_executor.execute({
            "subsidy_id": str(subsidy.subsidy_id),
            "encounter_id": encounter_id,
            "subsidy_amount_cents": subsidy.subsidy_amount_cents,
        })
    )
    print(f"  ✓ Workflow final state: {workflow_result['final_state']}")
    print(f"  ✓ Workflow steps: {len(workflow_result['history'])}")

    # Settle the subsidy
    subsidy_store.settle_subsidy(str(subsidy.subsidy_id))

    audit_ledger.write_event(
        event_type=AuditEventType.SUBSIDY_SETTLED,
        actor_type=ActorType.SYSTEM,
        actor_id="payment-processor",
        entity_type=EntityType.SUBSIDY,
        entity_id=str(subsidy.subsidy_id),
        payload={
            "payment_reference": f"pay-{uuid4().hex[:12]}",
            "settled_at": datetime.now(UTC).isoformat(),
        },
        correlation_id=correlation_id,
    )
    print("  ✓ Subsidy settled")

    # ── Step 5: F-06 — Audit verification ──────────────────────────────────
    print("\n[Step 5] F-06: Audit verification")
    integrity = audit_ledger.verify_integrity()
    print(f"  ✓ Chain status: {integrity['chain_status']}")
    print(f"  ✓ Total events: {integrity['total_events']}")

    # Query events by correlation
    events, total = audit_ledger.query_events(
        event_type=None,
        entity_type=None,
        entity_id=None,
    )
    correlation_events = [
        e for e in events if e.correlation_id == correlation_id
    ]
    print(f"  ✓ Events for this encounter: {len(correlation_events)}")

    # Project to read model
    for event in correlation_events:
        projection.project_event(event.model_dump())

    timeline = projection.get_entity_timeline("ENCOUNTER", encounter_id)
    print(f"  ✓ Entity timeline events: {timeline['event_count']}")

    # ── Summary ─────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("FLOW COMPLETE")
    print(f"{'='*60}")
    print(f"  Encounter:        {encounter_id}")
    print(f"  Urgency:          {urgency_label.value}")
    print(f"  Total cost:       ${est_total:,.2f}")
    print(f"  Patient pays:     ${pat_resp:,.2f}")
    print(f"  Platform subsidy: ${subsidy_amt:,.2f}")

    subsidy_status = subsidy_store.get_subsidy(
        str(subsidy.subsidy_id)
    ).subsidy_status.value
    print(f"  Subsidy status:   {subsidy_status}")
    print(f"  Audit events:     {integrity['total_events']}")
    print(f"  Audit integrity:  {integrity['chain_status']}")
    print()

    # ── Assertions ──────────────────────────────────────────────────────────
    assert integrity["chain_status"] == "VALID"
    assert len(correlation_events) >= 5  # At least 5 events for this encounter
    assert affordability_result.subsidy_amount_cents > 0
    assert affordability_result.tier_applied.value == "TIER-STANDARD"
    assert affordability_result.urgency_override_applied is True

    final_subsidy = subsidy_store.get_subsidy(str(subsidy.subsidy_id))
    assert final_subsidy.subsidy_status == SubsidyStatus.SETTLED


# ─── Test: Low-Income Patient Flow ─────────────────────────────────────────


def test_low_income_high_protection(
    audit_ledger, subsidy_store, projection, workflow_executor
):
    """Low-income patient with CRITICAL urgency gets maximum protection."""
    encounter_id = f"ENC-E2E-LOW-{uuid4().hex[:8]}"

    # Create proof for lowest income bracket
    now = datetime.now(UTC)
    proof = EligibilityProof(
        proof_id=uuid4(),
        income_bracket_code="IB-01",  # Lowest income
        affordability_tier="TIER-CRITICAL",
        eligibility_status_normalized=EligibilityStatus.ELIGIBLE,
        verification_assurance_level=VerificationAssuranceLevel.VERY_HIGH,
        proof_valid_from=now - timedelta(days=1),
        proof_valid_to=now + timedelta(days=30),
        revocation_status=RevocationStatus.ACTIVE,
        patient_pseudo_id=uuid4(),
    )

    request = AffordabilityCalculationRequest(
        encounter_id=encounter_id,
        patient_pseudo_id=uuid4(),
        urgency_label=UrgencyLabel.CRITICAL,
        estimated_total_cents=5_000_000,  # $50,000
        encounter_class=EncounterClass.EMERGENCY,
        eligibility_proof=proof,
    )

    result = calculate_affordability(request)

    # IB-01 midpoint = 750,000 * 0.05 = 37,500 / 4 = 9,375 * 0.75 = 7,031
    assert result.tier_applied.value == "TIER-CRITICAL"
    assert result.urgency_override_applied is True
    assert result.patient_responsibility_cents == 7_031
    assert result.subsidy_amount_cents == 4_992_969

    # 99.9% of the cost is subsidized
    subsidy_ratio = result.subsidy_amount_cents / 5_000_000
    assert subsidy_ratio > 0.99


# ─── Test: No Proof → Full Patient Responsibility ───────────────────────────


def test_no_proof_full_responsibility(
    audit_ledger, subsidy_store, projection, workflow_executor
):
    """Patient without eligibility proof pays full amount."""
    encounter_id = f"ENC-E2E-NO-PROOF-{uuid4().hex[:8]}"

    request = AffordabilityCalculationRequest(
        encounter_id=encounter_id,
        patient_pseudo_id=uuid4(),
        urgency_label=UrgencyLabel.URGENT,
        estimated_total_cents=10_000_000,  # $100,000
        encounter_class=EncounterClass.URGENT,
        eligibility_proof=None,
    )

    result = calculate_affordability(request)

    assert result.patient_responsibility_cents == 10_000_000
    assert result.subsidy_amount_cents == 0
    assert result.tier_applied.value == "TIER-UNVERIFIED"


# ─── Test: Expired Proof ────────────────────────────────────────────────────


def test_expired_proof_treated_as_unverified(
    audit_ledger, subsidy_store, projection, workflow_executor
):
    """Expired proof is treated as no proof."""
    now = datetime.now(UTC)
    proof = EligibilityProof(
        proof_id=uuid4(),
        income_bracket_code="IB-06",
        affordability_tier="TIER-STANDARD",
        eligibility_status_normalized=EligibilityStatus.ELIGIBLE,
        verification_assurance_level=VerificationAssuranceLevel.HIGH,
        proof_valid_from=now - timedelta(days=60),
        proof_valid_to=now - timedelta(days=30),  # Expired
        revocation_status=RevocationStatus.ACTIVE,
        patient_pseudo_id=uuid4(),
    )

    request = AffordabilityCalculationRequest(
        encounter_id=f"ENC-EXPIRED-{uuid4().hex[:8]}",
        patient_pseudo_id=uuid4(),
        urgency_label=UrgencyLabel.URGENT,
        estimated_total_cents=5_000_000,
        encounter_class=EncounterClass.EMERGENCY,
        eligibility_proof=proof,
    )

    result = calculate_affordability(request)
    assert result.tier_applied.value == "TIER-UNVERIFIED"
    assert result.patient_responsibility_cents == 5_000_000


# ─── Test: Workflow Retry on Failure ────────────────────────────────────────


@pytest.mark.asyncio
async def test_workflow_retries_on_failure():
    """Workflow retries with exponential backoff on activity failure."""
    from src.services.temporal_workflows import (
        ActivityResult,
        SubsidyWorkflowExecutor,
    )

    call_count = 0

    async def failing_then_succeeding_activity(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return ActivityResult(success=False, error="Simulated failure")
        return ActivityResult(success=True, data={"result": "success"})

    executor = SubsidyWorkflowExecutor(max_retries=3, timeout_seconds=60)

    # Patch the activity
    import src.services.temporal_workflows as tw
    original_func = tw.validate_subsidy_eligibility
    tw.validate_subsidy_eligibility = failing_then_succeeding_activity

    try:
        result = await executor.execute({
            "subsidy_id": str(uuid4()),
            "encounter_id": "ENC-RETRY-001",
            "subsidy_amount_cents": 100_000,
        })

        assert call_count == 3  # Failed twice, succeeded on third
        assert result["final_state"] in ("PAYMENT_SETTLED", "COMPENSATED")
    finally:
        tw.validate_subsidy_eligibility = original_func
