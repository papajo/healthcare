# Urgency Classifier (F-01) Prompt Engineering Strategy

**Project:** Crisis-Cost Orchestrator  
**Feature:** F-01 Real-Time Urgency Classifier  
**Upstream Contract:** `provider-api-f04-request.schema.json`  
**Status:** Draft v1.0

---

## 1. Purpose

This document defines the prompt engineering strategy for the **Urgency Classifier (F-01)**. The classifier consumes de-identified encounter data from **Provider API (F-04)** and assigns one of three urgency labels:

- **CRITICAL**
- **URGENT**
- **ROUTINE**

The strategy is optimized for:

- **patient safety** — especially avoiding under-triage of high-risk encounters
- **latency-aware inference** — suitable for the project target of `<150ms p99`
- **clinical grounding** — using only supplied encounter evidence from F-04
- **data minimization** — no unnecessary free-text expansion or inferred PHI
- **auditability** — concise evidence trace for why a label was assigned

> **Safety principle:** When evidence is borderline between two classes, the prompt should bias toward the **higher urgency** class rather than risk under-triage.

---

## 2. Goal

### 2.1 Primary objective
Classify an encounter into an urgency level based on real-time clinical signals received from the Provider API, with special emphasis on recognizing encounters that are potentially life-threatening or time-sensitive.

### 2.2 Operational goal
The model must answer the question:

> “Based only on the supplied intake data, how urgently should this encounter be treated?”

It must **not** answer:

- what diagnosis the patient has
- what treatment should be performed
- what billing code should be assigned
- what prognosis the patient will have

### 2.3 Intended output
At minimum, the classifier should return:

```json
{
  "urgency_label": "CRITICAL | URGENT | ROUTINE",
  "confidence": 0.0,
  "triggered_evidence": ["..."],
  "rationale_summary": "short explanation grounded only in supplied fields"
}
```

For production use, `triggered_evidence` should be short, deterministic, and audit-friendly (for example: `"HYPOXIA: spo2_percent=86"`, `"FLAG: STROKE_ALERT"`).

---

## 3. Input Analysis

The F-04 schema contains many fields, but the prompt should prioritize a **clinical-core subset** for urgency classification.

### 3.1 Primary high-signal inputs

#### A. Presenting problem
From `clinical_context.presenting_problem`:
- `chief_complaint_code`
- `chief_complaint_text` (optional, secondary only)
- `symptom_onset_hours`

**Prompt use:**
- Treat `chief_complaint_code` as the primary presenting-problem anchor.
- Use `chief_complaint_text` only to disambiguate the code when necessary.
- Use `symptom_onset_hours` to increase urgency for sudden-onset or recent high-risk complaints.

**Examples of high-risk complaint families:**
- chest pain
- shortness of breath
- stroke-like symptoms
- syncope
- active bleeding
- altered mental status
- pregnancy-related acute complaint

### 3.2 Vitals
From `clinical_context.vitals`:
- `heart_rate_bpm`
- `respiratory_rate_bpm`
- `spo2_percent`
- `temperature_c`
- `systolic_bp_mmhg`
- `diastolic_bp_mmhg`
- optional: `pain_score_0_10`, `gcs_total`, `blood_glucose_mg_dl`

**Prompt use:**
Vitals should be the strongest numerical evidence source. The prompt should force the model to evaluate:

1. **airway / breathing risk**
   - low oxygen saturation
   - markedly abnormal respiratory rate
2. **circulatory instability**
   - hypotension
   - severe tachycardia or bradycardia
3. **neurologic risk**
   - low GCS
   - altered mental status flags plus abnormal vitals
4. **metabolic instability**
   - markedly abnormal glucose when provided
5. **fever/systemic concern**
   - fever plus tachycardia/hypotension or sepsis-related flags

### 3.3 Critical lab results
From `clinical_context.critical_lab_values` and `clinical_context.critical_lab_results`:
- `lactate_mmol_l`
- `troponin_ng_ml`
- structured `critical_lab_results[*]`
  - `lab_code`
  - `result_value`
  - `unit`
  - `critical_flag`
  - `abnormal_flag`

**Prompt use:**
- Prefer structured `critical_lab_results` when present.
- Treat sender-provided `critical_flag=true` and `abnormal_flag in {CRITICAL_LOW, CRITICAL_HIGH}` as strong urgency evidence.
- Use lab values as **supporting risk evidence**, not as a diagnosis engine.
- The model should say “critical lab abnormality consistent with high urgency” rather than infer a disease.

### 3.4 High-alert medication context
From `clinical_context.high_alert_medication_context`:
- `ANTICOAGULANT`
- `INSULIN`
- `OPIOID`
- `CHEMOTHERAPY`
- `SEDATIVE`
- `ANESTHETIC`
- `DIURETIC`
- `ANTIBIOTIC`

**Prompt use:**
These are **risk modifiers**, not standalone urgency determinants.

Examples:
- `ANTICOAGULANT` + active bleeding or trauma concern => escalation
- `INSULIN` + abnormal glucose or altered mental status => escalation
- `OPIOID` or `SEDATIVE` + low respiratory rate or low SpO2 => escalation
- `CHEMOTHERAPY` + fever => escalation

### 3.5 Clinical flags
From `clinical_context.clinical_flags`:
- `CHEST_PAIN`
- `SHORTNESS_OF_BREATH`
- `STROKE_ALERT`
- `SEPSIS_ALERT`
- `TRAUMA_ALERT`
- `SUICIDAL_IDEATION`
- `PREGNANCY_RELATED`
- `ALTERED_MENTAL_STATUS`
- `SYNCOPE`
- `ACTIVE_BLEEDING`
- `FEVER`
- `HYPOTENSION`
- `HYPOXIA`
- `TACHYCARDIA`
- `BRADYCARDIA`

**Prompt use:**
These should be treated as pre-normalized triage clues from the source system and heavily weighted, especially when they align with abnormal vitals.

### 3.6 Demographics and encounter context
From `patient` and `encounter`:
- `age_bracket`
- `sex_at_birth`
- `pregnancy_status`
- `encounter_class`
- `arrival_mode`
- `acuity_level`

**Prompt use:**
Demographics are **modifiers only**.

Use them to contextualize risk, for example:
- `0-17` and `85+` may justify more conservative escalation when vitals are borderline
- `pregnancy_status=PREGNANT` increases urgency for concerning symptoms or bleeding
- `arrival_mode=EMS_AIR` or `EMS_GROUND` can be supporting context, but not a sole reason for `CRITICAL`
- `acuity_level` can be used as corroborating evidence if present, not as the only decision basis

### 3.7 Inputs that should not dominate the prompt
These fields should be excluded or strongly de-emphasized for F-01:
- `insurance_status`
- `patient_financial_context.*`
- `language_preference`
- `zip_code`
- downstream billing fields unless specifically validated for time-consistent triage use

**Reason:** They can introduce bias or leakage without improving true clinical urgency detection.

---

## 4. Prompt Architecture

The Urgency Classifier should use a **layered prompt stack**:

1. **System prompt** — role, boundaries, safety rules
2. **Developer prompt** — label taxonomy, reasoning steps, output schema
3. **Few-shot examples** — canonical clinical exemplars
4. **Encounter payload** — minimized F-04-derived JSON for the current case

### 4.1 System prompt design

Recommended system framing:

> You are a clinical urgency classification assistant for emergency and urgent-care encounter intake. Your task is to assign an urgency label using only the structured encounter data provided. You must not invent diagnoses, patient history, or unsupported facts. You must reason conservatively and prioritize patient safety. When evidence supports multiple classes, choose the higher urgency class. Return only the requested structured output.

### 4.2 System-level guardrails

The system prompt should explicitly enforce all of the following:

1. **No diagnosis generation**
   - Do not name or infer diseases unless explicitly encoded in the input.
   - Prefer phrases like “high-risk presentation” or “unstable vital pattern.”

2. **No hallucinated history**
   - Do not assume chronic illnesses, medications, allergies, or prior admissions.

3. **Evidence-only reasoning**
   - Every label must be supported by input fields present in the payload.

4. **Urgency, not treatment**
   - The task is triage classification only, not treatment recommendation.

5. **Safety-first tie-breaking**
   - If borderline between `URGENT` and `CRITICAL`, escalate to `CRITICAL` when objective instability or source-system critical flags are present.

6. **Demographic fairness**
   - Demographics may modify risk interpretation but must never be the sole reason for class assignment.

### 4.3 Few-shot prompting strategy

Use a compact set of high-value exemplars rather than a large prompt library. The goal is to teach:

- what “unstable” looks like
- how complaint + vitals + flags interact
- when meds/labs escalate urgency
- what stable presentations look like
- how to avoid over-diagnosing

#### Recommended few-shot coverage
Include at least 6–10 exemplars spanning:

1. **CRITICAL — respiratory compromise**
   - complaint: shortness of breath
   - SpO2 very low / RR high
   - label: `CRITICAL`

2. **CRITICAL — neuro/alert activation**
   - flag: `STROKE_ALERT` or `ALTERED_MENTAL_STATUS`
   - GCS low or marked vital abnormality
   - label: `CRITICAL`

3. **CRITICAL — bleeding / shock pattern**
   - `ACTIVE_BLEEDING` or `TRAUMA_ALERT`
   - hypotension and tachycardia
   - label: `CRITICAL`

4. **URGENT — high-risk complaint but stable vitals**
   - chest pain with stable oxygen and blood pressure
   - label: `URGENT`

5. **URGENT — fever / chemo / sepsis concern without shock**
   - chemotherapy context + fever + tachycardia, but no hypotension/hypoxia
   - label: `URGENT`

6. **ROUTINE — stable low-risk encounter**
   - mild complaint, stable vitals, no critical flags/labs
   - label: `ROUTINE`

### 4.4 Few-shot exemplar format

Each example should include:

- a short structured input
- the label
- concise evidence bullets
- a short rationale

Example pattern:

```json
{
  "input": {
    "chief_complaint_code": "SHORTNESS_OF_BREATH",
    "vitals": { "spo2_percent": 86, "respiratory_rate_bpm": 30, "heart_rate_bpm": 126, "systolic_bp_mmhg": 98 },
    "clinical_flags": ["SHORTNESS_OF_BREATH", "HYPOXIA", "TACHYCARDIA"],
    "age_bracket": "65-74"
  },
  "output": {
    "urgency_label": "CRITICAL",
    "triggered_evidence": [
      "HYPOXIA: spo2_percent=86",
      "TACHYPNEA: respiratory_rate_bpm=30",
      "FLAG: SHORTNESS_OF_BREATH"
    ],
    "rationale_summary": "Severe oxygen abnormality with respiratory distress pattern indicates immediate high-risk presentation."
  }
}
```

### 4.5 Chain-of-Thought (CoT) requirements

The classifier should be prompted to reason in a fixed sequence **before** assigning a label:

1. identify the presenting complaint and source-system clinical flags
2. identify objective instability in vitals
3. identify critical or panic-range labs
4. identify whether high-alert medication context increases risk
5. apply demographic modifiers conservatively
6. choose the highest justified urgency class

**Important implementation note:**
- The model may use internal stepwise reasoning to improve accuracy.
- The system should **not** store or expose unrestricted free-form chain-of-thought in logs.
- Instead, require a **concise evidence trace** and a **short rationale summary** as the auditable output.

Recommended developer instruction:

> Think through the encounter in a stepwise manner, but output only: (1) urgency label, (2) confidence, (3) triggered evidence, and (4) a short rationale summary grounded in the supplied fields.

### 4.6 Prompt template blueprint

```text
[SYSTEM]
You are a clinical urgency classification assistant. Assign only CRITICAL, URGENT, or ROUTINE using the supplied structured encounter data. Do not invent diagnoses or history. Use conservative safety-first reasoning. If evidence supports multiple classes, choose the higher urgency. Output only valid JSON.

[DEVELOPER]
Decision process:
1. Review chief complaint and clinical flags.
2. Review vital sign instability.
3. Review critical labs.
4. Review whether high-alert medication context increases immediate risk.
5. Use age bracket and pregnancy status only as modifiers.
6. Select the highest justified urgency label.
7. Do not use insurance, financial, or language fields.
8. Do not infer diagnoses.

Label definitions:
- CRITICAL: immediate or near-immediate risk suggested by unstable vitals, critical flags, or critical lab pattern.
- URGENT: serious/time-sensitive presentation without clear immediate instability.
- ROUTINE: stable presentation with no high-risk instability pattern.

Return JSON schema:
{
  "urgency_label": "CRITICAL|URGENT|ROUTINE",
  "confidence": number,
  "triggered_evidence": [string],
  "rationale_summary": string
}

[FEW-SHOT EXAMPLES]
...compact exemplar set...

[USER INPUT]
...minimized F-04 encounter JSON...
```

---

## 5. Label Definitions

The label taxonomy must be explicit and clinically conservative.

### 5.1 CRITICAL
Assign **CRITICAL** when the encounter suggests **immediate or near-immediate threat** based on the supplied evidence.

Typical triggers:
- severe hypoxia
- marked respiratory distress pattern
- hypotension with signs of instability
- major bradycardia/tachycardia with concerning presentation
- low GCS or altered mental status with objective instability
- `STROKE_ALERT`, `SEPSIS_ALERT`, or `TRAUMA_ALERT` with corroborating evidence
- active bleeding with instability
- sender-marked critical labs that materially increase immediate concern
- high-alert medication context plus objective instability (for example opioid/sedative + respiratory depression)

**Rule of thumb:** If a reasonable triage workflow would prioritize immediate physician or resuscitation-level attention, assign `CRITICAL`.

### 5.2 URGENT
Assign **URGENT** when the encounter is serious, high-risk, or time-sensitive but does **not** show clear immediate instability.

Typical triggers:
- high-risk complaint with currently stable or mildly abnormal vitals
- chest pain without shock/hypoxia pattern
- syncope with recovery and stable vitals
- fever with risk modifiers but no shock pattern
- pregnancy-related acute complaint without instability
- critical concern flags without severe objective deterioration
- moderately abnormal vitals requiring expedited evaluation

**Rule of thumb:** If the patient needs prompt clinical evaluation the same visit, but the supplied evidence does not show immediate physiologic compromise, assign `URGENT`.

### 5.3 ROUTINE
Assign **ROUTINE** when the encounter appears stable and low-risk based on the available evidence.

Typical characteristics:
- stable vitals
- no critical clinical flags
- no critical labs
- no instability-amplifying medication context
- low-risk presenting problem
- no severe neurologic, respiratory, circulatory, or bleeding indicators

**Rule of thumb:** If the supplied data suggests a clinically stable presentation with no evidence of immediate or time-critical deterioration, assign `ROUTINE`.

### 5.4 Escalation rule for ambiguity
When evidence is incomplete but includes meaningful high-risk features:
- prefer `URGENT` over `ROUTINE`
- prefer `CRITICAL` over `URGENT` if objective instability or source critical flags are present

This rule exists to reduce false negatives for the highest-risk population.

---

## 6. Evaluation Framework

Because the main patient-safety failure is **under-triaging truly critical encounters**, evaluation must prioritize the `CRITICAL` class.

### 6.1 Golden Dataset strategy

Build a de-identified **Golden Dataset** composed of real or expertly simulated F-04 payloads.

#### Dataset composition
The dataset should include:
- true `CRITICAL` encounters with varied presentations
- near-miss `URGENT` cases that resemble critical presentations
- clearly stable `ROUTINE` cases
- edge cases with sparse or conflicting data
- stratification across:
  - age brackets
  - pregnancy status
  - facility type
  - encounter class
  - arrival mode
  - complaint families
  - medication-risk contexts

#### Labeling workflow
Use a three-layer annotation process:

1. **Primary clinical labeling**
   - ED physician, advanced practice clinician, or experienced triage nurse assigns the urgency gold label.

2. **Secondary review**
   - a second reviewer independently labels the case.

3. **Adjudication**
   - disagreements are resolved in review conference with documented rationale.

#### Role of medical billing/coding specialists
Billing/coding specialists should not be the sole arbiters of clinical urgency, but they are critical for:
- validating that structured inputs map correctly from EHR/source coding
- identifying code-pattern ambiguities in `chief_complaint_code`
- spotting prompt drift caused by misinterpreting coded intake semantics
- reviewing whether the model over-relies on downstream coding artifacts

### 6.2 Core metrics for CRITICAL

Track at minimum:

- **Recall (Sensitivity) for CRITICAL** — primary safety KPI
- **Precision for CRITICAL** — secondary operational KPI
- **False Negative Rate for CRITICAL**
- **Confusion matrix** across all three labels
- **Under-triage rate** (`gold=CRITICAL`, `pred!=CRITICAL`)
- **Over-triage rate** (`pred=CRITICAL`, `gold!=CRITICAL`)

### 6.3 Recommended thresholds

For go-live readiness, set explicit thresholds such as:

- `CRITICAL recall >= 0.98` preferred, `>= 0.95` minimum acceptable for pilot
- `CRITICAL precision >= 0.80` initially, then tighten with refinement
- `ROUTINE-to-CRITICAL false negative count` reviewed case-by-case

Recall should be prioritized over precision for the `CRITICAL` class.

### 6.4 Error slicing

Every evaluation run should slice results by:
- age bracket
- pregnancy status
- encounter class
- facility type
- arrival mode
- each major complaint family
- each major clinical flag
- presence/absence of high-alert medication context
- missing-data scenarios

This is necessary to detect under-triage bias and brittle prompt behavior.

### 6.5 Prompt regression suite

Maintain a fixed regression suite containing:
- canonical CRITICAL exemplars
- previously missed critical cases
- previously over-triaged routine cases
- sparse-data and contradictory-data cases

No prompt revision should ship unless it preserves or improves CRITICAL recall on this suite.

---

## 7. Iterative Refinement Loop

Prompt engineering for F-01 should operate as a structured feedback loop.

### 7.1 Refinement cycle

1. **Run batch evaluation** on the Golden Dataset.
2. **Collect failure cases**, especially:
   - missed CRITICAL cases
   - CRITICAL vs URGENT confusions
   - unstable-vitals cases misread as ROUTINE
3. **Review with medical billing/coding specialists** to determine whether the issue is:
   - source coding ambiguity
   - missing field normalization
   - prompt wording ambiguity
   - exemplar coverage gap
4. **Revise prompt assets** by updating:
   - system guardrails
   - label wording
   - exemplar mix
   - evidence extraction instructions
5. **Re-run regression suite** and compare deltas.
6. **Promote only if** CRITICAL recall is preserved or improved and no fairness slice regresses materially.

### 7.2 What specialists should review

Medical billing/coding specialists should provide targeted feedback on:
- whether `chief_complaint_code` groupings align to actual intake semantics
- whether the prompt misreads diagnosis-oriented codes as confirmed diagnoses
- whether a complaint code should be treated as symptom-based versus condition-based
- whether structured lab and medication fields are being interpreted consistently
- whether clinically important context is being lost in normalization

### 7.3 Change log for prompt versions

Each prompt revision should record:
- prompt version ID
- changed instruction text
- changed exemplars
- motivation for change
- metrics before/after
- affected slices
- sign-off by clinical reviewer and coding reviewer

### 7.4 Human-in-the-loop escalation

If repeated review finds persistent ambiguity in a subgroup of encounters, the system should support one or more of:
- conservative fallback to higher urgency
- routing to manual review
- requiring additional upstream normalization
- splitting the prompt into sub-prompts by encounter type

---

## 8. Recommended Production Output Contract

To keep the system auditable and safe, the model output should be small and structured.

```json
{
  "urgency_label": "CRITICAL",
  "confidence": 0.94,
  "triggered_evidence": [
    "FLAG: STROKE_ALERT",
    "NEURO: gcs_total=11",
    "VITAL: systolic_bp_mmhg=88"
  ],
  "rationale_summary": "High-risk neurologic presentation with objective instability supports critical urgency."
}
```

### Output rules
- `triggered_evidence` should cite only present fields
- `rationale_summary` should be one sentence
- no diagnosis text unless explicitly present in the input
- no treatment recommendation text
- no free-form speculation

---

## 9. Implementation Recommendations

1. **Minimize payload before prompting**
   - Pass only the F-04 fields relevant to urgency classification.

2. **Prefer coded fields over free text**
   - Use `chief_complaint_text` only for disambiguation.

3. **Normalize obvious synonyms upstream**
   - complaint families, lab abnormality flags, and alert codes should be standardized before inference.

4. **Keep exemplars short and patterned**
   - teach the decision boundary, not a full chart narrative.

5. **Do not expose unrestricted CoT**
   - store evidence trace and rationale summary instead.

6. **Bias toward safety in prompt wording**
   - false negatives on `CRITICAL` are more harmful than moderate over-triage.

---

## 10. Summary

The best prompt strategy for **Urgency Classifier (F-01)** is a **few-shot, safety-first, evidence-grounded classifier prompt** that:

- anchors on coded presenting problem, vitals, critical labs, high-alert meds, and source clinical flags
- uses demographics only as conservative modifiers
- forces stepwise reasoning before label assignment
- blocks diagnosis hallucination and unsupported inference
- optimizes for **very high recall on the `CRITICAL` class**
- improves iteratively through Golden Dataset evaluation and specialist review

This approach fits the Crisis-Cost Orchestrator’s architecture: it is auditable, bounded, clinically conservative, and suitable for refinement under real provider feedback.
