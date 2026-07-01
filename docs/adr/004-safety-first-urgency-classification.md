# ADR-004: Safety-First Urgency Classification Design

**Status:** Accepted  
**Date:** 2026-07-01  
**Deciders:** Engineering, Clinical Advisory  
**Relates to:** F-01 Urgency Classifier

---

## Context

The Urgency Classifier determines whether a patient encounter is CRITICAL, URGENT, or ROUTINE. This classification directly affects:
- **Patient safety** — under-triage of critical patients is life-threatening
- **Financial impact** — CRITICAL encounters get 25% additional affordability protection
- **Provider liability** — misclassification could expose providers to risk
- **Regulatory compliance** — CMS and state regulators monitor triage accuracy

The primary failure mode we must avoid is **under-triage** (classifying a truly critical patient as URGENT or ROUTINE).

## Decision

**Design the Urgency Classifier with explicit safety-first principles:**
1. Bias toward higher urgency when evidence is ambiguous
2. Optimize for CRITICAL recall (≥ 0.98 target) over precision
3. Use deterministic, auditable evidence-based reasoning
4. Never allow the classifier to diagnose or recommend treatment
5. Maintain a regression suite of previously missed critical cases

## Options Considered

### Option 1: Safety-First Design (Chosen)

**Pros:**
- Protects patients from under-triage
- Conservative approach aligns with clinical practice
- Auditable decision path
- Clear escalation rules

**Cons:**
- May over-triage some encounters (higher false positives)
- Requires careful calibration to avoid alert fatigue
- Higher operational cost from additional triage reviews

### Option 2: Balanced Precision/Recall

**Pros:**
- More balanced classification
- Fewer false positives

**Cons:**
- Higher risk of missing critical patients
- Harder to justify clinically
- Regulatory scrutiny

### Option 3: High-Precision Only

**Pros:**
- Fewer false positives
- Lower operational cost

**Cons:**
- Unacceptable risk of missing critical patients
- Clinically irresponsible
- Regulatory non-compliance

## Safety Principles

### Principle 1: When in Doubt, Escalate

```
IF evidence is borderline between URGENT and CRITICAL:
    AND objective instability OR source critical flags present:
        CHOOSE CRITICAL
```

### Principle 2: Recall Over Precision

| Metric | Target | Minimum Acceptable |
|--------|--------|-------------------|
| CRITICAL Recall | ≥ 0.98 | ≥ 0.95 |
| CRITICAL Precision | ≥ 0.80 | ≥ 0.70 |
| CRITICAL False Negative Rate | ≤ 0.02 | ≤ 0.05 |

### Principle 3: Evidence-Based Only

- Every classification must be supported by input fields
- No diagnosis inference
- No hallucinated patient history
- No treatment recommendations

### Principle 4: Demographics as Modifiers Only

- Age brackets 0-17 and 85+ may justify escalation when borderline
- Pregnancy status increases urgency for concerning symptoms
- Demographics must never be the sole reason for classification

## Consequences

1. **Over-triage rate** will be higher than balanced approaches
2. **Operational cost** increases due to additional CRITICAL case reviews
3. **Patient safety** is prioritized over operational efficiency
4. **Regression suite** must be maintained and expanded continuously
5. **Prompt versioning** tracks all changes with before/after metrics
6. **Clinical review** required for any prompt changes affecting CRITICAL recall

## Evaluation Framework

### Golden Dataset Composition
- True CRITICAL encounters with varied presentations
- Near-miss URGENT cases resembling critical presentations
- Clearly stable ROUTINE cases
- Edge cases with sparse or conflicting data

### Slicing Requirements
Every evaluation run must slice results by:
- Age bracket
- Pregnancy status
- Encounter class
- Facility type
- Arrival mode
- Each major complaint family
- Each major clinical flag
- Presence/absence of high-alert medication context

## Monitoring

| Metric | Alert Threshold |
|--------|----------------|
| CRITICAL recall drops below 0.95 | Any occurrence |
| CRITICAL false negative | Every occurrence (case-by-case review) |
| Over-triage rate exceeds 30% | Weekly review |
| Prompt regression detected | Immediate review |

---

*This ADR documents the safety-first design principle for the F-01 Urgency Classifier in the Crisis-Cost Orchestrator.*
