"""Seed realistic clinical data for demo patients."""

from __future__ import annotations

import logging

from src.services.fhir_store import fhir_store

logger = logging.getLogger(__name__)


def seed_clinical_data() -> None:
    """Populate the FHIR store with 5 realistic clinical patients."""

    patients = _build_patients()
    conditions = _build_conditions()
    medications = _build_medications()
    allergies = _build_allergies()
    observations = _build_observations()
    encounters = _build_encounters()

    for r in patients + conditions + medications + allergies + observations + encounters:
        fhir_store.create(r["resourceType"], r)

    logger.info(
        "Clinical seed: %d patients, %d conditions, %d medications, "
        "%d allergies, %d observations, %d encounters",
        len(patients),
        len(conditions),
        len(medications),
        len(allergies),
        len(observations),
        len(encounters),
    )


# ─── Patient 1 — John Smith (55M) ──────────────────────────────────────────


def _build_patients() -> list[dict]:
    return [
        {
            "id": "clinical-patient-001",
            "resourceType": "Patient",
            "active": True,
            "name": [{"family": "Smith", "given": ["John"], "use": "official"}],
            "gender": "male",
            "birthDate": "1971-03-15",
            "identifier": [
                {"system": "http://hospital.example.org/mrn", "value": "MRN-10001"}
            ],
            "telecom": [{"system": "phone", "value": "555-0101", "use": "home"}],
            "address": [
                {
                    "line": ["101 Main St"],
                    "city": "Springfield",
                    "state": "IL",
                    "postalCode": "62701",
                    "country": "US",
                }
            ],
        },
        {
            "id": "clinical-patient-002",
            "resourceType": "Patient",
            "active": True,
            "name": [{"family": "Garcia", "given": ["Maria"], "use": "official"}],
            "gender": "female",
            "birthDate": "1992-07-22",
            "identifier": [
                {"system": "http://hospital.example.org/mrn", "value": "MRN-10002"}
            ],
            "telecom": [{"system": "phone", "value": "555-0102", "use": "home"}],
            "address": [
                {
                    "line": ["202 Oak Ave"],
                    "city": "Springfield",
                    "state": "IL",
                    "postalCode": "62702",
                    "country": "US",
                }
            ],
        },
        {
            "id": "clinical-patient-003",
            "resourceType": "Patient",
            "active": True,
            "name": [{"family": "Johnson", "given": ["Robert"], "use": "official"}],
            "gender": "male",
            "birthDate": "1954-11-08",
            "identifier": [
                {"system": "http://hospital.example.org/mrn", "value": "MRN-10003"}
            ],
            "telecom": [{"system": "phone", "value": "555-0103", "use": "home"}],
            "address": [
                {
                    "line": ["303 Elm St"],
                    "city": "Springfield",
                    "state": "IL",
                    "postalCode": "62703",
                    "country": "US",
                }
            ],
        },
        {
            "id": "clinical-patient-004",
            "resourceType": "Patient",
            "active": True,
            "name": [{"family": "Williams", "given": ["Sarah"], "use": "official"}],
            "gender": "female",
            "birthDate": "1998-01-30",
            "identifier": [
                {"system": "http://hospital.example.org/mrn", "value": "MRN-10004"}
            ],
            "telecom": [{"system": "phone", "value": "555-0104", "use": "home"}],
            "address": [
                {
                    "line": ["404 Pine Rd"],
                    "city": "Springfield",
                    "state": "IL",
                    "postalCode": "62704",
                    "country": "US",
                }
            ],
        },
        {
            "id": "clinical-patient-005",
            "resourceType": "Patient",
            "active": True,
            "name": [{"family": "Lee", "given": ["David"], "use": "official"}],
            "gender": "male",
            "birthDate": "1981-05-12",
            "identifier": [
                {"system": "http://hospital.example.org/mrn", "value": "MRN-10005"}
            ],
            "telecom": [{"system": "phone", "value": "555-0105", "use": "home"}],
            "address": [
                {
                    "line": ["505 Maple Dr"],
                    "city": "Springfield",
                    "state": "IL",
                    "postalCode": "62705",
                    "country": "US",
                }
            ],
        },
    ]


# ─── Conditions ─────────────────────────────────────────────────────────────


def _build_conditions() -> list[dict]:
    pid = "clinical-patient-"
    return [
        # Patient 1 — John Smith
        {
            "id": "cond-001",
            "resourceType": "Condition",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "code": {
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": "I10",
                "display": "Essential hypertension",
            },
            "subject": {"reference": f"{pid}001"},
            "onsetDateTime": "2022-03-10T00:00:00Z",
        },
        {
            "id": "cond-002",
            "resourceType": "Condition",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "code": {
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": "E11.9",
                "display": "Type 2 diabetes mellitus without complications",
            },
            "subject": {"reference": f"{pid}001"},
            "onsetDateTime": "2023-08-15T00:00:00Z",
        },
        {
            "id": "cond-003",
            "resourceType": "Condition",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "code": {
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": "E78.5",
                "display": "Hyperlipidemia, unspecified",
            },
            "subject": {"reference": f"{pid}001"},
            "onsetDateTime": "2024-11-01T00:00:00Z",
        },
        # Patient 2 — Maria Garcia
        {
            "id": "cond-004",
            "resourceType": "Condition",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "code": {
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": "J45.20",
                "display": "Mild intermittent asthma, uncomplicated",
            },
            "subject": {"reference": f"{pid}002"},
            "onsetDateTime": "2010-04-20T00:00:00Z",
        },
        {
            "id": "cond-005",
            "resourceType": "Condition",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "code": {
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": "J30.2",
                "display": "Other seasonal allergic rhinitis",
            },
            "subject": {"reference": f"{pid}002"},
            "onsetDateTime": "2012-06-01T00:00:00Z",
        },
        # Patient 3 — Robert Johnson
        {
            "id": "cond-006",
            "resourceType": "Condition",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "code": {
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": "I48.91",
                "display": "Unspecified atrial fibrillation",
            },
            "subject": {"reference": f"{pid}003"},
            "onsetDateTime": "2020-02-14T00:00:00Z",
        },
        {
            "id": "cond-007",
            "resourceType": "Condition",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "code": {
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": "I50.9",
                "display": "Heart failure, unspecified",
            },
            "subject": {"reference": f"{pid}003"},
            "onsetDateTime": "2021-09-03T00:00:00Z",
        },
        {
            "id": "cond-008",
            "resourceType": "Condition",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "code": {
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": "N18.3",
                "display": "Chronic kidney disease, stage 3",
            },
            "subject": {"reference": f"{pid}003"},
            "onsetDateTime": "2022-06-18T00:00:00Z",
        },
        # Patient 4 — Sarah Williams
        {
            "id": "cond-009",
            "resourceType": "Condition",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "code": {
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": "G43.909",
                "display": "Migraine, unspecified, not intractable, without status migrainosus",
            },
            "subject": {"reference": f"{pid}004"},
            "onsetDateTime": "2019-12-01T00:00:00Z",
        },
        # Patient 5 — David Lee
        {
            "id": "cond-010",
            "resourceType": "Condition",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "code": {
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": "K21.0",
                "display": "Gastro-esophageal reflux disease with esophagitis",
            },
            "subject": {"reference": f"{pid}005"},
            "onsetDateTime": "2025-02-20T00:00:00Z",
        },
        {
            "id": "cond-011",
            "resourceType": "Condition",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "code": {
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": "E66.01",
                "display": "Morbid (severe) obesity due to excess calories",
            },
            "subject": {"reference": f"{pid}005"},
            "onsetDateTime": "2024-07-10T00:00:00Z",
        },
    ]


# ─── Medications ────────────────────────────────────────────────────────────


def _build_medications() -> list[dict]:
    pid = "clinical-patient-"
    return [
        # Patient 1 — John Smith
        {
            "id": "med-001",
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "314076",
                "display": "Lisinopril 10 MG Oral Tablet",
            },
            "subject": {"reference": f"{pid}001"},
            "authoredOn": "2025-01-10T00:00:00Z",
            "dosageInstruction": [
                {
                    "text": "Take 1 tablet by mouth once daily",
                    "timing": {"code": {"code": "QD", "display": "once daily"}},
                    "doseAndRate": [
                        {"doseQuantity": {"value": 10, "unit": "mg", "code": "mg"}}
                    ],
                }
            ],
        },
        {
            "id": "med-002",
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "860975",
                "display": "Metformin hydrochloride 500 MG Oral Tablet",
            },
            "subject": {"reference": f"{pid}001"},
            "authoredOn": "2025-06-01T00:00:00Z",
            "dosageInstruction": [
                {
                    "text": "Take 1 tablet by mouth twice daily with meals",
                    "timing": {"code": {"code": "BID", "display": "twice daily"}},
                    "doseAndRate": [
                        {"doseQuantity": {"value": 500, "unit": "mg", "code": "mg"}}
                    ],
                }
            ],
        },
        {
            "id": "med-003",
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "259255",
                "display": "Atorvastatin 20 MG Oral Tablet",
            },
            "subject": {"reference": f"{pid}001"},
            "authoredOn": "2024-11-15T00:00:00Z",
            "dosageInstruction": [
                {
                    "text": "Take 1 tablet by mouth once daily at bedtime",
                    "timing": {"code": {"code": "QD", "display": "once daily"}},
                    "doseAndRate": [
                        {"doseQuantity": {"value": 20, "unit": "mg", "code": "mg"}}
                    ],
                }
            ],
        },
        # Patient 2 — Maria Garcia
        {
            "id": "med-004",
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "309740",
                "display": "Albuterol 0.09 MG/ACTUAT Metered Dose Inhaler",
            },
            "subject": {"reference": f"{pid}002"},
            "authoredOn": "2026-01-05T00:00:00Z",
            "dosageInstruction": [
                {
                    "text": "Inhale 2 puffs every 4-6 hours as needed for wheezing",
                    "doseAndRate": [
                        {"doseQuantity": {"value": 2, "unit": "puffs", "code": "puffs"}}
                    ],
                }
            ],
        },
        {
            "id": "med-005",
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "310207",
                "display": "Cetirizine 10 MG Oral Tablet",
            },
            "subject": {"reference": f"{pid}002"},
            "authoredOn": "2026-03-15T00:00:00Z",
            "dosageInstruction": [
                {
                    "text": "Take 1 tablet by mouth once daily",
                    "timing": {"code": {"code": "QD", "display": "once daily"}},
                    "doseAndRate": [
                        {"doseQuantity": {"value": 10, "unit": "mg", "code": "mg"}}
                    ],
                }
            ],
        },
        # Patient 3 — Robert Johnson
        {
            "id": "med-006",
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "855332",
                "display": "Warfarin 5 MG Oral Tablet",
            },
            "subject": {"reference": f"{pid}003"},
            "authoredOn": "2024-09-01T00:00:00Z",
            "dosageInstruction": [
                {
                    "text": "Take 1 tablet by mouth once daily, take at same time each day",
                    "timing": {"code": {"code": "QD", "display": "once daily"}},
                    "doseAndRate": [
                        {"doseQuantity": {"value": 5, "unit": "mg", "code": "mg"}}
                    ],
                }
            ],
        },
        {
            "id": "med-007",
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "866405",
                "display": "Metoprolol Tartrate 50 MG Oral Tablet",
            },
            "subject": {"reference": f"{pid}003"},
            "authoredOn": "2024-09-01T00:00:00Z",
            "dosageInstruction": [
                {
                    "text": "Take 1 tablet by mouth twice daily",
                    "timing": {"code": {"code": "BID", "display": "twice daily"}},
                    "doseAndRate": [
                        {"doseQuantity": {"value": 50, "unit": "mg", "code": "mg"}}
                    ],
                }
            ],
        },
        {
            "id": "med-008",
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "310429",
                "display": "Furosemide 40 MG Oral Tablet",
            },
            "subject": {"reference": f"{pid}003"},
            "authoredOn": "2025-01-10T00:00:00Z",
            "dosageInstruction": [
                {
                    "text": "Take 1 tablet by mouth once daily in the morning",
                    "timing": {"code": {"code": "QD", "display": "once daily"}},
                    "doseAndRate": [
                        {"doseQuantity": {"value": 40, "unit": "mg", "code": "mg"}}
                    ],
                }
            ],
        },
        # Patient 4 — Sarah Williams
        {
            "id": "med-009",
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "312961",
                "display": "Sumatriptan Succinate 50 MG Oral Tablet",
            },
            "subject": {"reference": f"{pid}004"},
            "authoredOn": "2026-02-01T00:00:00Z",
            "dosageInstruction": [
                {
                    "text": "Take 1 tablet at onset of migraine, may repeat after 2 hours",
                    "doseAndRate": [
                        {"doseQuantity": {"value": 50, "unit": "mg", "code": "mg"}}
                    ],
                }
            ],
        },
        {
            "id": "med-010",
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "200033",
                "display": "Ibuprofen 400 MG Oral Tablet",
            },
            "subject": {"reference": f"{pid}004"},
            "authoredOn": "2026-02-01T00:00:00Z",
            "dosageInstruction": [
                {
                    "text": "Take 1 tablet by mouth every 6 hours as needed for pain",
                    "doseAndRate": [
                        {"doseQuantity": {"value": 400, "unit": "mg", "code": "mg"}}
                    ],
                }
            ],
        },
        # Patient 5 — David Lee
        {
            "id": "med-011",
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "204855",
                "display": "Omeprazole 20 MG Delayed Release Oral Capsule",
            },
            "subject": {"reference": f"{pid}005"},
            "authoredOn": "2026-03-01T00:00:00Z",
            "dosageInstruction": [
                {
                    "text": "Take 1 capsule by mouth once daily before breakfast",
                    "timing": {"code": {"code": "QD", "display": "once daily"}},
                    "doseAndRate": [
                        {"doseQuantity": {"value": 20, "unit": "mg", "code": "mg"}}
                    ],
                }
            ],
        },
    ]


# ─── Allergies ──────────────────────────────────────────────────────────────


def _build_allergies() -> list[dict]:
    pid = "clinical-patient-"
    return [
        # Patient 1 — John Smith
        {
            "id": "allergy-001",
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "type": "allergy",
            "category": ["medication"],
            "criticality": "high",
            "code": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "7980",
                "display": "Penicillin",
            },
            "patient": {"reference": f"{pid}001"},
            "recordedDate": "2010-05-20T00:00:00Z",
            "reaction": [
                {
                    "substance": {"code": "7980", "display": "Penicillin"},
                    "manifestation": {"code": "39579001", "display": "Rash"},
                    "severity": {"code": "moderate", "display": "Moderate"},
                }
            ],
        },
        {
            "id": "allergy-002",
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "type": "allergy",
            "category": ["medication"],
            "criticality": "high",
            "code": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "9016",
                "display": "Sulfonamide antibiotics",
            },
            "patient": {"reference": f"{pid}001"},
            "recordedDate": "2012-08-14T00:00:00Z",
            "reaction": [
                {
                    "substance": {"code": "9016", "display": "Sulfonamide antibiotics"},
                    "manifestation": {
                        "code": "39579001",
                        "display": "Anaphylaxis",
                    },
                    "severity": {"code": "severe", "display": "Severe"},
                }
            ],
        },
        # Patient 2 — Maria Garcia
        {
            "id": "allergy-003",
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "type": "allergy",
            "category": ["environment"],
            "criticality": "low",
            "code": {
                "system": "http://snomed.info/sct",
                "code": "300913004",
                "display": "Latex",
            },
            "patient": {"reference": f"{pid}002"},
            "recordedDate": "2015-03-10T00:00:00Z",
            "reaction": [
                {
                    "substance": {"code": "300913004", "display": "Latex"},
                    "manifestation": {
                        "code": "271807003",
                        "display": "Contact dermatitis",
                    },
                    "severity": {"code": "mild", "display": "Mild"},
                }
            ],
        },
        # Patient 3 — Robert Johnson
        {
            "id": "allergy-004",
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "type": "allergy",
            "category": ["medication"],
            "criticality": "high",
            "code": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "723",
                "display": "Aspirin",
            },
            "patient": {"reference": f"{pid}003"},
            "recordedDate": "2018-11-20T00:00:00Z",
            "reaction": [
                {
                    "substance": {"code": "723", "display": "Aspirin"},
                    "manifestation": {
                        "code": "13645005",
                        "display": "GI bleeding",
                    },
                    "severity": {"code": "severe", "display": "Severe"},
                }
            ],
        },
        {
            "id": "allergy-005",
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "type": "allergy",
            "category": ["medication"],
            "criticality": "moderate",
            "code": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "2670",
                "display": "Codeine",
            },
            "patient": {"reference": f"{pid}003"},
            "recordedDate": "2019-04-05T00:00:00Z",
            "reaction": [
                {
                    "substance": {"code": "2670", "display": "Codeine"},
                    "manifestation": {
                        "code": "422587007",
                        "display": "Nausea",
                    },
                    "severity": {"code": "moderate", "display": "Moderate"},
                }
            ],
        },
        # Patient 5 — David Lee
        {
            "id": "allergy-006",
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {"code": "active", "display": "Active"},
            "verificationStatus": {"code": "confirmed", "display": "Confirmed"},
            "type": "allergy",
            "category": ["medication"],
            "criticality": "moderate",
            "code": {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "2670",
                "display": "Codeine",
            },
            "patient": {"reference": f"{pid}005"},
            "recordedDate": "2023-09-12T00:00:00Z",
            "reaction": [
                {
                    "substance": {"code": "2670", "display": "Codeine"},
                    "manifestation": {
                        "code": "422587007",
                        "display": "Drowsiness",
                    },
                    "severity": {"code": "mild", "display": "Mild"},
                }
            ],
        },
    ]


# ─── Observations (Vitals + Labs) ──────────────────────────────────────────


def _build_observations() -> list[dict]:
    pid = "clinical-patient-"
    ts = "2026-06-15T10:30:00Z"
    ts2 = "2026-06-01T09:00:00Z"
    return [
        # ── Patient 1 — John Smith vitals ──
        {
            "id": "obs-bp-001",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel",
            },
            "subject": {"reference": f"{pid}001"},
            "effectiveDateTime": ts,
            "valueString": "138/85 mmHg",
        },
        {
            "id": "obs-hr-001",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "8867-4",
                "display": "Heart rate",
            },
            "subject": {"reference": f"{pid}001"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 72,
                "unit": "beats/min",
                "code": "/min",
            },
        },
        {
            "id": "obs-temp-001",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "8310-5",
                "display": "Body temperature",
            },
            "subject": {"reference": f"{pid}001"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 98.6,
                "unit": "degF",
                "code": "[degF]",
            },
        },
        {
            "id": "obs-spo2-001",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "2708-6",
                "display": "Oxygen saturation",
            },
            "subject": {"reference": f"{pid}001"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 97,
                "unit": "%",
                "code": "%",
            },
        },
        # ── Patient 1 — John Smith labs ──
        {
            "id": "obs-hba1c-001",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "4548-4",
                "display": "Hemoglobin A1c",
            },
            "subject": {"reference": f"{pid}001"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 7.2,
                "unit": "%",
                "code": "%",
            },
            "interpretation": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "H",
                    "display": "High",
                }
            ],
            "referenceRange": [
                {"high": {"value": 7.0, "unit": "%", "code": "%"}, "text": "< 7.0%"}
            ],
        },
        {
            "id": "obs-ldl-001",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "2089-1",
                "display": "LDL Cholesterol",
            },
            "subject": {"reference": f"{pid}001"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 142,
                "unit": "mg/dL",
                "code": "mg/dL",
            },
            "interpretation": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "H",
                    "display": "High",
                }
            ],
            "referenceRange": [
                {
                    "high": {"value": 100, "unit": "mg/dL", "code": "mg/dL"},
                    "text": "< 100 mg/dL",
                }
            ],
        },
        {
            "id": "obs-creat-001",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "2160-0",
                "display": "Creatinine",
            },
            "subject": {"reference": f"{pid}001"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 1.0,
                "unit": "mg/dL",
                "code": "mg/dL",
            },
            "referenceRange": [
                {
                    "low": {"value": 0.6, "unit": "mg/dL"},
                    "high": {"value": 1.2, "unit": "mg/dL"},
                    "text": "0.6-1.2 mg/dL",
                }
            ],
        },
        # ── Patient 2 — Maria Garcia vitals ──
        {
            "id": "obs-bp-002",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel",
            },
            "subject": {"reference": f"{pid}002"},
            "effectiveDateTime": ts,
            "valueString": "118/72 mmHg",
        },
        {
            "id": "obs-hr-002",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "8867-4",
                "display": "Heart rate",
            },
            "subject": {"reference": f"{pid}002"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 68,
                "unit": "beats/min",
                "code": "/min",
            },
        },
        {
            "id": "obs-temp-002",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "8310-5",
                "display": "Body temperature",
            },
            "subject": {"reference": f"{pid}002"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 98.4,
                "unit": "degF",
                "code": "[degF]",
            },
        },
        {
            "id": "obs-spo2-002",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "2708-6",
                "display": "Oxygen saturation",
            },
            "subject": {"reference": f"{pid}002"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 99,
                "unit": "%",
                "code": "%",
            },
        },
        # ── Patient 2 — Maria Garcia labs ──
        {
            "id": "obs-ige-001",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "30192-7",
                "display": "IgE [Units/volume] in Serum or Plasma",
            },
            "subject": {"reference": f"{pid}002"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 180,
                "unit": "IU/mL",
                "code": "[IU]/mL",
            },
            "interpretation": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "H",
                    "display": "High",
                }
            ],
            "referenceRange": [
                {
                    "high": {"value": 100, "unit": "IU/mL"},
                    "text": "< 100 IU/mL normal, 100-200 slightly high",
                }
            ],
        },
        # ── Patient 3 — Robert Johnson vitals ──
        {
            "id": "obs-bp-003",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel",
            },
            "subject": {"reference": f"{pid}003"},
            "effectiveDateTime": ts,
            "valueString": "125/78 mmHg",
        },
        {
            "id": "obs-hr-003",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "8867-4",
                "display": "Heart rate",
            },
            "subject": {"reference": f"{pid}003"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 88,
                "unit": "beats/min",
                "code": "/min",
            },
            "valueString": "88 (irregular)",
        },
        {
            "id": "obs-temp-003",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "8310-5",
                "display": "Body temperature",
            },
            "subject": {"reference": f"{pid}003"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 98.2,
                "unit": "degF",
                "code": "[degF]",
            },
        },
        {
            "id": "obs-spo2-003",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "2708-6",
                "display": "Oxygen saturation",
            },
            "subject": {"reference": f"{pid}003"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 94,
                "unit": "%",
                "code": "%",
            },
        },
        # ── Patient 3 — Robert Johnson labs ──
        {
            "id": "obs-inr-001",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "3451-7",
                "display": "INR",
            },
            "subject": {"reference": f"{pid}003"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 2.8,
                "unit": "",
                "code": "",
            },
            "interpretation": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "N",
                    "display": "Normal",
                }
            ],
            "referenceRange": [
                {
                    "low": {"value": 2.0},
                    "high": {"value": 3.0},
                    "text": "2.0-3.0 therapeutic range",
                }
            ],
        },
        {
            "id": "obs-bnp-001",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "30934-4",
                "display": "BNP",
            },
            "subject": {"reference": f"{pid}003"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 450,
                "unit": "pg/mL",
                "code": "pg/mL",
            },
            "interpretation": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "H",
                    "display": "High",
                }
            ],
            "referenceRange": [
                {"high": {"value": 100, "unit": "pg/mL"}, "text": "< 100 pg/mL normal"}
            ],
        },
        {
            "id": "obs-egfr-001",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "48642-3",
                "display": "eGFR",
            },
            "subject": {"reference": f"{pid}003"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 45,
                "unit": "mL/min/1.73m2",
                "code": "mL/min/{1.73_m2}",
            },
            "interpretation": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "L",
                    "display": "Low",
                }
            ],
            "referenceRange": [
                {"low": {"value": 60, "unit": "mL/min/1.73m2"}, "text": ">= 60 mL/min normal"}
            ],
        },
        # ── Patient 4 — Sarah Williams vitals ──
        {
            "id": "obs-bp-004",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel",
            },
            "subject": {"reference": f"{pid}004"},
            "effectiveDateTime": ts,
            "valueString": "110/68 mmHg",
        },
        {
            "id": "obs-hr-004",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "8867-4",
                "display": "Heart rate",
            },
            "subject": {"reference": f"{pid}004"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 65,
                "unit": "beats/min",
                "code": "/min",
            },
        },
        {
            "id": "obs-temp-004",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "8310-5",
                "display": "Body temperature",
            },
            "subject": {"reference": f"{pid}004"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 98.8,
                "unit": "degF",
                "code": "[degF]",
            },
        },
        {
            "id": "obs-spo2-004",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "2708-6",
                "display": "Oxygen saturation",
            },
            "subject": {"reference": f"{pid}004"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 100,
                "unit": "%",
                "code": "%",
            },
        },
        # ── Patient 4 — Sarah Williams labs ──
        {
            "id": "obs-cbc-004",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "58410-2",
                "display": "CBC panel",
            },
            "subject": {"reference": f"{pid}004"},
            "effectiveDateTime": ts2,
            "valueString": "Normal",
        },
        # ── Patient 5 — David Lee vitals ──
        {
            "id": "obs-bp-005",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel",
            },
            "subject": {"reference": f"{pid}005"},
            "effectiveDateTime": ts,
            "valueString": "130/82 mmHg",
        },
        {
            "id": "obs-hr-005",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "8867-4",
                "display": "Heart rate",
            },
            "subject": {"reference": f"{pid}005"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 76,
                "unit": "beats/min",
                "code": "/min",
            },
        },
        {
            "id": "obs-temp-005",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "8310-5",
                "display": "Body temperature",
            },
            "subject": {"reference": f"{pid}005"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 98.5,
                "unit": "degF",
                "code": "[degF]",
            },
        },
        {
            "id": "obs-spo2-005",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "2708-6",
                "display": "Oxygen saturation",
            },
            "subject": {"reference": f"{pid}005"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 98,
                "unit": "%",
                "code": "%",
            },
        },
        {
            "id": "obs-bmi-005",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "39156-5",
                "display": "Body mass index",
            },
            "subject": {"reference": f"{pid}005"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 34.2,
                "unit": "kg/m2",
                "code": "kg/m2",
            },
            "interpretation": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "H",
                    "display": "High",
                }
            ],
        },
        # ── Patient 5 — David Lee labs ──
        {
            "id": "obs-chol-005",
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory",
                }
            ],
            "code": {
                "system": "http://loinc.org",
                "code": "2093-3",
                "display": "Total cholesterol",
            },
            "subject": {"reference": f"{pid}005"},
            "effectiveDateTime": ts,
            "valueQuantity": {
                "value": 220,
                "unit": "mg/dL",
                "code": "mg/dL",
            },
            "interpretation": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "H",
                    "display": "Borderline high",
                }
            ],
            "referenceRange": [
                {"high": {"value": 200, "unit": "mg/dL"}, "text": "< 200 mg/dL desirable"}
            ],
        },
    ]


# ─── Encounters ─────────────────────────────────────────────────────────────


def _build_encounters() -> list[dict]:
    pid = "clinical-patient-"
    return [
        {
            "id": "enc-001",
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
            },
            "subject": {"reference": f"{pid}001"},
            "period": {
                "start": "2026-06-28T10:00:00Z",
                "end": "2026-06-28T10:30:00Z",
            },
            "identifier": [
                {
                    "system": "http://hospital.example.org/encounter",
                    "value": "ENC-10001",
                }
            ],
        },
        {
            "id": "enc-002",
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
            },
            "subject": {"reference": f"{pid}002"},
            "period": {
                "start": "2026-06-20T14:00:00Z",
                "end": "2026-06-20T14:20:00Z",
            },
            "identifier": [
                {
                    "system": "http://hospital.example.org/encounter",
                    "value": "ENC-10002",
                }
            ],
        },
        {
            "id": "enc-003",
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "IMP",
                "display": "inpatient encounter",
            },
            "subject": {"reference": f"{pid}003"},
            "period": {
                "start": "2026-06-10T08:00:00Z",
                "end": "2026-06-14T12:00:00Z",
            },
            "identifier": [
                {
                    "system": "http://hospital.example.org/encounter",
                    "value": "ENC-10003",
                }
            ],
        },
        {
            "id": "enc-004",
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
            },
            "subject": {"reference": f"{pid}004"},
            "period": {
                "start": "2026-05-20T09:00:00Z",
                "end": "2026-05-20T09:30:00Z",
            },
            "identifier": [
                {
                    "system": "http://hospital.example.org/encounter",
                    "value": "ENC-10004",
                }
            ],
        },
        {
            "id": "enc-005",
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory",
            },
            "subject": {"reference": f"{pid}005"},
            "period": {
                "start": "2026-06-25T11:00:00Z",
                "end": "2026-06-25T11:45:00Z",
            },
            "identifier": [
                {
                    "system": "http://hospital.example.org/encounter",
                    "value": "ENC-10005",
                }
            ],
        },
    ]
