# F-02 Affordability Engine — Detailed Implementation Spec

**Project:** Crisis-Cost Orchestrator  
**Feature:** F-02 Affordability Engine  
**Status:** Draft v1.0  
**Owner:** Engineering  
**Depends On:** F-04 Provider API (complete), F-01 Urgency Classifier (complete), Eligibility Proof Schema (complete)

---

## 1. Purpose

The Affordability Engine calculates the maximum out-of-pocket cost a patient is responsible for during an encounter, given their verified eligibility status, the encounter's urgency classification, and the billing context. It enforces the platform's core promise: **no patient pays more than 10% of their annual income for emergency or acute care**.

### 1.1 Design Principles

1. **Deterministic** — same inputs always produce the same output (no randomness)
2. **Idempotent** — re-running the calculation for the same encounter returns the same result
3. **Auditable** — every decision path produces a traceable output
4. **Stateless** — no side effects, no persistent state within the engine itself
5. **Fail-safe** — if proof is missing or invalid, default to no cap (patient responsibility), never to zero

---

## 2. Input Contract

The engine receives a single calculation request containing all necessary data.

### 2.1 Request Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://crisiscost.health/schemas/affordability-calculation-request.schema.json",
  "title": "AffordabilityCalculationRequest",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "request_id",
    "encounter_id",
    "patient_pseudo_id",
    "urgency_label",
    "estimated_total_cents",
    "encounter_class"
  ],
  "properties": {
    "request_id": {
      "type": "string",
      "format": "uuid",
      "description": "Client-generated idempotency key."
    },
    "encounter_id": {
      "type": "string",
      "maxLength": 64,
      "description": "Reference to the F-04 encounter."
    },
    "patient_pseudo_id": {
      "type": "string",
      "format": "uuid",
      "description": "Vault-issued pseudonymous patient identifier."
    },
    "urgency_label": {
      "type": "string",
      "enum": ["CRITICAL", "URGENT", "ROUTINE"],
      "description": "Output from F-01 Urgency Classifier."
    },
    "estimated_total_cents": {
      "type": "integer",
      "minimum": 0,
      "description": "Estimated total cost of the encounter in cents."
    },
    "encounter_class": {
      "type": "string",
      "enum": ["EMERGENCY", "URGENT", "OBSERVATION", "OUTPATIENT", "INPATIENT"],
      "description": "From F-04 encounter.encounter_class."
    },
    "eligibility_proof": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "proof_id",
        "income_bracket_code",
        "affordability_tier",
        "eligibility_status_normalized",
        "verification_assurance_level",
        "proof_valid_from",
        "proof_valid_to",
        "revocation_status"
      ],
      "properties": {
        "proof_id": {
          "type": "string",
          "format": "uuid"
        },
        "income_bracket_code": {
          "type": "string",
          "pattern": "^IB-[A-Z0-9][A-Z0-9-]{0,15}$"
        },
        "affordability_tier": {
          "type": "string",
          "pattern": "^TIER-[A-Z0-9][A-Z0-9-]{0,23}$"
        },
        "eligibility_status_normalized": {
          "type": "string",
          "enum": ["ELIGIBLE", "CONDITIONALLY_ELIGIBLE", "NOT_ELIGIBLE", "NOT_VERIFIED", "EXPIRED", "REVOKED"]
        },
        "verification_assurance_level": {
          "type": "string",
          "enum": ["LOW", "MODERATE", "HIGH", "VERY_HIGH"]
        },
        "proof_valid_from": {
          "type": "string",
          "format": "date-time"
        },
        "proof_valid_to": {
          "type": "string",
          "format": "date-time"
        },
        "revocation_status": {
          "type": "string",
          "enum": ["ACTIVE", "REVOKED", "EXPIRED", "SUPERSEDED"]
        }
      },
      "description": "Minimal proof attributes needed for affordability calculation. The engine never handles raw financial evidence."
    },
    "household_size_band": {
      "type": "string",
      "pattern": "^HS-[A-Z0-9][A-Z0-9-]{0,15}$",
      "description": "Optional household size band for enhanced tier calculation."
    }
  }
}
```

### 2.2 Required Inputs Summary

| Field | Source | Required | Notes |
|-------|--------|----------|-------|
| `request_id` | Caller | Yes | Idempotency key |
| `encounter_id` | F-04 | Yes | References the encounter |
| `patient_pseudo_id` | F-04 | Yes | Vault-issued, no direct identity |
| `urgency_label` | F-01 | Yes | CRITICAL / URGENT / ROUTINE |
| `estimated_total_cents` | Billing | Yes | Pre-cap estimated total |
| `encounter_class` | F-04 | Yes | EMERGENCY / URGENT / etc. |
| `eligibility_proof` | Verification Service | No* | If absent, no cap applied |
| `household_size_band` | Verification Service | No | Enhances tier calculation |

*If `eligibility_proof` is absent or invalid, the engine returns `TIER-UNVERIFIED` with no affordability cap.

---

## 3. Output Contract

### 3.1 Response Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://crisiscost.health/schemas/affordability-calculation-response.schema.json",
  "title": "AffordabilityCalculationResponse",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "request_id",
    "affordability_cap_cents",
    "patient_responsibility_cents",
    "subsidy_amount_cents",
    "cap_rule_applied",
    "tier_applied",
    "urgency_override_applied",
    "confidence_level",
    "computed_at"
  ],
  "properties": {
    "request_id": {
      "type": "string",
      "format": "uuid"
    },
    "affordability_cap_cents": {
      "type": "integer",
      "minimum": 0,
      "description": "Maximum patient responsibility after all rules applied."
    },
    "patient_responsibility_cents": {
      "type": "integer",
      "minimum": 0,
      "description": "Final patient responsibility (min of estimated total and cap)."
    },
    "subsidy_amount_cents": {
      "type": "integer",
      "minimum": 0,
      "description": "Amount to be subsidized by the platform."
    },
    "cap_rule_applied": {
      "type": "string",
      "description": "Human-readable rule that generated the cap."
    },
    "tier_applied": {
      "type": "string",
      "enum": ["TIER-CRITICAL", "TIER-LOW", "TIER-STANDARD", "TIER-MODERATE", "TIER-UNVERIFIED"]
    },
    "urgency_override_applied": {
      "type": "boolean",
      "description": "Whether the urgency label modified the base cap."
    },
    "confidence_level": {
      "type": "string",
      "enum": ["HIGH", "MODERATE", "LOW"],
      "description": "Based on proof assurance level and data completeness."
    },
    "computed_at": {
      "type": "string",
      "format": "date-time"
    },
    "calculation_trace": {
      "type": "object",
      "description": "Optional audit trace for debugging and compliance review."
    }
  }
}
```

---

## 4. Calculation Algorithm

### 4.1 Step-by-Step Process

```
FUNCTION calculateAffordability(request):

  // Step 1: Validate proof validity
  IF request.eligibility_proof IS NULL:
    RETURN unverifiedResult(request)

  IF request.eligibility_proof.revocation_status != "ACTIVE":
    RETURN unverifiedResult(request)

  IF NOW() < request.eligibility_proof.proof_valid_from 
     OR NOW() > request.eligibility_proof.proof_valid_to:
    RETURN unverifiedResult(request)

  IF request.eligibility_proof.eligibility_status_normalized NOT IN ["ELIGIBLE", "CONDITIONALLY_ELIGIBLE"]:
    RETURN unverifiedResult(request)

  // Step 2: Determine income bracket midpoint
  bracket = INCOME_BRACKETS[request.eligibility_proof.income_bracket_code]
  IF bracket IS NULL:
    RETURN errorResult("UNKNOWN_INCOME_BRACKET")

  annual_income_cents = bracket.midpoint_cents

  // Step 3: Determine base cap multiplier from tier
  tier = request.eligibility_proof.affordability_tier
  base_multiplier = TIER_MULTIPLIERS[tier]

  // Step 4: Calculate base affordability cap
  base_cap_cents = FLOOR(annual_income_cents × base_multiplier)

  // Step 5: Apply household size adjustment (if provided)
  IF request.household_size_band IS NOT NULL:
    hh_factor = HOUSEHOLD_FACTORS[request.household_size_band]
    base_cap_cents = FLOOR(base_cap_cents × hh_factor)

  // Step 6: Apply per-encounter frequency limit
  per_encounter_cap = FLOOR(base_cap_cents / ENCOUNTER_FREQUENCY_DIVISOR)

  // Step 7: Apply urgency override
  urgency_override = FALSE
  IF request.urgency_label == "CRITICAL":
    per_encounter_cap = FLOOR(per_encounter_cap × 0.75)
    urgency_override = TRUE

  // Step 8: Calculate final patient responsibility
  patient_responsibility = MIN(request.estimated_total_cents, per_encounter_cap)

  // Step 9: Calculate subsidy
  subsidy = request.estimated_total_cents - patient_responsibility

  // Step 10: Determine confidence level
  confidence = determineConfidence(request.eligibility_proof)

  // Step 11: Build result
  RETURN {
    request_id: request.request_id,
    affordability_cap_cents: per_encounter_cap,
    patient_responsibility_cents: patient_responsibility,
    subsidy_amount_cents: subsidy,
    cap_rule_applied: buildRuleDescription(tier, urgency_override),
    tier_applied: tier,
    urgency_override_applied: urgency_override,
    confidence_level: confidence,
    computed_at: NOW()
  }
```

### 4.2 Income Bracket Reference Table

| Bracket Code | Min Annual (cents) | Max Annual (cents) | Midpoint (cents) |
|-------------|-------------------|-------------------|------------------|
| IB-01 | 0 | 1,500,000 | 750,000 |
| IB-02 | 1,500,001 | 3,000,000 | 2,250,000 |
| IB-03 | 3,000,001 | 5,000,000 | 4,000,000 |
| IB-04 | 5,000,001 | 7,500,000 | 6,250,000 |
| IB-05 | 7,500,001 | 10,000,000 | 8,750,000 |
| IB-06 | 10,000,001 | 15,000,000 | 12,500,000 |
| IB-07 | 15,000,001 | 20,000,000 | 17,500,000 |
| IB-08 | 20,000,001 | 30,000,000 | 25,000,000 |
| IB-09 | 30,000,001 | 50,000,000 | 40,000,000 |
| IB-10 | 50,000,001 | 75,000,000 | 62,500,000 |
| IB-11 | 75,000,001 | 100,000,000 | 87,500,000 |
| IB-12 | 100,000,001 | ∞ | 150,000,000 |

### 4.3 Tier Multiplier Table

| Tier Code | Multiplier | When Applied |
|-----------|-----------|-------------|
| TIER-CRITICAL | 0.05 | Income ≤ IB-02 AND emergency encounter |
| TIER-LOW | 0.08 | Income ≤ IB-03 OR Medicaid-qualified |
| TIER-STANDARD | 0.10 | Income ≤ IB-08 (default) |
| TIER-MODERATE | 0.12 | Income > IB-08 |
| TIER-UNVERIFIED | 1.00 | No valid proof — no cap applied |

### 4.4 Household Size Adjustment Factors

| Band | Factor | Description |
|------|--------|-------------|
| HS-1 | 0.70 | Single person, no dependents |
| HS-2 | 0.85 | 2-person household |
| HS-3 | 1.00 | 3-person household (baseline) |
| HS-4 | 1.15 | 4-person household |
| HS-5 | 1.30 | 5+ person household |

### 4.5 Per-Encounter Frequency Divisor

Default: **4** (assumes up to 4 qualifying encounters per year)

This prevents a single patient from exhausting their entire annual cap on one encounter while still providing meaningful protection for recurring emergencies.

---

## 5. Confidence Level Determination

```
FUNCTION determineConfidence(proof):

  IF proof.verification_assurance_level == "VERY_HIGH":
    RETURN "HIGH"
  
  IF proof.verification_assurance_level == "HIGH":
    RETURN "HIGH"
  
  IF proof.verification_assurance_level == "MODERATE":
    RETURN "MODERATE"
  
  IF proof.verification_assurance_level == "LOW":
    RETURN "LOW"

  // Default for unknown assurance levels
  RETURN "LOW"
```

| Confidence | Proof Assurance | Implication |
|-----------|----------------|-------------|
| HIGH | VERY_HIGH or HIGH | Full cap applied, high trust |
| MODERATE | MODERATE | Full cap applied, moderate trust |
| LOW | LOW or unknown | Cap applied but flagged for review |

---

## 6. Unverified / Invalid Proof Handling

When no valid proof is available, the engine returns a transparent "no cap" result:

```
FUNCTION unverifiedResult(request):
  RETURN {
    request_id: request.request_id,
    affordability_cap_cents: request.estimated_total_cents,
    patient_responsibility_cents: request.estimated_total_cents,
    subsidy_amount_cents: 0,
    cap_rule_applied: "NO_PROOF_AVAILABLE",
    tier_applied: "TIER-UNVERIFIED",
    urgency_override_applied: FALSE,
    confidence_level: "LOW",
    computed_at: NOW()
  }
```

**Why no cap?** Without a verified proof, the platform cannot safely assume income or eligibility. Applying a cap without verification risks subsidizing patients who don't qualify, which is a financial and compliance risk. The patient is still directed to verify eligibility.

---

## 7. Error Handling

| Error Code | Condition | HTTP Status | Response |
|-----------|-----------|-------------|----------|
| `INVALID_REQUEST` | Malformed payload | 400 | Error details |
| `UNKNOWN_INCOME_BRACKET` | Bracket code not in reference table | 422 | Error details |
| `UNKNOWN_TIER` | Tier code not recognized | 422 | Error details |
| `PROOF_EXPIRED` | Valid proof but expired | 200* | Result with TIER-UNVERIFIED |
| `PROOF_REVOKED` | Proof revoked by issuer | 200* | Result with TIER-UNVERIFIED |
| `COMPUTATION_ERROR` | Internal failure | 500 | Retry suggestion |

*Note: Expired/revoked proofs return a successful response with TIER-UNVERIFIED rather than an error, because the patient can still receive care — they just don't get the affordability cap.

---

## 8. API Endpoint

### 8.1 Calculate Affordability

```
POST /api/v1/affordability/calculate
Content-Type: application/json
Authorization: Bearer <service-token>
X-Request-ID: <uuid>
X-HIPAA-Use-Basis: PAYMENT

Request Body: AffordabilityCalculationRequest

Response 200:
  Body: AffordabilityCalculationResponse

Response 400:
  { "error": "INVALID_REQUEST", "message": "..." }

Response 422:
  { "error": "UNKNOWN_INCOME_BRACKET", "message": "..." }

Response 500:
  { "error": "COMPUTATION_ERROR", "message": "..." }
```

### 8.2 Batch Calculate (Future)

```
POST /api/v1/affordability/calculate-batch
Content-Type: application/json

Request Body: { "calculations": [AffordabilityCalculationRequest, ...] }
Response 200: { "results": [AffordabilityCalculationResponse, ...] }
```

---

## 9. SLA Requirements

| Metric | Target |
|--------|--------|
| Latency (p50) | < 10ms |
| Latency (p99) | < 50ms |
| Throughput | 10,000 requests/sec |
| Idempotency | Guaranteed (same request_id → same result) |
| Availability | 99.99% |
| Error rate | < 0.01% |

---

## 10. Unit Test Cases

### 10.1 Happy Path Tests

| Test ID | Description | Inputs | Expected |
|---------|-------------|--------|----------|
| TC-001 | Standard emergency with valid proof | IB-03, TIER-STANDARD, EMERGENCY, CRITICAL, $2500 total | Cap = $333 (annual $4k × 10% ÷ 4 × 75%), Responsibility = $333, Subsidy = $2167 |
| TC-002 | Routine visit with valid proof | IB-05, TIER-STANDARD, OUTPATIENT, ROUTINE, $800 total | Cap = $2187 (annual $87.5k × 10% ÷ 4), Responsibility = $800, Subsidy = $0 |
| TC-003 | Low-income critical patient | IB-01, TIER-CRITICAL, EMERGENCY, CRITICAL, $5000 total | Cap = $18 (annual $750k × 5% ÷ 4 × 75%), Responsibility = $18, Subsidy = $4982 |
| TC-004 | No proof provided | No eligibility_proof | Cap = total, Responsibility = total, Subsidy = 0, Tier = TIER-UNVERIFIED |

### 10.2 Edge Case Tests

| Test ID | Description | Inputs | Expected |
|---------|-------------|--------|----------|
| TC-010 | Proof expired | proof_valid_to = past date | TIER-UNVERIFIED, no cap |
| TC-011 | Proof revoked | revocation_status = REVOKED | TIER-UNVERIFIED, no cap |
| TC-012 | Eligibility not verified | eligibility_status = NOT_VERIFIED | TIER-UNVERIFIED, no cap |
| TC-013 | Estimated total is $0 | estimated_total_cents = 0 | All values = 0 |
| TC-014 | Very high income | IB-12, TIER-MODERATE | Cap = $375k (annual $150M × 12% ÷ 4) |
| TC-015 | Household size adjustment | IB-03, HS-5 | Cap multiplied by 1.30 |
| TC-016 | URGENT (no override) | IB-03, TIER-STANDARD, EMERGENCY, URGENT | No urgency override applied |

### 10.3 Boundary Tests

| Test ID | Description | Inputs | Expected |
|---------|-------------|--------|----------|
| TC-020 | Estimated total < cap | IB-03, $500 total | Responsibility = $500 (full, below cap) |
| TC-021 | Estimated total = cap | IB-03, cap = $1000, total = $1000 | Responsibility = $1000 |
| TC-022 | Estimated total > cap | IB-03, $5000 total, cap = $1000 | Responsibility = $1000, Subsidy = $4000 |

---

## 11. Integration Points

```
                    ┌─────────────────┐
  F-04 Encounter ──►│                 │
                    │  Affordability  │──────► Audit Ledger (F-06)
  F-01 Urgency ────►│     Engine      │
                    │    (F-02)       │──────► Subsidy Orchestrator (F-03)
  Eligibility ─────►│                 │
  Proof             └─────────────────┘
```

| Upstream | Data Provided | Protocol |
|----------|--------------|----------|
| F-04 Gateway | encounter_id, estimated_total_cents, encounter_class | gRPC / REST |
| F-01 Classifier | urgency_label | gRPC / REST |
| Verification Service | eligibility_proof (reduced attributes) | gRPC / REST |

| Downstream | Data Provided | Protocol |
|-----------|--------------|----------|
| Audit Ledger | Full calculation trace event | Async (event bus) |
| Subsidy Orchestrator | Subsidy amount to process | gRPC / REST |

---

## 12. Configuration

All configuration should be externalized and version-controlled:

```yaml
affordability_engine:
  income_brackets:
    IB-01: { min: 0, max: 1500000, midpoint: 750000 }
    IB-02: { min: 1500001, max: 3000000, midpoint: 2250000 }
    # ... (full table from §4.2)

  tier_multipliers:
    TIER-CRITICAL: 0.05
    TIER-LOW: 0.08
    TIER-STANDARD: 0.10
    TIER-MODERATE: 0.12
    TIER-UNVERIFIED: 1.00

  household_factors:
    HS-1: 0.70
    HS-2: 0.85
    HS-3: 1.00
    HS-4: 1.15
    HS-5: 1.30

  urgency_overrides:
    CRITICAL:
      multiplier: 0.75
      description: "25% additional protection for critical encounters"

  encounter_frequency_divisor: 4

  confidence_mapping:
    VERY_HIGH: HIGH
    HIGH: HIGH
    MODERATE: MODERATE
    LOW: LOW
```

---

*This document defines the complete implementation specification for the F-02 Affordability Engine. All changes must be version-controlled and reviewed by both engineering and compliance.*
