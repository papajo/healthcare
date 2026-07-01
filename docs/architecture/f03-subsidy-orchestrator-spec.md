# F-03 Subsidy Orchestrator — Detailed Implementation Spec

**Project:** Crisis-Cost Orchestrator  
**Feature:** F-03 Subsidy Orchestrator  
**Status:** Draft v1.0  
**Owner:** Engineering  
**Depends On:** F-02 Affordability Engine (Phase 2), F-06 Audit Ledger (Phase 2)

---

## 1. Purpose

The Subsidy Orchestrator manages the complete lifecycle of subsidy payments from the platform to healthcare providers. It ensures that once the Affordability Engine determines a patient's subsidy amount, that amount is reliably, idempotently, and auditably transferred to the provider.

### 1.1 Design Principles

1. **At-least-once delivery** — a subsidy will be paid if the system allows it; retries are safe
2. **Idempotent operations** — reprocessing the same subsidy produces the same outcome
3. **Workflow-driven** — all orchestration runs through Temporal.io for durability and visibility
4. **Audit-first** — every state transition is recorded before it takes effect
5. **Fail-safe financials** — on ambiguity, hold funds rather than risk incorrect payment

---

## 2. Temporal Workflow Architecture

### 2.1 Why Temporal

| Requirement | Why Temporal Fits |
|------------|-------------------|
| Multi-step payment flow | Durable workflows survive crashes |
| 72-hour payment timeout | Built-in timer and timeout support |
| Retry with backoff | Native retry policies with exponential backoff |
| Audit trail | Workflow history is itself an audit trail |
| Visibility | Temporal UI shows every running workflow |
| Compensation | Saga pattern for rollback on failure |

### 2.2 Workflow Topology

```
┌─────────────────────────────────────────────────────────────┐
│                  SubsidyOrchestrationWorkflow                │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  1. Validate  │───►│ 2. Create    │───►│ 3. Initiate  │  │
│  │  Eligibility  │    │ Subsidy Rec  │    │   Payment    │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                  │          │
│                                                  ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  6. Audit &   │◄───│ 5. Settle or │◄───│ 4. Await     │  │
│  │  Notify       │    │    Fail      │    │ Confirmation │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Subsidy Record Schema

### 3.1 Database Schema (PostgreSQL)

```sql
CREATE TABLE subsidy_records (
    subsidy_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    encounter_id        VARCHAR(64) NOT NULL,
    patient_pseudo_id   UUID NOT NULL,
    provider_org_id     UUID NOT NULL,
    proof_id            UUID NOT NULL,
    
    -- Financial details
    estimated_total_cents       BIGINT NOT NULL,
    affordability_cap_cents     BIGINT NOT NULL,
    patient_responsibility_cents BIGINT NOT NULL,
    subsidy_amount_cents        BIGINT NOT NULL,
    
    -- Classification
    urgency_label       VARCHAR(16) NOT NULL CHECK (urgency_label IN ('CRITICAL', 'URGENT', 'ROUTINE')),
    tier_applied        VARCHAR(32) NOT NULL,
    
    -- Payment
    payment_method      VARCHAR(16) CHECK (payment_method IN ('ACH', 'WIRE', 'STABLECOIN')),
    payment_reference   VARCHAR(128),
    
    -- Status
    subsidy_status      VARCHAR(16) NOT NULL DEFAULT 'PENDING' 
                        CHECK (subsidy_status IN ('PENDING', 'VALIDATING', 'PROCESSING', 'SETTLED', 'FAILED', 'CANCELLED')),
    failure_reason      TEXT,
    retry_count         INTEGER DEFAULT 0,
    
    -- Audit
    audit_event_id      UUID,
    workflow_id         VARCHAR(128),  -- Temporal workflow ID
    
    -- Timestamps
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    settled_at          TIMESTAMP,
    failed_at           TIMESTAMP
);

CREATE INDEX idx_subsidy_encounter ON subsidy_records(encounter_id);
CREATE INDEX idx_subsidy_patient ON subsidy_records(patient_pseudo_id);
CREATE INDEX idx_subsidy_status ON subsidy_records(subsidy_status);
CREATE INDEX idx_subsidy_provider ON subsidy_records(provider_org_id);
```

### 3.2 Record Lifecycle States

```
                    ┌─────────────┐
                    │   PENDING   │  ← Initial state
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
              ┌────►│  VALIDATING │  ← Proof verification
              │     └──────┬──────┘
              │            │
              │            ▼
              │     ┌─────────────┐
              │     │  PROCESSING │  ← Payment initiated
              │     └──────┬──────┘
              │            │
              │       ┌────┴────┐
              │       ▼         ▼
              │  ┌─────────┐ ┌─────────┐
              │  │ SETTLED │ │ FAILED  │
              │  └─────────┘ └────┬────┘
              │                   │
              │              (retry < 3)
              │                   │
              └───────────────────┘
              
                    ┌─────────────┐
                    │  CANCELLED  │  ← Manual cancellation
                    └─────────────┘
```

---

## 4. Temporal Workflow Definition

### 4.1 Workflow Input

```json
{
  "subsidy_id": "uuid",
  "encounter_id": "string",
  "patient_pseudo_id": "uuid",
  "provider_org_id": "uuid",
  "proof_id": "uuid",
  "urgency_label": "CRITICAL|URGENT|ROUTINE",
  "estimated_total_cents": 0,
  "affordability_cap_cents": 0,
  "patient_responsibility_cents": 0,
  "subsidy_amount_cents": 0,
  "tier_applied": "string"
}
```

### 4.2 Workflow Steps

```
Workflow: SubsidyOrchestrationWorkflow
  TaskQueue: subsidy-orchestrator
  Timeout: 7 days

  Step 1: ValidateSubsidyEligibility
    - Verify proof is ACTIVE and not expired
    - Verify subsidy_amount_cents > 0
    - Verify patient_pseudo_id matches proof
    - On failure: RETURN EligibilityInvalid(subsidy_id)
    
  Step 2: CreateSubsidyRecord
    - Write subsidy record to PostgreSQL
    - Status: PENDING → VALIDATING
    - Emit AUDIT_EVENT: SUBSIDY_CREATED
    - On failure: COMPENSATION → DeleteSubsidyRecord
    
  Step 3: DeterminePaymentMethod
    - IF subsidy_amount_cents > 1,000,000: WIRE
    - IF subsidy_amount_cents > 10,000,000 AND provider supports: STABLECOIN
    - ELSE: ACH
    - Update subsidy record: payment_method, status → PROCESSING
    
  Step 4: InitiatePayment
    - Call payment rail API with provider banking details
    - Store payment_reference
    - Emit AUDIT_EVENT: SUBSIDY_PAYMENT_INITIATED
    - On failure: RETRY (max 3, exponential backoff)
    
  Step 5: AwaitPaymentConfirmation
    - Timeout: 72 hours
    - Poll payment rail for confirmation
    - On timeout: COMPENSATION → CancelPayment(subsidy_id)
    
  Step 6: SettleSubsidy
    - Update subsidy status: SETTLED
    - Set settled_at timestamp
    - Emit AUDIT_EVENT: SUBSIDY_SETTLED
    - Notify provider dashboard
    
  Step 7: EmitFinalAuditEvent
    - Complete workflow audit trail
    - Return SubsidyResult(subsidy_id, SETTLED)
```

### 4.3 Compensation (Saga) Actions

```
COMPENSATION for Step 2 (CreateSubsidyRecord):
  - Delete subsidy record from PostgreSQL
  - Emit AUDIT_EVENT: SUBSIDY_CANCELLED

COMPENSATION for Step 5 (AwaitPaymentConfirmation timeout):
  - Cancel payment with payment rail
  - Update subsidy status: FAILED
  - Set failure_reason: "PAYMENT_TIMEOUT"
  - Emit AUDIT_EVENT: SUBSIDY_FAILED
```

### 4.4 Retry Policy

```yaml
retry_policy:
  maximum_attempts: 3
  initial_interval: 3600      # 1 hour
  maximum_interval: 43200     # 12 hours
  backoff_coefficient: 2.0
  non_retryable_error_types:
    - INVALID_ACCOUNT
    - COMPLIANCE_BLOCK
    - PROVIDER_NOT_FOUND
```

---

## 5. Payment Rails Integration

### 5.1 Payment Rail Abstraction

```python
class PaymentRail(ABC):
    """Abstract base for payment rail implementations."""
    
    @abstractmethod
    async def initiate_payment(
        self,
        subsidy_id: str,
        provider_id: str,
        amount_cents: int,
        reference: str
    ) -> PaymentInitiationResult:
        """Initiate a payment. Returns payment_reference."""
        pass
    
    @abstractmethod
    async def check_status(
        self,
        payment_reference: str
    ) -> PaymentStatus:
        """Check payment status. Returns PENDING/SETTLED/FAILED."""
        pass
    
    @abstractmethod
    async def cancel_payment(
        self,
        payment_reference: str
    ) -> bool:
        """Attempt to cancel a pending payment."""
        pass
```

### 5.2 ACH Rail Implementation

```
Provider: Stripe / Plaid / Dwolla
Settlement: 2-3 business days
Fee: $0.25 per transaction
Limits: No upper limit for verified providers

Flow:
  1. Debit platform ACH account
  2. Credit provider bank account
  3. Await NACHA confirmation (T+2)
  4. Update subsidy record
```

### 5.3 Wire Rail Implementation

```
Provider: SWIFT / Fedwire
Settlement: Same day (if submitted before 4pm ET)
Fee: $15 per transaction
Limits: Preferred for amounts > $10,000

Flow:
  1. Initiate wire transfer
  2. Await Fedwire confirmation (same day)
  3. Update subsidy record
```

### 5.4 Stablecoin Rail Implementation (Future)

```
Provider: Circle / USDC
Settlement: < 1 hour
Fee: Network gas only
Limits: Emergency/instant payouts only

Flow:
  1. Convert USD to USDC
  2. Transfer to provider wallet
  3. Await blockchain confirmation (3 blocks)
  4. Update subsidy record
```

---

## 6. Provider Banking Details

### 6.1 Provider Payment Profile Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ProviderPaymentProfile",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "provider_organization_id",
    "payment_method",
    "account_verified"
  ],
  "properties": {
    "provider_organization_id": {
      "type": "string",
      "format": "uuid"
    },
    "payment_method": {
      "type": "string",
      "enum": ["ACH", "WIRE", "STABLECOIN"]
    },
    "ach_details": {
      "type": "object",
      "properties": {
        "routing_number": { "type": "string", "pattern": "^[0-9]{9}$" },
        "account_number_encrypted": { "type": "string" },
        "account_type": { "type": "string", "enum": ["CHECKING", "SAVINGS"] }
      }
    },
    "wire_details": {
      "type": "object",
      "properties": {
        "swift_code": { "type": "string", "pattern": "^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$" },
        "bank_name": { "type": "string" },
        "account_number_encrypted": { "type": "string" }
      }
    },
    "stablecoin_details": {
      "type": "object",
      "properties": {
        "wallet_address": { "type": "string", "pattern": "^0x[0-9a-fA-F]{40}$" },
        "chain_id": { "type": "integer" }
      }
    },
    "account_verified": {
      "type": "boolean",
      "const": true
    },
    "verified_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

### 6.2 Provider Verification Requirements

Before a provider can receive subsidy payments:

1. **ACH:** Verify micro-deposit (two small deposits, provider confirms amounts)
2. **Wire:** Verify SWIFT code and bank letter
3. **Stablecoin:** Verify wallet ownership via signature challenge

---

## 7. API Endpoints

### 7.1 Create Subsidy

```
POST /api/v1/subsidies
Content-Type: application/json
Authorization: Bearer <service-token>

Request: SubsidyCreationRequest
Response 201:
{
  "subsidy_id": "uuid",
  "subsidy_status": "PENDING",
  "workflow_id": "temporal-workflow-id",
  "created_at": "timestamp"
}
```

### 7.2 Get Subsidy Status

```
GET /api/v1/subsidies/:subsidy_id
Authorization: Bearer <service-token>

Response 200:
{
  "subsidy_id": "uuid",
  "encounter_id": "string",
  "subsidy_status": "SETTLED",
  "subsidy_amount_cents": 150000,
  "payment_reference": "ach-ref-123",
  "settled_at": "timestamp"
}
```

### 7.3 Cancel Subsidy

```
POST /api/v1/subsidies/:subsidy_id/cancel
Authorization: Bearer <service-token>

Request: { "reason": "string" }
Response 200:
{
  "subsidy_id": "uuid",
  "subsidy_status": "CANCELLED",
  "cancelled_at": "timestamp"
}
```

### 7.4 List Subsidies by Encounter

```
GET /api/v1/subsidies?encounter_id={id}&status={status}
Authorization: Bearer <service-token>

Response 200:
{
  "subsidies": [...],
  "total": 1,
  "has_more": false
}
```

### 7.5 Reconciliation Report

```
GET /api/v1/subsidies/reconciliation?date={date}
Authorization: Bearer <service-token>

Response 200:
{
  "reconciliation_date": "2026-07-01",
  "total_created": 142,
  "total_settled": 138,
  "total_failed": 3,
  "total_pending": 1,
  "total_amount_settled_cents": 45000000,
  "mismatches": []
}
```

---

## 8. Reconciliation Job

### 8.1 Daily Reconciliation Process

```
Job: DailySubsidyReconciliation
Schedule: 0 2 * * * (2:00 AM UTC daily)

Steps:
  1. Fetch all subsidies created in last 24 hours
  2. For each subsidy, check payment rail confirmation
  3. Match:
     - Settlement confirmed by rail AND status = SETTLED → OK
     - Settlement confirmed by rail AND status ≠ SETTLED → UPDATE status
     - No confirmation AND status = SETTLED → FLAG mismatch
     - No confirmation AND status = PENDING/PROCESSING → continue waiting
  4. Generate reconciliation report
  5. Write RECONCILIATION_COMPLETED audit event
  6. If mismatches found: ALERT operations team
```

### 8.2 Reconciliation Report Schema

```json
{
  "report_id": "uuid",
  "report_date": "date",
  "period_start": "timestamp",
  "period_end": "timestamp",
  "summary": {
    "total_subsidies": 0,
    "total_settled": 0,
    "total_failed": 0,
    "total_pending": 0,
    "total_amount_settled_cents": 0,
    "total_amount_pending_cents": 0
  },
  "mismatches": [
    {
      "subsidy_id": "uuid",
      "expected_status": "SETTLED",
      "actual_status": "PROCESSING",
      "payment_reference": "string",
      "rail_confirmation": "string|null"
    }
  ],
  "generated_at": "timestamp"
}
```

---

## 9. SLA Requirements

| Metric | Target |
|--------|--------|
| Workflow start latency | < 100ms |
| Payment initiation | < 5 seconds |
| ACH settlement | 2-3 business days |
| Wire settlement | Same day |
| Stablecoin settlement | < 1 hour |
| Reconciliation completion | < 30 minutes daily |
| Idempotency | Guaranteed |
| At-least-once delivery | Guaranteed |

---

## 10. Error Handling

| Error | Handling | Retry? |
|-------|----------|--------|
| Provider account not found | Fail workflow, alert ops | No |
| Payment rail timeout | Retry with exponential backoff | Yes (max 3) |
| Insufficient platform funds | Hold workflow, alert finance | Yes (after funds) |
| Provider account suspended | Fail workflow, alert compliance | No |
| Compliance block | Fail workflow, no retry | No |
| Network error | Retry immediately | Yes (max 5) |

---

## 11. Monitoring & Alerting

### 11.1 Key Metrics

| Metric | Alert Threshold |
|--------|----------------|
| Workflow failure rate | > 1% in 1 hour |
| Payment timeout rate | > 5% in 24 hours |
| Settlement delay > SLA | Any occurrence |
| Reconciliation mismatch | Any occurrence |
| Platform balance low | < $100,000 |

### 11.2 Dashboard

The Provider Dashboard (F-07) will consume subsidy data via:

```
GET /api/v1/providers/:id/subsidies?month={month}
GET /api/v1/providers/:id/reconciliation?month={month}
GET /api/v1/providers/:id/summary?month={month}
```

---

## 12. Security Requirements

| Requirement | Implementation |
|------------|---------------|
| Payment rail credentials | Stored in KMS, never in application code |
| Provider banking details | Encrypted at rest (AES-256-GCM), field-level |
| All payment API calls | mTLS + JWT |
| Subsidy amount validation | Server-side (cannot be manipulated by client) |
| Dual approval for wire > $50k | Workflow step requires human approval |

---

*This document defines the complete implementation specification for the F-03 Subsidy Orchestrator. All changes must be reviewed by engineering, finance, and compliance.*
