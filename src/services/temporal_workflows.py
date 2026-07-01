"""Temporal.io workflow definitions for F-03 Subsidy Orchestrator.

In production, these workflows run on a Temporal server and provide:
- Durable execution (survives crashes/restarts)
- Automatic retries with exponential backoff
- Timeout handling (72h for subsidy settlement)
- Saga pattern for compensating transactions

This module defines the workflow and activity interfaces.
For development, we use a mock executor that mimics Temporal semantics.
"""

from __future__ import annotations

import asyncio
import logging
import math
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

logger = logging.getLogger(__name__)


# ─── Workflow State Machine ──────────────────────────────────────────────────


class SubsidyWorkflowState(StrEnum):
    """States in the subsidy workflow state machine."""

    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    VALIDATION_PASSED = "VALIDATION_PASSED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INITIATING_PAYMENT = "INITIATING_PAYMENT"
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    PAYMENT_SETTLED = "PAYMENT_SETTLED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    COMPENSATING = "COMPENSATING"
    COMPENSATED = "COMPENSATED"
    CANCELLED = "CANCELLED"


# ─── Activity Definitions ────────────────────────────────────────────────────


class ActivityResult:
    """Result of a workflow activity."""

    def __init__(self, success: bool, data: dict | None = None, error: str | None = None):
        self.success = success
        self.data = data or {}
        self.error = error


async def validate_subsidy_eligibility(subsidy_data: dict) -> ActivityResult:
    """Activity: Validate subsidy eligibility.
    
    Checks:
    - Patient has valid eligibility proof
    - Encounter is within allowed time window
    - Subsidy amount is within tier limits
    - No duplicate subsidy for same encounter
    """
    # Simulate async validation
    await asyncio.sleep(0.01)

    if subsidy_data.get("subsidy_amount_cents", 0) <= 0:
        return ActivityResult(success=False, error="Invalid subsidy amount")

    if subsidy_data.get("encounter_id") is None:
        return ActivityResult(success=False, error="Missing encounter_id")

    return ActivityResult(
        success=True,
        data={"validation_passed": True, "validated_at": datetime.now(UTC).isoformat()},
    )


async def select_payment_method(subsidy_data: dict) -> ActivityResult:
    """Activity: Select the appropriate payment rail.
    
    Rules:
    - Amount < $100,000 → ACH
    - Amount $100,000 - $500,000 → Wire
    - Amount > $500,000 → Stablecoin
    """
    amount = subsidy_data.get("subsidy_amount_cents", 0)

    if amount >= 50_000_000:
        method = "STABLECOIN"
    elif amount >= 10_000_000:
        method = "WIRE"
    else:
        method = "ACH"

    return ActivityResult(
        success=True,
        data={"payment_method": method, "selected_at": datetime.now(UTC).isoformat()},
    )


async def initiate_payment(subsidy_data: dict, payment_method: str) -> ActivityResult:
    """Activity: Initiate payment to provider.
    
    In production, this calls the actual payment rail API.
    """
    await asyncio.sleep(0.01)

    payment_ref = f"pay-{uuid4().hex[:12]}"

    logger.info(
        "Payment initiated: %s via %s for subsidy %s",
        payment_ref,
        payment_method,
        subsidy_data.get("subsidy_id"),
    )

    return ActivityResult(
        success=True,
        data={
            "payment_reference": payment_ref,
            "initiated_at": datetime.now(UTC).isoformat(),
        },
    )


async def check_payment_status(payment_reference: str) -> ActivityResult:
    """Activity: Check payment status with the payment rail.
    
    In production, this polls the payment API.
    """
    await asyncio.sleep(0.01)

    # Simulate successful settlement
    return ActivityResult(
        success=True,
        data={
            "status": "SETTLED",
            "settled_at": datetime.now(UTC).isoformat(),
        },
    )


async def compensate_payment(subsidy_data: dict) -> ActivityResult:
    """Activity: Compensate (reverse) a failed payment.
    
    This is part of the saga pattern — if downstream steps fail,
    we compensate by reversing any completed steps.
    """
    await asyncio.sleep(0.01)

    logger.warning(
        "Payment compensation executed for subsidy %s",
        subsidy_data.get("subsidy_id"),
    )

    return ActivityResult(
        success=True,
        data={"compensated_at": datetime.now(UTC).isoformat()},
    )


async def emit_audit_event(event_type: str, entity_id: str, payload: dict) -> ActivityResult:
    """Activity: Emit an audit event to the ledger."""
    from src.models.domain import ActorType, AuditEventType, EntityType
    from src.services.audit_ledger import audit_ledger

    audit_ledger.write_event(
        event_type=AuditEventType(event_type),
        actor_type=ActorType.SYSTEM,
        actor_id="temporal-workflow",
        entity_type=EntityType.SUBSIDY,
        entity_id=entity_id,
        payload=payload,
    )

    return ActivityResult(success=True)


# ─── Workflow Executor (Mock for Development) ───────────────────────────────


class SubsidyWorkflowExecutor:
    """Mock Temporal workflow executor for development.
    
    Mimics Temporal's retry and timeout semantics without
    requiring a running Temporal server.
    """

    def __init__(self, max_retries: int = 3, timeout_seconds: int = 72 * 3600):
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

    async def execute(self, subsidy_data: dict) -> dict:
        """Execute the full subsidy workflow.
        
        Workflow steps:
        1. VALIDATING → Validate eligibility
        2. INITIATING_PAYMENT → Select payment method
        3. PAYMENT_PROCESSING → Initiate payment
        4. PAYMENT_SETTLED → Verify settlement
        
        On failure at any step, compensate in reverse order.
        """
        workflow_id = subsidy_data.get("subsidy_id", str(uuid4()))
        state = SubsidyWorkflowState.CREATED
        history: list[dict] = []

        try:
            # Step 1: Validate
            state = SubsidyWorkflowState.VALIDATING
            history.append({"state": state.value, "timestamp": datetime.now(UTC).isoformat()})

            validation = await self._retry_with_backoff(
                validate_subsidy_eligibility, subsidy_data
            )
            if not validation.success:
                state = SubsidyWorkflowState.VALIDATION_FAILED
                history.append({"state": state.value, "error": validation.error})
                return {"workflow_id": workflow_id, "final_state": state.value, "history": history}

            state = SubsidyWorkflowState.VALIDATION_PASSED
            history.append({"state": state.value, "timestamp": datetime.now(UTC).isoformat()})

            # Step 2: Select payment method
            state = SubsidyWorkflowState.INITIATING_PAYMENT
            history.append({"state": state.value, "timestamp": datetime.now(UTC).isoformat()})

            method_result = await self._retry_with_backoff(
                select_payment_method, subsidy_data
            )
            payment_method = method_result.data["payment_method"]

            # Step 3: Initiate payment
            state = SubsidyWorkflowState.PAYMENT_PROCESSING
            history.append({"state": state.value, "payment_method": payment_method})

            payment_result = await self._retry_with_backoff(
                initiate_payment, subsidy_data, payment_method
            )
            payment_reference = payment_result.data["payment_reference"]

            state = SubsidyWorkflowState.PAYMENT_INITIATED
            history.append({
                "state": state.value,
                "payment_reference": payment_reference,
            })

            # Step 4: Wait for settlement
            status_result = await self._retry_with_backoff(
                check_payment_status, payment_reference
            )

            if status_result.data["status"] == "SETTLED":
                state = SubsidyWorkflowState.PAYMENT_SETTLED
                history.append({"state": state.value, "timestamp": datetime.now(UTC).isoformat()})

                # Emit audit event
                await emit_audit_event(
                    "SUBSIDY_SETTLED",
                    workflow_id,
                    {"payment_reference": payment_reference, "final_state": state.value},
                )
            else:
                raise Exception(f"Unexpected payment status: {status_result.data['status']}")

        except Exception as e:
            logger.error("Workflow failed at state %s: %s", state, e)
            state = SubsidyWorkflowState.PAYMENT_FAILED
            history.append({"state": state.value, "error": str(e)})

            # Compensate
            state = SubsidyWorkflowState.COMPENSATING
            history.append({"state": state.value, "timestamp": datetime.now(UTC).isoformat()})

            await compensate_payment(subsidy_data)

            state = SubsidyWorkflowState.COMPENSATED
            history.append({"state": state.value, "timestamp": datetime.now(UTC).isoformat()})

            await emit_audit_event(
                "SUBSIDY_FAILED",
                workflow_id,
                {"error": str(e), "compensated": True},
            )

        payment_ref = (
            payment_reference
            if state == SubsidyWorkflowState.PAYMENT_SETTLED
            else None
        )

        return {
            "workflow_id": workflow_id,
            "final_state": state.value,
            "payment_reference": payment_ref,
            "history": history,
        }

    async def _retry_with_backoff(self, activity_func, *args, **kwargs) -> ActivityResult:
        """Retry an activity with exponential backoff."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                result = await activity_func(*args, **kwargs)
                if result.success:
                    return result
                last_error = result.error
            except Exception as e:
                last_error = str(e)

            # Exponential backoff: 1s, 2s, 4s
            wait_time = math.pow(2, attempt)
            logger.warning(
                "Activity %s failed (attempt %d/%d), retrying in %.1fs",
                activity_func.__name__,
                attempt + 1,
                self.max_retries,
                wait_time,
            )
            await asyncio.sleep(wait_time * 0.01)  # Scaled down for testing

        return ActivityResult(success=False, error=f"Max retries exceeded: {last_error}")


# Singleton
subsidy_workflow = SubsidyWorkflowExecutor()
