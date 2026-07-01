# Phase 2 Implementation Plan

**Project:** Crisis-Cost Orchestrator  
**Date:** July 1, 2026  
**Status:** Draft v1.0  
**Owner:** Engineering / Product

---

## 1. Executive Summary

Phase 1 completed the foundational schemas, security protocols, AI classifier strategy, and UX design. Phase 2 moves from design artifacts into **implementation-ready architecture** for the three remaining core backend engines and the supporting infrastructure that ties them together.

### Phase 1 Recap (Completed)

| Artifact | Status | Location |
|----------|--------|----------|
| Provider API (F-04) JSON Schema | ✅ Done | `provider-api-f04-request.schema.json` |
| Provider API (F-04) Protobuf | ✅ Done | `schemas/provider-api-f04-request.proto` |
| Urgency Classifier (F-01) Strategy | ✅ Done | `docs/ai/urgency-classifier-strategy.md` |
| Urgency Classifier (F-01) Prompts | ✅ Done | `docs/ai/urgency-classifier-prompts.md` |
| Eligibility Proof Schema | ✅ Done | `schemas/eligibility-proof.schema.json` |
| Eligibility Proof Audit Event Schema | ✅ Done | `schemas/eligibility-proof-audit-event.schema.json` |
| Patient Income Proof Protocol | ✅ Done | `docs/security/patient-income-proof-protocol.md` |
| Data Retention Schedule | ✅ Done | `docs/security/retention-schedule.md` |
| Encounter Flow Architecture | ✅ Done | `docs/architecture/encounter-flow.mmd` |
| Patient Cost Dashboard UX | ✅ Done | `docs/design/patient-cost-dashboard-ux.md` |

### Phase 2 Scope

| Feature | ID | Deliverable | Priority |
|---------|-----|-------------|----------|
| Affordability Engine | F-02 | Architecture + implementation spec | P0 |
| Subsidy Orchestrator | F-03 | Architecture + implementation spec | P0 |
| Audit Ledger | F-06 | Implementation spec + integration plan | P0 |
| OpenAPI Specification | — | Generated from F-04 schemas | P1 |
| Provider Dashboard | F-07 | UX architecture | P1 |

---

## 2. Phase 2 Priority Matrix

```
                        HIGH IMPACT
                            │
         F-02 Affordability │ F-03 Subsidy Orchestrator
              Engine        │
                            │
   ─────────────────────────┼─────────────────────────
                            │
         F-06 Audit Ledger  │ F-07 Provider Dashboard
                            │
                        LOW IMPACT
        LOW EFFORT ────────┼──────── HIGH EFFORT
```

**Priority rationale:**
- **F-02 and F-03** are the core financial engines — without them, the platform cannot function. They depend on F-04 (ingestion) and F-01 (classification) which are complete.
- **F-06** is a compliance gate — cannot ship without immutable audit trail.
- **F-07** is important for provider adoption but can follow backend completion.
- **OpenAPI spec** unblocks provider integration testing.

---

## 3. F-02 Affordability Engine — Architecture Spec

### 3.1 Purpose

The Affordability Engine calculates the maximum out-of-pocket cost a patient is responsible for, given:
- their verified eligibility proof (income bracket, affordability tier)
- the urgency classification from F-01
- the encounter's billing context from F-04

### 3.2 Core Responsibility

```
Input:
  ├── EligibilityProof (from eligibility-proof.schema.json)
  ├── UrgencyResult (from F-01 classifier output)
  └── BillingContext (from F-04 provider payload)

Output:
  ├── affordability_cap_cents (max patient responsibility)
  ├── subsidy_amount_cents (platform/provider subsidy)
  ├── cap_rule_applied (which rule generated the cap)
  └── confidence_level (based on proof assurance level)
```

### 3.3 Affordability Cap Calculation Logic

The core formula derived from the PRD:

```
annual_income_cents = income_bracket.midpoint (or conservative estimate)
affordability_cap = annual_income_cents × 0.10   (10% cap rule)

patient_responsibility = MIN(estimated_total_cost, affordability_cap)
subsidy_amount = estimated_total_cost - patient_responsibility
```

### 3.4 Income Bracket Mapping

The system uses bracket codes, not raw income. The engine must map bracket codes to calculation ranges:

| Bracket Code | Estimated Annual Range | 10% Cap (Annual) | Per-Encounter Cap |
|-------------|----------------------|------------------|-------------------|
| IB-01 | $0 – $15,000 | $0 – $1,500 | $0 – $375 |
| IB-02 | $15,001 – $30,000 | $1,500 – $3,000 | $375 – $750 |
| IB-03 | $30,001 – $50,000 | $3,000 – $5,000 | $750 – $1,250 |
| IB-04 | $50,001 – $75,000 | $5,000 – $7,500 | $1,250 – $1,875 |
| IB-05 | $75,001 – $100,000 | $7,500 – $10,000 | $1,875 – $2,500 |
| IB-06 | $100,001+ | $10,000+ | $2,500+ |

**Note:** Per-encounter cap is the annual cap divided by a policy-defined encounter frequency factor (default: 4 quarterly encounters).

### 3.5 Affordability Tier Rules

| Tier | Condition | Cap Multiplier |
|------|-----------|----------------|
| TIER-CRITICAL | Income ≤ $15k AND emergency encounter | 0.05 (5%) |
| TIER-LOW | Income ≤ $30k OR Medicaid-qualified | 0.08 (8%) |
| TIER-STANDARD | Income ≤ $75k | 0.10 (10%) |
| TIER-MODERATE | Income > $75k | 0.12 (12%) |
| TIER-UNVERIFIED | No valid proof | No cap applied (full responsibility) |

### 3.6 Urgency-Based Override Rules

```
IF urgency_label == "CRITICAL":
    affordability_cap = affordability_cap × 0.75   # 25% additional protection
    subsidy_amount = subsidy_amount + (original_cap × 0.25)

IF urgency_label == "ROUTINE" AND encounter_class == "OUTPATIENT":
    affordability_cap = affordability_cap × 1.0    # standard cap, no override
```

### 3.7 Implementation Spec

```
Service: AffordabilityEngine
Input Contract:
  - patient_pseudo_id: UUID
  - proof_id: UUID
  - urgency_label: "CRITICAL" | "URGENT" | "ROUTINE"
  - estimated_total_cents: integer
  - encounter_class: string
  - income_bracket_code: string (from proof)
  - affordability_tier: string (from proof)
  - verification_assurance_level: string (from proof)

Output Contract:
  - affordability_cap_cents: integer
  - patient_responsibility_cents: integer
  - subsidy_amount_cents: integer
  - cap_rule_applied: string
  - tier_applied: string
  - urgency_override: boolean
  - confidence_level: "HIGH" | "MODERATE" | "LOW"
  - computed_at: timestamp

SLA:
  - Latency: < 50ms p99
  - Idempotent: yes (same inputs → same outputs)
  - Stateless: yes (no side effects)
```

### 3.8 API Endpoint (Proposed)

```
POST /api/v1/affordability/calculate
Content-Type: application/json
Authorization: Bearer <service-token>

Request: AffordabilityCalculationRequest
Response: AffordabilityCalculationResponse

Error codes:
  400 - Invalid request payload
  404 - Proof not found or expired
  422 - Proof verification failed
  500 - Internal computation error
```

---

## 4. F-03 Subsidy Orchestrator — Architecture Spec

### 4.1 Purpose

The Subsidy Orchestrator manages the lifecycle of subsidy payments from the platform to healthcare providers. It uses Temporal.io workflows to ensure reliable, auditable, and idempotent payment orchestration.

### 4.2 Core Workflow

```
Encounter Ingested
    │
    ▼
Urgency Classified
    │
    ▼
Affordability Calculated
    │
    ▼
Subsidy Orchestrator Activated
    │
    ├── 1. Validate subsidy eligibility
    │      - Proof is ACTIVE
    │      - Affordability cap is computed
    │      - Subsidy amount > $0
    │
    ├── 2. Create subsidy record
    │      - Write to subsidy_ledger (mutable operational store)
    │      - Status: PENDING
    │
    ├── 3. Initiate payment
    │      - Route to Payment Rails (ACH, wire, or stablecoin)
    │      - Generate payment reference
    │
    ├── 4. Await confirmation
    │      - Poll payment provider
    │      - Timeout: 72 hours
    │
    ├── 5. Settle or fail
    │      - On success: status → SETTLED
    │      - On failure: status → FAILED, trigger retry (max 3)
    │
    └── 6. Audit
           - Write subsidy lifecycle event to QLDB
           - Update provider dashboard reconciliation
```

### 4.3 Subsidy Record Schema

```json
{
  "subsidy_id": "uuid",
  "encounter_id": "string",
  "patient_pseudo_id": "uuid",
  "provider_organization_id": "uuid",
  "proof_id": "uuid",
  "urgency_label": "CRITICAL|URGENT|ROUTINE",
  "affordability_cap_cents": 0,
  "patient_responsibility_cents": 0,
  "subsidy_amount_cents": 0,
  "subsidy_status": "PENDING|PROCESSING|SETTLED|FAILED|REFUNDED",
  "payment_reference": "string|null",
  "payment_method": "ACH|WIRE|STABLECOIN",
  "created_at": "timestamp",
  "settled_at": "timestamp|null",
  "failure_reason": "string|null",
  "retry_count": 0,
  "audit_event_id": "uuid"
}
```

### 4.4 Temporal Workflow Definition

```
Workflow: SubsidyOrchestrationWorkflow
  Input: SubsidyWorkflowInput
  Steps:
    1. ValidateSubsidyEligibility(input)
    2. CreateSubsidyRecord(input) → subsidy_id
    3. InitiatePayment(subsidy_id) → payment_reference
    4. AwaitPaymentConfirmation(payment_reference, timeout=72h)
    5. HandlePaymentOutcome(subsidy_id, outcome)
       ├── ON SUCCESS: SettleSubsidy(subsidy_id)
       └── ON FAILURE: RetryOrFail(subsidy_id, retry_count)
    6. EmitAuditEvent(subsidy_id, final_status)

  Retry Policy:
    - Max retries: 3
    - Backoff: exponential (1h, 4h, 12h)
    - Non-retryable errors: INVALID_ACCOUNT, COMPLIANCE_BLOCK

  Timeout Policy:
    - Step 4 (payment confirmation): 72 hours
    - Workflow total: 7 days
```

### 4.5 Payment Rails Integration

| Rail | Use Case | Settlement Time | Fee |
|------|----------|----------------|-----|
| ACH | Standard provider payouts | 2-3 business days | $0.25/tx |
| Wire | Large subsidy amounts (>$10k) | Same day | $15/tx |
| Stablecoin | Emergency / instant payouts | < 1 hour | Network gas |

### 4.6 Reconciliation

The orchestrator must support daily reconciliation:

```
Daily Reconciliation Job:
  1. Fetch all subsidies created in last 24h
  2. Match against payment rail confirmations
  3. Flag mismatches (settled but not confirmed, or vice versa)
  4. Generate reconciliation report
  5. Write reconciliation audit event to QLDB
```

### 4.7 API Endpoints (Proposed)

```
POST   /api/v1/subsidies                    # Create subsidy record
GET    /api/v1/subsidies/:id                # Get subsidy status
POST   /api/v1/subsidies/:id/approve        # Approve for payment
POST   /api/v1/subsidies/:id/cancel         # Cancel subsidy
GET    /api/v1/subsidies?encounter_id=      # List subsidies by encounter
GET    /api/v1/subsidies/reconciliation     # Daily reconciliation report
```

---

## 5. F-06 Audit Ledger — Implementation Spec

### 5.1 Purpose

The Audit Ledger provides an **immutable, append-only** record of every material event in the platform. It is the compliance backbone — no event may be silenced, altered, or deleted.

### 5.2 Technology Choice

| Option | Pros | Cons |
|--------|------|------|
| **Amazon QLDB** (recommended) | Immutable, cryptographically verifiable, managed | AWS lock-in, cost |
| PostgreSQL + append-only tables | Familiar, flexible | Requires custom immutability enforcement |
| Amazon QLDB + PostgreSQL hybrid | Best of both | Complexity |

**Recommendation:** Amazon QLDB for primary immutable ledger; PostgreSQL for operational queries via projected views.

### 5.3 Event Taxonomy

All events follow a consistent envelope:

```json
{
  "event_id": "uuid",
  "event_type": "string",
  "event_timestamp": "ISO-8601",
  "actor": {
    "actor_type": "SYSTEM|PROVIDER|PATIENT|VERIFICATION_PROVIDER",
    "actor_id": "string"
  },
  "entity": {
    "entity_type": "ENCOUNTER|ELIGIBILITY_PROOF|SUBSIDY|AFFORDABILITY_DECISION",
    "entity_id": "string"
  },
  "payload": {},
  "integrity_hash": "SHA-256",
  "schema_version": "1.0.0"
}
```

### 5.4 Required Event Types

| Event Type | Trigger | Entity |
|-----------|---------|--------|
| `ENCOUNTER_INGESTED` | F-04 intake accepted | ENCOUNTER |
| `URGENCY_CLASSIFIED` | F-01 classifier output | ENCOUNTER |
| `ELIGIBILITY_PROOF_INGESTED` | Proof received and validated | ELIGIBILITY_PROOF |
| `ELIGIBILITY_PROOF_VERIFIED` | Proof signature verified | ELIGIBILITY_PROOF |
| `ELIGIBILITY_PROOF_EXPIRED` | Proof validity window elapsed | ELIGIBILITY_PROOF |
| `ELIGIBILITY_PROOF_REVOKED` | Proof revoked by issuer | ELIGIBILITY_PROOF |
| `AFFORDABILITY_DECISION_COMPUTED` | F-02 engine output | AFFORDABILITY_DECISION |
| `SUBSIDY_CREATED` | F-03 subsidy record created | SUBSIDY |
| `SUBSIDY_PAYMENT_INITIATED` | Payment sent to rail | SUBSIDY |
| `SUBSIDY_SETTLED` | Payment confirmed | SUBSIDY |
| `SUBSIDY_FAILED` | Payment failed after retries | SUBSIDY |
| `BREAK_GLASS_ACCESS` | Emergency access granted | ANY |
| `KEY_ROTATED` | KMS key rotation | SYSTEM |
| `RETENTION_PURGE_EXECUTED` | Data purge completed | SYSTEM |
| `LEDGER_DIGEST_VERIFIED` | Daily integrity check | SYSTEM |

### 5.5 Ledger Integrity Protocol

```
Daily Integrity Check (automated):
  1. Compute hash chain of all events since last check
  2. Compare against stored ledger digest
  3. If mismatch → trigger INCIDENT_RESPONSE
  4. Store verification result as LEDGER_DIGEST_VERIFIED event

On-Demand Verification:
  - Available via API for compliance/audit teams
  - Returns: last_verified_at, chain_status, event_count
```

### 5.6 Integration Points

```
Provider API Gateway ──────► QLDB (ENCOUNTER_INGESTED)
Urgency Classifier ────────► QLDB (URGENCY_CLASSIFIED)
Affordability Engine ──────► QLDB (AFFORDABILITY_DECISION_COMPUTED)
Subsidy Orchestrator ──────► QLDB (SUBSIDY_*)
Verification Service ──────► QLDB (ELIGIBILITY_PROOF_*)
Retention Service ─────────► QLDB (RETENTION_PURGE_EXECUTED)
Key Management ────────────► QLDB (KEY_ROTATED)
```

---

## 6. OpenAPI Specification Generation

### 6.1 Scope

Generate an OpenAPI 3.1 specification from the existing F-04 JSON Schema and the proposed Phase 2 endpoints.

### 6.2 Endpoints to Document

| Method | Path | Description | Source |
|--------|------|-------------|--------|
| POST | `/api/v1/encounters` | Provider intake (F-04) | `provider-api-f04-request.schema.json` |
| POST | `/api/v1/urgency/classify` | Trigger F-01 classification | `urgency-classifier-prompts.md` |
| POST | `/api/v1/affordability/calculate` | F-02 calculation | Phase 2 spec |
| POST | `/api/v1/subsidies` | F-03 create subsidy | Phase 2 spec |
| GET | `/api/v1/subsidies/:id` | F-03 subsidy status | Phase 2 spec |
| GET | `/api/v1/audit/events` | F-06 query audit events | Phase 2 spec |
| GET | `/api/v1/patients/:pseudo_id/results` | Patient dashboard data | Phase 2 spec |

### 6.3 Authentication & Security

All endpoints require:
- mTLS for service-to-service calls
- Bearer token (JWT) for client-facing calls
- HIPAA-permitted-use basis header
- Request ID for idempotency

---

## 7. Agent Integration Plan (Phase 2)

### 7.1 Agents to Activate

| Agent | Role | Target Features |
|-------|------|-----------------|
| `specialized/medical-billing-coding-specialist` | Validate CPT/ICD-10 mapping in billing context | F-02, F-04 |
| `engineering/engineering-backend-architect` | Design Temporal workflows for F-03 | F-03 |
| `engineering/engineering-ai-engineer` | Implement F-01 classifier runtime | F-01 |
| `security/security-compliance-auditor` | Audit QLDB schema and ledger integrity | F-06 |
| `design/design-ux-architect` | Finalize F-07 Provider Dashboard | F-07 |
| `specialized/data-privacy-officer` | Review data flow for HIPAA compliance | F-02, F-03 |

### 7.2 Agent Workflow

```
Phase 2 Agent Sprint:
  Week 1: billing-specialist + software-architect → F-02 spec validation
  Week 2: backend-architect → F-03 Temporal workflow design
  Week 3: ai-engineer → F-01 classifier runtime prototype
  Week 4: security-auditor + data-privacy-officer → F-06 audit review
  Week 5: ux-architect → F-07 provider dashboard wireframes
```

---

## 8. Implementation Timeline

### Q2 2026 Sprint Plan (12 weeks)

| Week | Focus | Deliverables |
|------|-------|-------------|
| 1-2 | F-02 Affordability Engine | Architecture spec, API contract, income bracket mapping |
| 3-4 | F-03 Subsidy Orchestrator | Temporal workflow design, payment rails integration spec |
| 5-6 | F-06 Audit Ledger | QLDB schema, event taxonomy, integrity protocol |
| 7-8 | OpenAPI Generation | Full OpenAPI 3.1 spec from all schemas |
| 9-10 | Integration Testing | End-to-end flow: F-04 → F-01 → F-02 → F-03 → F-06 |
| 11-12 | Provider Dashboard | F-07 UX architecture, wireframes, API contract |

### Success Criteria

- [ ] F-02 Affordability Engine spec complete and validated by billing specialist
- [ ] F-03 Subsidy Orchestrator Temporal workflow defined and peer-reviewed
- [ ] F-06 Audit Ledger QLDB schema deployed to dev environment
- [ ] OpenAPI 3.1 spec published and validated against all schemas
- [ ] End-to-end integration test passing (simulated EHR → subsidy payout)
- [ ] Provider Dashboard wireframes approved by design review

---

## 9. Risks & Mitigations (Phase 2)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Income bracket mapping lacks real-world calibration | High | Partner with 2 safety-net hospitals for bracket validation |
| Temporal.io workflow complexity | Medium | Start with linear workflow, add compensation later |
| QLDB cost at scale | Medium | Evaluate PostgreSQL append-only as fallback |
| Payment rails compliance (ACH/wire) | High | Engage fintech compliance counsel early |
| OpenAPI spec drift from schemas | Low | Generate spec automatically from JSON Schema |

---

## 10. Recommended Next Actions

1. **Immediate (this week):**
   - Review and approve this Phase 2 plan
   - Activate `engineering-backend-architect` agent for F-03 design
   - Begin F-02 Affordability Engine detailed spec

2. **Week 1-2:**
   - Finalize income bracket mapping with billing specialist
   - Define F-02 API contract in OpenAPI draft
   - Create F-02 unit test cases

3. **Week 3-4:**
   - Design F-03 Temporal workflows
   - Research payment rails integration options
   - Begin F-06 QLDB schema design

---

*This document is the official Phase 2 implementation plan. All architecture decisions should be recorded as ADRs and linked back to this plan.*
