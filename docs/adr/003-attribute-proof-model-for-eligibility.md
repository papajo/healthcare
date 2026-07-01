# ADR-003: Attribute-Proof Model for Eligibility Verification

**Status:** Accepted  
**Date:** 2026-07-01  
**Deciders:** Security/Compliance, Engineering  
**Relates to:** F-02 Affordability Engine, Patient Income Proof Protocol

---

## Context

The Affordability Engine needs patient income data to calculate affordability caps. However, storing raw financial evidence (pay stubs, tax returns, bank statements) in the core platform creates significant risks:

1. **HIPAA compliance burden** — raw financial data linked to patient identity requires extensive controls
2. **Breach impact** — exposure of raw financial data is catastrophic
3. **Data minimization** — regulatory principle of collecting only what's needed
4. **Retention complexity** — raw evidence requires careful lifecycle management

## Decision

**Use an attribute-proof model: verify raw evidence externally, issue a reduced signed proof containing only minimum attributes, and never store raw evidence in the core platform.**

## How It Works

```
Patient/Source → Verification Provider (isolated boundary)
                        │
                        ├── Validates raw evidence
                        ├── Reduces to attributes:
                        │     - income_bracket_code (not raw income)
                        │     - affordability_tier
                        │     - eligibility_status_normalized
                        │     - service_area_code (not ZIP5)
                        ├── Signs the proof
                        └── Returns signed proof to core platform
                                │
                                ▼
                    Core Platform stores only:
                    - proof_id
                    - patient_pseudo_id
                    - income_bracket_code
                    - affordability_tier
                    - eligibility_status_normalized
                    - signature_metadata
                    - proof_hash
                    - validity window
                    
                    Core Platform NEVER stores:
                    - tax returns
                    - pay stubs
                    - bank statements
                    - SSN/TIN
                    - raw income amounts
                    - full ZIP code
```

## Options Considered

### Option 1: Attribute-Proof Model (Chosen)

**Pros:**
- Minimal data in core platform
- Reduced breach impact
- Simplified compliance
- Clear separation of concerns
- Raw evidence lifecycle managed by verification provider

**Cons:**
- Requires trusted verification providers
- Adds verification step to patient onboarding
- Less flexibility for downstream analytics

### Option 2: Raw Evidence Storage (Rejected)

**Pros:**
- Full data available for any use case
- No verification provider dependency

**Cons:**
- Massive compliance burden
- Catastrophic breach impact
- Complex retention management
- Violates data minimization principle

### Option 3: Hybrid (Partial Storage) (Rejected)

**Pros:**
- Some flexibility
- Reduced compliance vs. full storage

**Cons:**
- Still significant compliance burden
- Unclear where to draw the line
- Complexity without clear benefit

## Consequences

1. **Verification providers** must be trusted and audited
2. **Raw evidence** is deleted within 24 hours of proof issuance
3. **Core platform** operates only on reduced attributes
4. **Analytics** use aggregated bracket data, not individual income
5. **Patient onboarding** requires verification step before affordability protection
6. **Proof refresh** required periodically (validity windows)

## Compliance Impact

- HIPAA: Minimum necessary principle satisfied
- GLBA: Financial data minimization achieved
- FCRA: Consumer report data reduced to attributes
- IRS/FTI: Tax information never enters core platform
- State privacy laws: SDOH proxies minimized (ZIP → service area code)

---

*This ADR documents the decision to use an attribute-proof model for eligibility verification in the Crisis-Cost Orchestrator.*
