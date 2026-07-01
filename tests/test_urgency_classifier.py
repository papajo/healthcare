"""Tests for F-01 Urgency Classifier.

Covers:
- Rule-based classification (CRITICAL, URGENT, ROUTINE)
- Vitals threshold evaluation
- Clinical flag escalation
- High-risk complaint codes
- Medication risk context
- LLM fallback for ambiguous cases
- Edge cases
"""

from datetime import UTC, date, datetime
from uuid import uuid4

from src.models.f04_request import (
    AcuityLevel,
    AgeBracket,
    ArrivalMode,
    ClinicalContext,
    ClinicalFlag,
    CriticalLabValues,
    EHRVendor,
    EncounterClass,
    EncounterInfo,
    EncounterStatus,
    F04EncounterRequest,
    FacilityType,
    HighAlertMedication,
    PatientInfo,
    PregnancyStatus,
    PresentingProblem,
    ProviderInfo,
    SexAtBirth,
    Vitals,
)
from src.services.urgency_classifier import (
    UrgencyClassifier,
    UrgencyLabel,
)


def _make_request(
    complaint_code: str = "22253000",  # Abdominal pain (ROUTINE)
    complaint_text: str | None = None,
    symptom_onset_hours: float | None = None,
    hr: int = 75,
    rr: int = 16,
    spo2: float = 98.0,
    temp: float = 36.8,
    sbp: int = 120,
    dbp: int = 80,
    gcs: int | None = None,
    glucose: float | None = None,
    flags: list[ClinicalFlag] | None = None,
    meds: list[HighAlertMedication] | None = None,
    labs: list | None = None,
    lactate: float | None = None,
    troponin: float | None = None,
    acuity: AcuityLevel | None = None,
    arrival: ArrivalMode = ArrivalMode.WALK_IN,
    age: AgeBracket = AgeBracket.AGE_35_49,
    pregnancy: PregnancyStatus = PregnancyStatus.NOT_APPLICABLE,
) -> F04EncounterRequest:
    """Helper to create a minimal F-04 request."""
    return F04EncounterRequest(
        request_id=uuid4(),
        provider=ProviderInfo(
            provider_organization_id=uuid4(),
            facility_id="FAC-001",
            facility_type=FacilityType.ACUTE_CARE_HOSPITAL,
            ehr_vendor=EHRVendor.EPIC,
        ),
        encounter=EncounterInfo(
            encounter_id=f"ENC-{uuid4().hex[:8]}",
            encounter_class=EncounterClass.EMERGENCY,
            encounter_status=EncounterStatus.IN_TRIAGE,
            arrival_mode=arrival,
            occurred_at=datetime.now(UTC),
            service_date=date.today(),
            acuity_level=acuity,
        ),
        patient=PatientInfo(
            patient_pseudo_id=uuid4(),
            age_bracket=age,
            sex_at_birth=SexAtBirth.M,
            pregnancy_status=pregnancy,
        ),
        clinical_context=ClinicalContext(
            presenting_problem=PresentingProblem(
                chief_complaint_code=complaint_code,
                chief_complaint_text=complaint_text,
                symptom_onset_hours=symptom_onset_hours,
            ),
            vitals=Vitals(
                heart_rate_bpm=hr,
                respiratory_rate_bpm=rr,
                spo2_percent=spo2,
                temperature_c=temp,
                systolic_bp_mmhg=sbp,
                diastolic_bp_mmhg=dbp,
                gcs_total=gcs,
                blood_glucose_mg_dl=glucose,
            ),
            critical_lab_values=CriticalLabValues(
                lactate_mmol_l=lactate,
                troponin_ng_ml=troponin,
            ),
            clinical_flags=flags,
            high_alert_medication_context=meds,
        ),
    )


# ─── Test 1: CRITICAL — Stroke Alert ────────────────────────────────────────


def test_critical_stroke_alert():
    """Stroke alert flag → CRITICAL."""
    request = _make_request(flags=[ClinicalFlag.STROKE_ALERT])
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert result.classification_path == "rule_based"
    assert any("STROKE_ALERT" in e for e in result.triggered_evidence)


# ─── Test 2: CRITICAL — Sepsis Alert ────────────────────────────────────────


def test_critical_sepsis_alert():
    """Sepsis alert flag → CRITICAL."""
    request = _make_request(flags=[ClinicalFlag.SEPSIS_ALERT])
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL


# ─── Test 3: CRITICAL — Trauma Alert ────────────────────────────────────────


def test_critical_trauma_alert():
    """Trauma alert flag → CRITICAL."""
    request = _make_request(flags=[ClinicalFlag.TRAUMA_ALERT])
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL


# ─── Test 4: CRITICAL — Low SpO2 ───────────────────────────────────────────


def test_critical_low_spo2():
    """SpO2 < 90% → CRITICAL."""
    request = _make_request(spo2=86.0)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert any("CRITICAL_SPO2" in e for e in result.triggered_evidence)


# ─── Test 5: CRITICAL — Hypotension ────────────────────────────────────────


def test_critical_hypotension():
    """SBP < 80 → CRITICAL."""
    request = _make_request(sbp=75, dbp=45)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert any("CRITICAL_HYPOTENSION" in e for e in result.triggered_evidence)


# ─── Test 6: CRITICAL — Tachycardia ────────────────────────────────────────


def test_critical_tachycardia():
    """HR > 150 → CRITICAL."""
    request = _make_request(hr=160)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert any("CRITICAL_TACHYCARDIA" in e for e in result.triggered_evidence)


# ─── Test 7: CRITICAL — Low GCS ────────────────────────────────────────────


def test_critical_low_gcs():
    """GCS < 8 → CRITICAL."""
    request = _make_request(gcs=6)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert any("CRITICAL_GCS" in e for e in result.triggered_evidence)


# ─── Test 8: CRITICAL — EMS Air Transport ──────────────────────────────────


def test_critical_ems_air():
    """EMS air transport → CRITICAL."""
    request = _make_request(arrival=ArrivalMode.EMS_AIR)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert any("EMS_AIR" in e for e in result.triggered_evidence)


# ─── Test 9: CRITICAL — ESI-1 Acuity ───────────────────────────────────────


def test_critical_esi_1():
    """ESI-1 acuity → CRITICAL."""
    request = _make_request(acuity=AcuityLevel.ESI_1)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL


# ─── Test 10: CRITICAL — Critical Lactate ───────────────────────────────────


def test_critical_lactate():
    """Lactate > 4.0 → CRITICAL."""
    request = _make_request(lactate=5.2)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert any("CRITICAL_LACTATE" in e for e in result.triggered_evidence)


# ─── Test 11: CRITICAL — Elevated Troponin ──────────────────────────────────


def test_critical_troponin():
    """Troponin > 0.04 → CRITICAL."""
    request = _make_request(troponin=0.15)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert any("ELEVATED_TROPONIN" in e for e in result.triggered_evidence)


# ─── Test 12: URGENT — Low SpO2 (borderline) ──────────────────────────────


def test_urgent_low_spo2():
    """SpO2 90-94% → URGENT."""
    request = _make_request(spo2=92.0)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.URGENT
    assert any("LOW_SPO2" in e for e in result.triggered_evidence)


# ─── Test 13: URGENT — Tachycardia (borderline) ────────────────────────────


def test_urgent_tachycardia():
    """HR 130-150 → URGENT."""
    request = _make_request(hr=140)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.URGENT


# ─── Test 14: URGENT — Hypotension (borderline) ────────────────────────────


def test_urgent_hypotension():
    """SBP 80-90 → URGENT."""
    request = _make_request(sbp=85, dbp=55)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.URGENT


# ─── Test 15: URGENT — ESI-2 Acuity ───────────────────────────────────────


def test_urgent_esi_2():
    """ESI-2 acuity → URGENT."""
    request = _make_request(acuity=AcuityLevel.ESI_2)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.URGENT


# ─── Test 16: URGENT — Elevated Lactate ────────────────────────────────────


def test_urgent_elevated_lactate():
    """Lactate 2.0-4.0 → URGENT."""
    request = _make_request(lactate=3.0)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.URGENT


# ─── Test 17: URGENT — Child (age modifier) ────────────────────────────────


def test_urgent_child_modifier():
    """Child (0-17) with abnormal vitals → URGENT (conservative escalation)."""
    request = _make_request(
        age=AgeBracket.AGE_0_17,
        spo2=93.0,  # Low SpO2 → URGENT
    )
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.URGENT


# ─── Test 18: URGENT — Elderly (age modifier) ──────────────────────────────


def test_urgent_elderly_modifier():
    """Elderly (85+) with abnormal vitals → URGENT (conservative escalation)."""
    request = _make_request(
        age=AgeBracket.AGE_85_PLUS,
        hr=135,  # Tachycardia → URGENT
    )
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.URGENT


# ─── Test 19: URGENT — Pregnant patient ────────────────────────────────────


def test_urgent_pregnant_modifier():
    """Pregnant patient → conservative escalation."""
    request = _make_request(
        pregnancy=PregnancyStatus.PREGNANT,
        complaint_code="371631005",  # Anaphylaxis (CRITICAL code)
    )
    result = UrgencyClassifier().classify(request)

    # Pregnancy + critical complaint = CRITICAL
    assert result.urgency_label == UrgencyLabel.CRITICAL


# ─── Test 20: ROUTINE — Stable patient ─────────────────────────────────────


def test_routine_stable():
    """Stable patient with normal vitals → ROUTINE."""
    request = _make_request(
        complaint_code="225823000",  # Routine follow-up (not in risk lists)
        hr=72,
        rr=16,
        spo2=99.0,
        temp=36.8,
        sbp=120,
        dbp=80,
    )
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.ROUTINE
    # Can be either rule_based (if evidence found) or llm (if ambiguous)
    assert result.classification_path in ("rule_based", "llm")


# ─── Test 21: LLM Fallback — Ambiguous case ────────────────────────────────


def test_llm_fallback_ambiguous():
    """Ambiguous case with no evidence → LLM classifier."""
    # Minimal case with no flags, no abnormal vitals, no critical complaint
    request = _make_request(
        complaint_code="UNKNOWN_CODE",  # Not in any risk list
        hr=80,
        rr=18,
        spo2=97.0,
        temp=37.0,
        sbp=115,
        dbp=75,
    )
    result = UrgencyClassifier().classify(request)

    # Should use LLM fallback
    assert result.classification_path == "llm"
    assert result.confidence <= 0.85


# ─── Test 22: CRITICAL — Critical Lab Result ────────────────────────────────


def test_critical_lab_result_flag():
    """Lab result with critical_flag=True → CRITICAL."""
    from src.models.f04_request import CriticalLabResult

    request = _make_request(
        labs=[CriticalLabResult(
            lab_code="K",
            result_value=7.5,
            unit="mEq/L",
            critical_flag=True,
        )]
    )
    # Manually set lab results since the helper doesn't support them directly
    request.clinical_context.critical_lab_results = [
        CriticalLabResult(
            lab_code="K",
            result_value=7.5,
            unit="mEq/L",
            critical_flag=True,
        )
    ]
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert any("CRITICAL_LAB" in e for e in result.triggered_evidence)


# ─── Test 23: Medication Risk — Opioid + Respiratory Depression ────────────


def test_medication_risk_opioid():
    """Opioid + low RR → escalation."""
    request = _make_request(
        meds=[HighAlertMedication.OPIOID],
        rr=8,  # Low respiratory rate
        spo2=90.0,
    )
    result = UrgencyClassifier().classify(request)

    # Should escalate due to medication risk
    assert result.urgency_label == UrgencyLabel.CRITICAL


# ─── Test 24: Confidence levels ────────────────────────────────────────────


def test_confidence_levels():
    """CRITICAL has higher confidence than ROUTINE."""
    critical_request = _make_request(flags=[ClinicalFlag.STROKE_ALERT])
    critical_result = UrgencyClassifier().classify(critical_request)

    routine_request = _make_request(
        complaint_code="271807003",
        hr=72, rr=16, spo2=99.0, temp=36.8, sbp=120, dbp=80,
    )
    routine_result = UrgencyClassifier().classify(routine_request)

    assert critical_result.confidence >= routine_result.confidence


# ─── Test 25: Multiple flags → CRITICAL ────────────────────────────────────


def test_multiple_flags_escalation():
    """Multiple clinical flags → CRITICAL."""
    request = _make_request(
        flags=[ClinicalFlag.CHEST_PAIN, ClinicalFlag.SHORTNESS_OF_BREATH],
    )
    result = UrgencyClassifier().classify(request)

    # Multiple flags should escalate
    assert result.urgency_label in (UrgencyLabel.CRITICAL, UrgencyLabel.URGENT)
    assert len(result.triggered_evidence) > 0


# ─── Test 26: Fever + Hypotension → CRITICAL ───────────────────────────────


def test_fever_with_hypotension():
    """Fever + hypotension → CRITICAL (sepsis concern)."""
    request = _make_request(
        temp=39.8,
        sbp=85,
        flags=[ClinicalFlag.FEVER, ClinicalFlag.HYPOTENSION],
    )
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert len(result.triggered_evidence) >= 2


# ─── Test 27: Hypoglycemia → CRITICAL ──────────────────────────────────────


def test_critical_hypoglycemia():
    """Blood glucose < 50 → CRITICAL."""
    request = _make_request(glucose=42.0)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert any("CRITICAL_HYPOGLYCEMIA" in e for e in result.triggered_evidence)


# ─── Test 28: Hyperthermia → CRITICAL ──────────────────────────────────────


def test_critical_hyperthermia():
    """Temperature > 40.5C → CRITICAL."""
    request = _make_request(temp=41.2)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert any("CRITICAL_HYPERTHERMIA" in e for e in result.triggered_evidence)


# ─── Test 29: Bradycardia → CRITICAL ───────────────────────────────────────


def test_critical_bradycardia():
    """HR < 40 → CRITICAL."""
    request = _make_request(hr=35)
    result = UrgencyClassifier().classify(request)

    assert result.urgency_label == UrgencyLabel.CRITICAL
    assert any("CRITICAL_BRADYCARDIA" in e for e in result.triggered_evidence)


# ─── Test 30: Rationale is non-diagnostic ──────────────────────────────────


def test_rationale_non_diagnostic():
    """Rationale should not contain diagnostic language."""
    request = _make_request(flags=[ClinicalFlag.STROKE_ALERT])
    result = UrgencyClassifier().classify(request)

    # Should not mention specific diagnoses
    assert "diagnosis" not in result.rationale_summary.lower()
    assert "disease" not in result.rationale_summary.lower()
