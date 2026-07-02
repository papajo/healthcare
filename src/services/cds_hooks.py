"""CDS Hooks service — clinical decision support engine.

Provides a pluggable framework for registering CDS hooks and executing
clinical decision support rules. Built-in hooks cover patient-view,
order-select, order-sign, and medication-prescribe workflows.

New hooks can be registered via `register_hook()`.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from src.models.cds_hooks import (
    CDSCard,
    CDSContext,
    CDSDiscoveryResponse,
    CDSHookDefinition,
    CDSHookRequest,
    CDSHookResponse,
    CDSSource,
)
from src.services.cds_rules import (
    check_drug_allergy_interactions,
    check_drug_drug_interactions,
    check_duplicate_therapy,
    check_high_risk_medications,
    check_preventive_care,
)
from src.services.clinical_data import clinical_data_service

logger = logging.getLogger(__name__)

_SOURCE = CDSSource(label="Crisis-Cost Orchestrator CDS")


class CDSHooksService:
    """CDS Hooks service providing clinical decision support."""

    def __init__(self) -> None:
        self._hooks: dict[str, dict[str, Any]] = {}
        self._register_builtin_hooks()

    def _register_builtin_hooks(self) -> None:
        """Register built-in CDS hooks."""
        builtin_defs = [
            {
                "id": "patient-view",
                "title": "Patient View CDS",
                "description": (
                    "Clinical decision support when viewing a patient record. "
                    "Checks for drug-allergy interactions, high-risk medications, "
                    "and preventive care reminders."
                ),
                "hook": "patient-view",
                "version": "1.0.0",
            },
            {
                "id": "order-select",
                "title": "Order Select CDS",
                "description": (
                    "Clinical decision support when selecting an order. "
                    "Checks for duplicate therapy, drug interactions, and "
                    "cost-aware alternatives."
                ),
                "hook": "order-select",
                "version": "1.0.0",
            },
            {
                "id": "order-sign",
                "title": "Order Sign CDS",
                "description": (
                    "Clinical decision support before signing an order. "
                    "Checks for high-cost alerts, prior authorization "
                    "requirements, and generic substitution."
                ),
                "hook": "order-sign",
                "version": "1.0.0",
            },
            {
                "id": "medication-prescribe",
                "title": "Medication Prescribe CDS",
                "description": (
                    "Clinical decision support when prescribing medication. "
                    "Checks for drug-drug interactions, drug-allergy "
                    "interactions, duplicate therapy, and high-risk medications."
                ),
                "hook": "medication-prescribe",
                "version": "1.0.0",
            },
        ]

        handlers = {
            "patient-view": self._patient_view_handler,
            "order-select": self._order_select_handler,
            "order-sign": self._order_sign_handler,
            "medication-prescribe": self._medication_prescribe_handler,
        }

        for defn in builtin_defs:
            hook_id = defn["id"]
            self._hooks[hook_id] = {
                "definition": CDSHookDefinition(**defn),
                "handler": handlers[hook_id],
            }

    def register_hook(self, hook_id: str, handler: Callable[..., list[CDSCard]]) -> None:
        """Register a CDS hook handler.

        The handler receives a CDSContext and optional kwargs, and
        returns a list of CDSCard objects.
        """
        definition = CDSHookDefinition(
            id=hook_id,
            title=hook_id.replace("-", " ").title(),
            description=f"Custom CDS hook: {hook_id}",
            hook=hook_id,
            version="1.0.0",
        )
        self._hooks[hook_id] = {
            "definition": definition,
            "handler": handler,
        }
        logger.info("Registered CDS hook: %s", hook_id)

    def discover(self) -> CDSDiscoveryResponse:
        """Return discovery response with all registered hooks."""
        return CDSDiscoveryResponse(
            services=[h["definition"] for h in self._hooks.values()]
        )

    def get_hook_definition(self, hook_id: str) -> CDSHookDefinition | None:
        """Get the definition of a specific hook."""
        entry = self._hooks.get(hook_id)
        return entry["definition"] if entry else None

    def execute_hook(
        self,
        hook_id: str,
        request: CDSHookRequest,
    ) -> CDSHookResponse:
        """Execute a CDS hook and return cards.

        Raises KeyError if hook_id is not registered.
        """
        entry = self._hooks.get(hook_id)
        if entry is None:
            raise KeyError(f"CDS hook not found: {hook_id}")

        handler = entry["handler"]
        context = request.context

        try:
            # Extract order/medication from context for order hooks
            order = None
            if context.draftOrders:
                # draftOrders contains FHIR resources keyed by reference
                for _ref, resource in context.draftOrders.items():
                    if isinstance(resource, dict):
                        order = resource
                        break

            if hook_id in ("order-select", "order-sign"):
                cards = handler(context, order=order)
            elif hook_id == "medication-prescribe":
                cards = handler(context, medication=order)
            else:
                cards = handler(context)

            return CDSHookResponse(cards=cards)

        except Exception:
            logger.exception("Error executing CDS hook %s", hook_id)
            return CDSHookResponse(cards=[])

    # ─── Built-in Hook Handlers ──────────────────────────────────────────────

    def _patient_view_handler(self, context: CDSContext) -> list[CDSCard]:
        """Patient view hook — show alerts when viewing a patient.

        Checks:
        - Drug-allergy interactions
        - High-risk medications
        - Preventive care reminders
        """
        patient_id = context.patientId
        cards: list[CDSCard] = []

        # Fetch clinical data from FHIR store
        medications = clinical_data_service.get_patient_medications(patient_id)
        allergies = clinical_data_service.get_patient_allergies(patient_id)
        conditions = clinical_data_service.get_patient_conditions(patient_id)
        observations = clinical_data_service.get_patient_observations(patient_id)

        # Check drug-allergy interactions
        cards.extend(check_drug_allergy_interactions(medications, allergies))

        # Check high-risk medications
        cards.extend(check_high_risk_medications(medications))

        # Check preventive care
        cards.extend(check_preventive_care(conditions, observations))

        return cards

    def _order_select_handler(
        self,
        context: CDSContext,
        order: dict[str, Any] | None = None,
    ) -> list[CDSCard]:
        """Order select hook — suggestions when selecting an order.

        Checks:
        - Duplicate therapy detection
        - Drug-drug interactions
        """
        patient_id = context.patientId
        cards: list[CDSCard] = []

        if order is None:
            return cards

        medications = clinical_data_service.get_patient_medications(patient_id)

        # Check duplicate therapy
        resource_type = order.get("resourceType", "")
        if resource_type == "MedicationRequest":
            dup_card = check_duplicate_therapy(medications, order)
            if dup_card:
                cards.append(dup_card)

            # Check drug-drug interactions with the new medication
            all_meds = medications + [order]
            cards.extend(check_drug_drug_interactions(all_meds))

        return cards

    def _order_sign_handler(
        self,
        context: CDSContext,
        order: dict[str, Any] | None = None,
    ) -> list[CDSCard]:
        """Order sign hook — warnings before signing an order.

        Checks:
        - High-cost order alerts
        - High-risk medications
        """
        cards: list[CDSCard] = []

        if order is None:
            return cards

        resource_type = order.get("resourceType", "")

        if resource_type == "MedicationRequest":
            # Check high-risk medications
            cards.extend(check_high_risk_medications([order]))

        return cards

    def _medication_prescribe_handler(
        self,
        context: CDSContext,
        medication: dict[str, Any] | None = None,
    ) -> list[CDSCard]:
        """Medication prescribe hook — drug safety checks.

        Checks:
        - Drug-drug interactions
        - Drug-allergy interactions
        - Duplicate therapy
        - High-risk medications
        """
        patient_id = context.patientId
        cards: list[CDSCard] = []

        if medication is None:
            return cards

        medications = clinical_data_service.get_patient_medications(patient_id)
        allergies = clinical_data_service.get_patient_allergies(patient_id)

        # Check drug-allergy interactions (including new med)
        all_meds = medications + [medication]
        cards.extend(check_drug_allergy_interactions(all_meds, allergies))

        # Check drug-drug interactions
        cards.extend(check_drug_drug_interactions(all_meds))

        # Check duplicate therapy
        dup_card = check_duplicate_therapy(medications, medication)
        if dup_card:
            cards.append(dup_card)

        # Check high-risk medications
        cards.extend(check_high_risk_medications([medication]))

        return cards


# Singleton
cds_hooks_service = CDSHooksService()
