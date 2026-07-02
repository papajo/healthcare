"""Built-in clinical decision support rules.

Contains drug-allergy interactions, drug-drug interactions, high-risk
medication alerts, preventive care reminders, and duplicate therapy
detection logic.

All rule functions return lists of CDSCard objects that can be
directly included in a CDSHooksResponse.
"""

from __future__ import annotations

from typing import Any

from src.models.cds_hooks import (
    CDSAction,
    CDSCard,
    CDSIndicator,
    CDSLink,
    CDSSource,
    CDSSuggestion,
)

# ─── Drug-Allergy Interaction Rules ──────────────────────────────────────────

# Mapping: drug_class -> {allergy_term -> warning_message}
DRUG_ALLERGY_RULES: dict[str, dict[str, str]] = {
    "penicillins": {
        "penicillin": (
            "Patient has penicillin allergy — avoid amoxicillin, "
            "ampicillin, piperacillin"
        ),
        "amoxicillin": (
            "Patient has amoxicillin allergy — cross-reactive "
            "with other penicillins"
        ),
        "ampicillin": (
            "Patient has ampicillin allergy — cross-reactive "
            "with other penicillins"
        ),
    },
    "sulfonamides": {
        "sulfonamides": (
            "Patient has sulfa allergy — avoid sulfamethoxazole, "
            "sulfasalazine"
        ),
        "sulfamethoxazole": (
            "Patient has sulfamethoxazole allergy — avoid all "
            "sulfonamide antibiotics"
        ),
    },
    "nsaids": {
        "aspirin": (
            "Patient has aspirin allergy — avoid all NSAIDs "
            "(ibuprofen, naproxen)"
        ),
        "ibuprofen": (
            "Patient has ibuprofen allergy — avoid all NSAIDs "
            "(aspirin, naproxen)"
        ),
        "naproxen": (
            "Patient has naproxen allergy — avoid all NSAIDs "
            "(aspirin, ibuprofen)"
        ),
    },
    "opioids": {
        "codeine": (
            "Patient has codeine allergy/intolerance — avoid all "
            "opioids or use with caution"
        ),
        "morphine": (
            "Patient has morphine allergy — avoid all opioids "
            "or use with caution"
        ),
    },
    "ace_inhibitors": {
        "ace inhibitor": (
            "Patient has ACE inhibitor allergy — avoid lisinopril, "
            "enalapril, ramipril"
        ),
        "lisinopril": (
            "Patient has lisinopril allergy — avoid all ACE inhibitors"
        ),
    },
    "statins": {
        "statin": (
            "Patient has statin allergy — avoid atorvastatin, "
            "simvastatin, rosuvastatin"
        ),
    },
    "cephalosporins": {
        "cephalosporin": (
            "Patient has cephalosporin allergy — use with caution, "
            "possible cross-reactivity with penicillins"
        ),
    },
}

# Generic drug name to class mapping for matching
_DRUG_TO_CLASS: dict[str, str] = {
    "amoxicillin": "penicillins",
    "ampicillin": "penicillins",
    "piperacillin": "penicillins",
    "penicillin": "penicillins",
    "sulfamethoxazole": "sulfonamides",
    "sulfasalazine": "sulfonamides",
    "ibuprofen": "nsaids",
    "naproxen": "nsaids",
    "aspirin": "nsaids",
    "codeine": "opioids",
    "morphine": "opioids",
    "oxycodone": "opioids",
    "hydrocodone": "opioids",
    "fentanyl": "opioids",
    "lisinopril": "ace_inhibitors",
    "enalapril": "ace_inhibitors",
    "ramipril": "ace_inhibitors",
    "atorvastatin": "statins",
    "simvastatin": "statins",
    "rosuvastatin": "statins",
    "cephalexin": "cephalosporins",
    "ceftriaxone": "cephalosporins",
}


# ─── Drug-Drug Interaction Rules ─────────────────────────────────────────────

# Mapping: (drug_a, drug_b) -> warning message
DRUG_INTERACTION_RULES: dict[tuple[str, str], str] = {
    ("warfarin", "aspirin"): (
        "Major: Increased bleeding risk with warfarin + aspirin"
    ),
    ("warfarin", "ibuprofen"): (
        "Major: NSAIDs increase warfarin bleeding risk"
    ),
    ("warfarin", "naproxen"): (
        "Major: NSAIDs increase warfarin bleeding risk"
    ),
    ("metformin", "contrast"): (
        "Moderate: Hold metformin 48h before/after IV contrast"
    ),
    ("lisinopril", "potassium"): (
        "Major: ACE inhibitors + potassium supplements — "
        "hyperkalemia risk"
    ),
    ("enalapril", "potassium"): (
        "Major: ACE inhibitors + potassium supplements — "
        "hyperkalemia risk"
    ),
    ("ssri", "tramadol"): (
        "Moderate: SSRIs + tramadol — increased seizure risk"
    ),
    ("methotrexate", "nsaids"): (
        "Major: NSAIDs reduce methotrexate clearance — "
        "toxicity risk"
    ),
    ("digoxin", "amiodarone"): (
        "Major: Amiodarone increases digoxin levels — "
        "toxicity risk"
    ),
}

# Generic names for interaction matching
_INTERACTION_GENERIC_NAMES: dict[str, list[str]] = {
    "warfarin": ["warfarin", "coumadin"],
    "aspirin": ["aspirin", "acetylsalicylic acid"],
    "ibuprofen": ["ibuprofen", "advil", "motrin"],
    "naproxen": ["naproxen", "aleve"],
    "metformin": ["metformin", "glucophage"],
    "lisinopril": ["lisinopril", "prinivil", "zestril"],
    "enalapril": ["enalapril", "vasotec"],
    "potassium": ["potassium", "k-dur", "klor-con"],
}


# ─── High-Risk Medication Alerts ─────────────────────────────────────────────

HIGH_RISK_MEDICATIONS: dict[str, str] = {
    "warfarin": "High-risk anticoagulant — verify INR before prescribing",
    "heparin": "High-risk anticoagulant — verify aPTT before prescribing",
    "insulin": "High-risk medication — verify dose and patient education",
    "methotrexate": "High-risk immunosuppressant — verify renal function",
    "digoxin": "High-risk cardiac glycoside — verify drug levels",
    "lithium": "High-risk mood stabilizer — narrow therapeutic index",
    "phenytoin": "High-risk anticonvulsant — monitor drug levels",
    "opioid": (
        "High-risk controlled substance — check PDMP, verify indication"
    ),
    "morphine": (
        "High-risk controlled substance — check PDMP, verify indication"
    ),
    "oxycodone": (
        "High-risk controlled substance — check PDMP, verify indication"
    ),
    "hydrocodone": (
        "High-risk controlled substance — check PDMP, verify indication"
    ),
    "fentanyl": (
        "High-risk controlled substance — check PDMP, verify indication"
    ),
}


# ─── Preventive Care Reminders ───────────────────────────────────────────────

PREVENTIVE_CARE: dict[str, dict[str, Any]] = {
    "diabetes": {
        "screening": "HbA1c every 3-6 months",
        "overdue_threshold_days": 90,
        "observation_code": "4548-4",
    },
    "hypertension": {
        "screening": "BP check every visit",
        "overdue_threshold_days": 30,
        "observation_code": "85354-9",
    },
    "hyperlipidemia": {
        "screening": "Lipid panel annually",
        "overdue_threshold_days": 365,
        "observation_code": "2093-3",
    },
}


# ─── Rule Functions ──────────────────────────────────────────────────────────

_SOURCE = CDSSource(label="Crisis-Cost Orchestrator CDS")


def _normalize_medication_name(med: dict[str, Any]) -> str:
    """Extract normalized medication name from a FHIR MedicationRequest."""
    concept = med.get("medicationCodeableConcept", {})
    if isinstance(concept, dict):
        return (concept.get("display") or concept.get("code") or "").lower().strip()
    return ""


def _normalize_allergy_name(allergy: dict[str, Any]) -> str:
    """Extract normalized allergy name from a FHIR AllergyIntolerance."""
    code = allergy.get("code", {})
    if isinstance(code, dict):
        return (code.get("display") or code.get("code") or "").lower().strip()
    return ""


def _normalize_condition_name(condition: dict[str, Any]) -> str:
    """Extract normalized condition name from a FHIR Condition."""
    code = condition.get("code", {})
    if isinstance(code, dict):
        return (code.get("display") or code.get("code") or "").lower().strip()
    return ""


def check_drug_allergy_interactions(
    medications: list[dict[str, Any]],
    allergies: list[dict[str, Any]],
) -> list[CDSCard]:
    """Check for drug-allergy interactions and return CDS cards.

    Compares active medications against known allergies and returns
    warning cards for any detected interactions.
    """
    cards: list[CDSCard] = []
    allergy_names = [_normalize_allergy_name(a) for a in allergies]
    allergy_names = [a for a in allergy_names if a]

    if not allergy_names:
        return cards

    for med in medications:
        med_name = _normalize_medication_name(med)
        if not med_name:
            continue

        drug_class = _DRUG_TO_CLASS.get(med_name)
        if drug_class is None:
            continue

        class_rules = DRUG_ALLERGY_RULES.get(drug_class, {})
        for allergy_name, message in class_rules.items():
            if allergy_name in allergy_names:
                cards.append(
                    CDSCard(
                        summary=f"Drug-Allergy Interaction: {med_name}",
                        indicator=CDSIndicator.WARNING,
                        detail=message,
                        source=_SOURCE,
                        suggestions=[
                            CDSSuggestion(
                                label="Review medication for allergy safety",
                                isRecommended=True,
                                actions=[
                                    CDSAction(
                                        label="Review alternative medications",
                                        description=message,
                                        type="create",
                                    )
                                ],
                            )
                        ],
                        links=[
                            CDSLink(
                                label="Drug-Allergy Interaction Reference",
                                url="https://www.fda.gov/drugs/drug-safety"
                                "and-availability/fda-drug-safety-communication",
                            )
                        ],
                    )
                )
                break  # One card per medication

    return cards


def check_drug_drug_interactions(
    medications: list[dict[str, Any]],
) -> list[CDSCard]:
    """Check for drug-drug interactions and return CDS cards.

    Compares all active medications against each other for known
    interactions and returns warning cards.
    """
    cards: list[CDSCard] = []
    med_names = [_normalize_medication_name(m) for m in medications]
    med_names = [m for m in med_names if m]

    if len(med_names) < 2:
        return cards

    checked_pairs: set[tuple[str, str]] = set()

    for i, name_a in enumerate(med_names):
        for name_b in med_names[i + 1 :]:
            pair = tuple(sorted([name_a, name_b]))
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)

            interaction_msg = _find_interaction(name_a, name_b)
            if interaction_msg:
                cards.append(
                    CDSCard(
                        summary=f"Drug-Drug Interaction: {name_a} + {name_b}",
                        indicator=CDSIndicator.WARNING,
                        detail=interaction_msg,
                        source=_SOURCE,
                        suggestions=[
                            CDSSuggestion(
                                label="Review drug interaction",
                                isRecommended=True,
                                actions=[
                                    CDSAction(
                                        label="Review interaction management",
                                        description=interaction_msg,
                                    )
                                ],
                            )
                        ],
                        links=[
                            CDSLink(
                                label="Drug Interaction Reference",
                                url="https://www.drugs.com/drug_interactions.html",
                            )
                        ],
                    )
                )

    return cards


def _find_interaction(name_a: str, name_b: str) -> str | None:
    """Find an interaction between two drug names."""
    # Direct pair match
    pair_a = (name_a, name_b)
    pair_b = (name_b, name_a)
    if pair_a in DRUG_INTERACTION_RULES:
        return DRUG_INTERACTION_RULES[pair_a]
    if pair_b in DRUG_INTERACTION_RULES:
        return DRUG_INTERACTION_RULES[pair_b]

    # Check generic name mappings
    for generic, names in _INTERACTION_GENERIC_NAMES.items():
        if name_a in names:
            for generic_b, names_b in _INTERACTION_GENERIC_NAMES.items():
                if name_b in names_b:
                    pair_g = (generic, generic_b)
                    pair_gb = (generic_b, generic)
                    if pair_g in DRUG_INTERACTION_RULES:
                        return DRUG_INTERACTION_RULES[pair_g]
                    if pair_gb in DRUG_INTERACTION_RULES:
                        return DRUG_INTERACTION_RULES[pair_gb]

    return None


def check_high_risk_medications(
    medications: list[dict[str, Any]],
) -> list[CDSCard]:
    """Check for high-risk medications and return CDS cards.

    Flags medications that require additional monitoring, dose
    verification, or special handling.
    """
    cards: list[CDSCard] = []

    for med in medications:
        med_name = _normalize_medication_name(med)
        if not med_name:
            continue

        for risk_med, message in HIGH_RISK_MEDICATIONS.items():
            if risk_med in med_name or med_name in risk_med:
                cards.append(
                    CDSCard(
                        summary=f"High-Risk Medication: {med_name}",
                        indicator=CDSIndicator.WARNING,
                        detail=message,
                        source=_SOURCE,
                        suggestions=[
                            CDSSuggestion(
                                label="Verify monitoring requirements",
                                isRecommended=True,
                                actions=[
                                    CDSAction(
                                        label="Check monitoring protocol",
                                        description=message,
                                    )
                                ],
                            )
                        ],
                    )
                )
                break  # One card per medication

    return cards


def check_preventive_care(
    conditions: list[dict[str, Any]],
    recent_observations: list[dict[str, Any]],
) -> list[CDSCard]:
    """Check for overdue preventive care and return CDS cards.

    For each active condition with a preventive care rule, checks
    whether the relevant observation was recorded within the
    overdue threshold.
    """
    cards: list[CDSCard] = []

    for condition in conditions:
        cond_name = _normalize_condition_name(condition)
        if not cond_name:
            continue

        for condition_key, rule in PREVENTIVE_CARE.items():
            if condition_key in cond_name or cond_name in condition_key:
                target_code = rule.get("observation_code", "")
                has_recent = False

                for obs in recent_observations:
                    code_obj = obs.get("code", {})
                    if isinstance(code_obj, dict) and code_obj.get("code") == target_code:
                        has_recent = True
                        break

                if not has_recent:
                    cards.append(
                        CDSCard(
                            summary=f"Preventive Care Due: {rule['screening']}",
                            indicator=CDSIndicator.INFO,
                            detail=(
                                f"Patient with {condition_key} is overdue for "
                                f"{rule['screening']}"
                            ),
                            source=_SOURCE,
                            suggestions=[
                                CDSSuggestion(
                                    label=f"Order {rule['screening']}",
                                    isRecommended=True,
                                    actions=[
                                        CDSAction(
                                            label=f"Order {rule['screening']}",
                                            description=rule["screening"],
                                            type="create",
                                        )
                                    ],
                                )
                            ],
                        )
                    )
                break

    return cards


def check_duplicate_therapy(
    medications: list[dict[str, Any]],
    new_medication: dict[str, Any],
) -> CDSCard | None:
    """Check if new medication duplicates an existing therapy.

    Returns a CDSCard if a duplicate is detected, None otherwise.
    """
    new_name = _normalize_medication_name(new_medication)
    if not new_name:
        return None

    new_class = _DRUG_TO_CLASS.get(new_name)

    for existing in medications:
        existing_name = _normalize_medication_name(existing)
        if not existing_name:
            continue

        # Exact duplicate
        if existing_name == new_name:
            return CDSCard(
                summary=f"Duplicate Therapy: {new_name}",
                indicator=CDSIndicator.WARNING,
                detail=(
                    f"Patient is already taking {new_name}. "
                    f"Verify if duplicate is intentional."
                ),
                source=_SOURCE,
                suggestions=[
                    CDSSuggestion(
                        label="Review duplicate therapy",
                        isRecommended=True,
                        actions=[
                            CDSAction(
                                label="Remove duplicate order",
                                description=f"Patient already taking {new_name}",
                            )
                        ],
                    )
                ],
            )

        # Same therapeutic class
        existing_class = _DRUG_TO_CLASS.get(existing_name)
        if new_class and existing_class and new_class == existing_class:
            return CDSCard(
                summary=(
                    f"Therapeutic Duplication: {new_name} "
                    f"(same class as {existing_name})"
                ),
                indicator=CDSIndicator.WARNING,
                detail=(
                    f"Patient is already taking {existing_name} "
                    f"({new_class}). Consider if both are needed."
                ),
                source=_SOURCE,
                suggestions=[
                    CDSSuggestion(
                        label="Review therapeutic duplication",
                        isRecommended=True,
                        actions=[
                            CDSAction(
                                label="Review therapeutic alternatives",
                                description=(
                                    f"Patient already on {existing_name}"
                                ),
                            )
                        ],
                    )
                ],
            )

    return None
