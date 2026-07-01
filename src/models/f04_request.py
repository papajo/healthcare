"""F-04 Provider API request models.

Pydantic models matching the provider-api-f04-request.schema.json specification.
Used by F-01 Urgency Classifier as input.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

# ─── Enums ────────────────────────────────────────────────────────────────────


class FacilityType(StrEnum):
    ACUTE_CARE_HOSPITAL = "ACUTE_CARE_HOSPITAL"
    CRITICAL_ACCESS_HOSPITAL = "CRITICAL_ACCESS_HOSPITAL"
    FREESTANDING_ED = "FREESTANDING_ED"
    URGENT_CARE = "URGENT_CARE"
    AMBULATORY_SURGERY_CENTER = "AMBULATORY_SURGERY_CENTER"
    INPATIENT_HOSPITAL = "INPATIENT_HOSPITAL"
    OUTPATIENT_HOSPITAL = "OUTPATIENT_HOSPITAL"


class EHRVendor(StrEnum):
    EPIC = "EPIC"
    CERNER = "CERNER"
    MEDITECH = "MEDITECH"
    ALLSCRIPTS = "ALLSCRIPTS"
    ATHENAHEALTH = "ATHENAHEALTH"
    NEXTGEN = "NEXTGEN"
    OTHER = "OTHER"


class EncounterClass(StrEnum):
    EMERGENCY = "EMERGENCY"
    URGENT = "URGENT"
    OBSERVATION = "OBSERVATION"
    OUTPATIENT = "OUTPATIENT"
    INPATIENT = "INPATIENT"


class EncounterStatus(StrEnum):
    ARRIVED = "ARRIVED"
    IN_TRIAGE = "IN_TRIAGE"
    IN_PROGRESS = "IN_PROGRESS"
    DISCHARGED = "DISCHARGED"
    ADMITTED = "ADMITTED"
    TRANSFERRED = "TRANSFERRED"


class ArrivalMode(StrEnum):
    WALK_IN = "WALK_IN"
    EMS_GROUND = "EMS_GROUND"
    EMS_AIR = "EMS_AIR"
    TRANSFER = "TRANSFER"
    POLICE = "POLICE"
    OTHER = "OTHER"


class AcuityLevel(StrEnum):
    ESI_1 = "ESI_1"
    ESI_2 = "ESI_2"
    ESI_3 = "ESI_3"
    ESI_4 = "ESI_4"
    ESI_5 = "ESI_5"
    CTAS_1 = "CTAS_1"
    CTAS_2 = "CTAS_2"
    CTAS_3 = "CTAS_3"
    CTAS_4 = "CTAS_4"
    CTAS_5 = "CTAS_5"
    UNKNOWN = "UNKNOWN"


class AgeBracket(StrEnum):
    AGE_0_17 = "0-17"
    AGE_18_34 = "18-34"
    AGE_35_49 = "35-49"
    AGE_50_64 = "50-64"
    AGE_65_74 = "65-74"
    AGE_75_84 = "75-84"
    AGE_85_PLUS = "85+"


class SexAtBirth(StrEnum):
    F = "F"
    M = "M"
    X = "X"
    U = "U"


class PregnancyStatus(StrEnum):
    PREGNANT = "PREGNANT"
    NOT_PREGNANT = "NOT_PREGNANT"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ClinicalFlag(StrEnum):
    CHEST_PAIN = "CHEST_PAIN"
    SHORTNESS_OF_BREATH = "SHORTNESS_OF_BREATH"
    STROKE_ALERT = "STROKE_ALERT"
    SEPSIS_ALERT = "SEPSIS_ALERT"
    TRAUMA_ALERT = "TRAUMA_ALERT"
    SUICIDAL_IDEATION = "SUICIDAL_IDEATION"
    PREGNANCY_RELATED = "PREGNANCY_RELATED"
    ALTERED_MENTAL_STATUS = "ALTERED_MENTAL_STATUS"
    SYNCOPE = "SYNCOPE"
    ACTIVE_BLEEDING = "ACTIVE_BLEEDING"
    FEVER = "FEVER"
    HYPOTENSION = "HYPOTENSION"
    HYPOXIA = "HYPOXIA"
    TACHYCARDIA = "TACHYCARDIA"
    BRADYCARDIA = "BRADYCARDIA"


class HighAlertMedication(StrEnum):
    ANTICOAGULANT = "ANTICOAGULANT"
    INSULIN = "INSULIN"
    OPIOID = "OPIOID"
    CHEMOTHERAPY = "CHEMOTHERAPY"
    SEDATIVE = "SEDATIVE"
    ANESTHETIC = "ANESTHETIC"
    DIURETIC = "DIURETIC"
    ANTIBIOTIC = "ANTIBIOTIC"


# ─── Nested Models ────────────────────────────────────────────────────────────


class ProviderInfo(BaseModel):
    provider_organization_id: UUID
    facility_id: str = Field(max_length=64)
    facility_type: FacilityType
    department_code: str | None = Field(default=None, max_length=32)
    ehr_vendor: EHRVendor
    npi: str | None = Field(default=None, pattern=r"^[0-9]{10}$")


class EncounterInfo(BaseModel):
    encounter_id: str = Field(max_length=64)
    encounter_class: EncounterClass
    encounter_status: EncounterStatus
    arrival_mode: ArrivalMode
    occurred_at: datetime
    service_date: date
    acuity_level: AcuityLevel | None = None
    disposition: str | None = None


class PatientInfo(BaseModel):
    patient_pseudo_id: UUID
    age_bracket: AgeBracket
    sex_at_birth: SexAtBirth
    pregnancy_status: PregnancyStatus | None = None
    insurance_status: str | None = None


class PresentingProblem(BaseModel):
    chief_complaint_code: str = Field(max_length=32)
    chief_complaint_text: str | None = Field(default=None, max_length=280)
    symptom_onset_hours: float | None = Field(default=None, ge=0, le=8760)


class Vitals(BaseModel):
    heart_rate_bpm: int = Field(ge=20, le=260)
    respiratory_rate_bpm: int = Field(ge=4, le=80)
    spo2_percent: float = Field(ge=0, le=100)
    temperature_c: float = Field(ge=25, le=45)
    systolic_bp_mmhg: int = Field(ge=40, le=300)
    diastolic_bp_mmhg: int = Field(ge=20, le=200)
    pain_score_0_10: int | None = Field(default=None, ge=0, le=10)
    gcs_total: int | None = Field(default=None, ge=3, le=15)
    blood_glucose_mg_dl: float | None = Field(default=None, ge=10, le=1000)


class CriticalLabResult(BaseModel):
    lab_code: str = Field(max_length=32)
    result_value: float
    unit: str = Field(max_length=16)
    critical_flag: bool = False
    abnormal_flag: str | None = None


class CriticalLabValues(BaseModel):
    lactate_mmol_l: float | None = None
    troponin_ng_ml: float | None = None


class ClinicalContext(BaseModel):
    presenting_problem: PresentingProblem
    vitals: Vitals
    critical_lab_values: CriticalLabValues | None = None
    critical_lab_results: list[CriticalLabResult] | None = None
    high_alert_medication_context: list[HighAlertMedication] | None = None
    clinical_flags: list[ClinicalFlag] | None = None


class TraceInfo(BaseModel):
    trace_id: str | None = Field(default=None, max_length=64)
    span_id: str | None = Field(default=None, max_length=32)
    source_system: str | None = Field(default=None, max_length=64)
    source_message_id: str | None = Field(default=None, max_length=128)


class BillingContext(BaseModel):
    """Billing context — de-emphasized for urgency classification."""
    pass


class F04EncounterRequest(BaseModel):
    """Full F-04 Provider API encounter intake request."""
    schema_version: str = "1.3.0"
    request_id: UUID
    trace: TraceInfo | None = None
    provider: ProviderInfo
    encounter: EncounterInfo
    patient: PatientInfo
    clinical_context: ClinicalContext
    billing_context: BillingContext = Field(default_factory=BillingContext)
