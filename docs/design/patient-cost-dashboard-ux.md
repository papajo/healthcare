# Patient Cost Dashboard (F-01) UX Architecture

**Project:** Crisis-Cost Orchestrator  
**Artifact:** UX architecture for the patient-facing cost dashboard  
**Status:** Draft v1.0  
**Target surface:** Mobile-first patient dashboard within the Patient App (F-05), presenting outputs from the F-01 urgency classifier, F-02 affordability engine, F-03 subsidy orchestrator, and F-04 Provider API workflow.

---

## 1. Purpose

The Patient Cost Dashboard is the primary patient touchpoint for a high-stress moment: the period immediately after an encounter has been ingested from a provider system and the platform has calculated both:

1. the **urgency classification** for the episode of care, and  
2. the **estimated patient financial responsibility** after affordability protections and cost-cap logic are applied.

The UX goal is not merely to show numbers. It is to help a patient understand:

- **How urgent their care is**
- **What they may owe**
- **What protections were applied**
- **What they need to do next**
- **How to correct or verify their eligibility status if the result looks wrong**

This dashboard must reduce medical financial anxiety without making promises the system cannot technically support.

---

## 2. Technical Grounding and System Constraints

This UX architecture is grounded in the current project artifacts:

- `provider-api-f04-request.schema.json`
- `schemas/provider-api-f04-request.proto`
- `schemas/eligibility-proof.schema.json`
- `schemas/eligibility-proof-audit-event.schema.json`
- `docs/security/patient-income-proof-protocol.md`
- `docs/security/retention-schedule.md`
- `docs/architecture/encounter-flow.mmd`

### 2.1 System reality the UX must respect

1. **The provider system triggers the flow** via F-04 intake. The patient dashboard is downstream of that event, not the source of truth for encounter creation.
2. **The dashboard should use `patient_pseudo_id` and encounter/result references**, not direct identity fields. The provider payload explicitly excludes name, MRN, DOB, and street address.
3. **Eligibility is proof-based**, not raw-document-based. The system stores signed, reduced eligibility proofs and must not expose raw pay stubs, benefits letters, tax files, or ZIP5 by default.
4. **Protected affordability attributes may be field-level encrypted**, including normalized eligibility status and minimized geography proxies. The UI must assume some proof details are intentionally hidden.
5. **The current documented Provider API defines the intake request, not a full patient-facing response schema.** Therefore, the dashboard should be designed against a derived “result view model” produced by the gateway/economic engine rather than assuming undocumented backend fields.
6. **Language preference exists** in the F-04 request (`language_preference`) and should drive localization and reading level where available.
7. **Auditability matters.** Presentation, disputes, verification, and status changes should produce ledger-friendly events rather than free-form undocumented workflows.

### 2.2 UX implication of those constraints

- Show **clear, human-readable summaries** of urgency and cost.
- Show **explanations of protections applied**, not sensitive raw evidence.
- Offer **structured dispute and reverification paths** instead of “upload anything here” by default.
- Avoid displaying hidden system internals as if they were patient-facing truth.
- Use explicit labels like **Estimated**, **Verified**, **Pending review**, **Expired**, and **Needs action**.

---

## 3. User Personas

### 3.1 Persona A: The Price-Blind Patient

**Profile**
- Adult patient seeking emergency or urgent care
- Historically receives bills long after care
- Low familiarity with insurance, CPT/ICD codes, or charity-care rules
- Primary need: “Tell me plainly what this might cost me.”

**Emotional state**
- Confused
- Skeptical of medical billing
- Vulnerable to abandoning follow-up care if cost is unclear

**UX needs**
- A single clear estimate at the top
- Plain-language explanation of why the estimate looks the way it does
- Reassurance that affordability protections were checked
- Minimal jargon

### 3.2 Persona B: The Anxious Caregiver

**Profile**
- Family member managing care for a parent, spouse, or child
- May not be the clinically treated person but is coordinating logistics
- Needs quick understanding and next steps

**Emotional state**
- High stress
- Multitasking
- Wants certainty and escalation options

**UX needs**
- Scannable urgency/result summary
- Fast access to next steps and support
- Clear status if eligibility is already verified vs still pending
- Dispute/review path that is obvious and non-threatening

### 3.3 Persona C: The Fixed-Income / Uninsured Patient

**Profile**
- Uninsured, self-pay, Medicaid-qualified, or financially fragile
- Most sensitive to catastrophic out-of-pocket estimates
- May use an older device and may have limited digital literacy

**Emotional state**
- Fear of unaffordable bills
- Concern about being denied care or support

**UX needs**
- Very clear affordability tier and cost-cap communication
- Prominent “You may qualify / You are protected” messaging when applicable
- Mobile-first simplicity
- Ability to verify or refresh eligibility with minimal steps

### 3.4 Persona D: The Distrustful Verifier

**Profile**
- Patient who doubts that the estimate is fair or current
- May have recently changed insurance, employment, household status, or benefit eligibility

**Emotional state**
- Defensive
- Wants proof and correction options

**UX needs**
- Transparent explanation of what inputs affected the estimate
- Explicit “Why am I seeing this?” section
- Easy dispute and reverification workflow
- Timestamp and status freshness indicators

---

## 4. User Journey Map

This journey begins when the **Provider API (F-04) trigger** occurs.

### 4.1 End-to-end journey

| Phase | System Event | Patient Experience | UX Goal | Risks to Manage |
|---|---|---|---|---|
| 1. Encounter ingestion | Provider EHR sends `ProviderEncounterIntakeRequest` | Patient may be waiting, in treatment, or post-discharge | Keep patient unaware of backend complexity | Avoid implying the dashboard is instant if processing is still pending |
| 2. Urgency classification | Urgency engine evaluates clinical context and returns urgency result | Patient expects clarity on seriousness and what it means for cost protection | Present urgency as understandable, not as raw model jargon | Avoid exposing sensitive raw vitals/labs unnecessarily |
| 3. Proof verification | Affordability engine verifies signed eligibility proof | Patient wants reassurance protections were checked | Show status: verified, pending, expired, or needs review | Avoid showing raw financial evidence or hidden encrypted fields |
| 4. Cost-cap application | Gateway applies affordability tier + billing context + protection rules | Patient wants a bottom-line estimate | Show estimated responsibility and cap/protection summary | Avoid overpromising final bill certainty |
| 5. Result presentation | Dashboard receives result view model | Patient reads urgency, estimate, and next steps | Reduce anxiety, increase action confidence | Avoid clutter, jargon, or dead-end states |
| 6. Follow-up / challenge | Patient verifies status, disputes estimate, or asks for help | Patient regains agency if result looks wrong | Offer structured escalation paths | Avoid making the correction path feel punitive |

### 4.2 Patient-facing state flow

1. **Processing state**
   - Triggered after F-04 intake is accepted (`request_id` acknowledged).
   - Dashboard shows: “We’re preparing your care cost estimate.”
   - Optional sub-statuses:
     - Reviewing care urgency
     - Checking affordability protections
     - Building your estimate

2. **Result ready state**
   - Dashboard shows the primary summary:
     - urgency result
     - estimated patient cost
     - affordability/protection summary
     - next-step actions

3. **Verification needed state**
   - Used when eligibility proof is missing, expired, revoked, or needs manual review.
   - Dashboard still shows the best available estimate but clearly labels confidence/risk.

4. **Dispute/review submitted state**
   - Patient sees confirmation, case number, expected turnaround, and interim estimate policy.

5. **Updated result state**
   - A superseding proof or corrected encounter/billing status updates the dashboard.
   - Previous estimate is visually marked as superseded.

### 4.3 Journey details tied to contracts

The journey may reference these F-04 request facts as inputs to decisioning or explanation:

- `encounter.encounter_id`
- `encounter.encounter_class`
- `encounter.encounter_status`
- `clinical_context.presenting_problem.chief_complaint_code`
- `clinical_context.clinical_flags`
- `billing_context.diagnoses[]`
- `billing_context.procedures[]`
- `patient.insurance_status`
- `patient_financial_context.insurance_coverage_status`
- `patient_financial_context.financial_assistance_status`
- `language_preference`

The dashboard should **not** display these raw fields verbatim unless translated into patient language.

---

## 5. Information Architecture (IA)

The IA should prioritize the patient’s main questions in this order:

1. **Am I safe / how urgent is this?**
2. **What is my estimated cost?**
3. **What protections were applied?**
4. **How certain is this estimate?**
5. **What should I do next?**
6. **How can I correct or verify this?**

### 5.1 Primary information blocks

| Priority | IA Block | Purpose | Source / Derivation | Patient wording guidance |
|---|---|---|---|---|
| 1 | Urgency Summary | Shows the care urgency outcome | Derived from F-01 urgency result + clinical context | “Your care was classified as Emergency/Urgent/Routine for cost protection purposes” |
| 2 | Estimated Cost | Shows estimated patient responsibility | Derived after cost-cap logic | “Estimated amount you may owe” |
| 3 | Affordability Protection | Explains affordability tier / support status | Derived from signed eligibility proof + affordability engine | “Financial protections applied” |
| 4 | Cost Cap Applied | Makes the protection concrete | Gateway cost-cap computation | “Your responsibility was limited by program rules” |
| 5 | Estimate Confidence / Status | Shows verified vs pending vs provisional | Proof validity, revocation, manual review flags | “Verified estimate” / “Temporary estimate” |
| 6 | Next Steps | Tells patient what to do | Workflow state | “What you can do now” |
| 7 | Help / Review | Lets patient challenge or verify | Eligibility proof lifecycle + support workflows | “Verify eligibility” / “Request review” |
| 8 | Result Metadata | Provides trust markers | request_id, timestamps, proof validity window, estimate timestamp | “Updated 8 minutes ago” |

### 5.2 Key data points to display

#### A. Urgency
- **Urgency Level** (primary label)
- Plain-language explanation of what it means for care-cost protections
- Optional note: “This does not replace your clinician’s medical advice”

#### B. Cost
- **Estimated patient responsibility** (largest numeric value)
- **Estimated total care amount** or “provider billed amount considered” only if available and not misleading
- **Subsidy/protection amount applied**
- **Cost cap applied**
- Estimate confidence/status: verified, provisional, pending documentation, expired eligibility

#### C. Affordability / eligibility
- **Affordability Tier** (patient-friendly label)
- **Eligibility status** (ELIGIBLE / CONDITIONALLY ELIGIBLE / NOT VERIFIED / EXPIRED / REVOKED translated into friendly wording)
- Verification freshness window (`proof_valid_to` translated to “Valid through”)
- If manual review is required, say so clearly

#### D. Next steps
- Pay later / wait for final bill
- Verify eligibility
- Request review/dispute
- Contact support / financial counselor
- Return to encounter list / care summary

### 5.3 Information the dashboard should not expose directly

Per the proof protocol and schema design, the patient dashboard should not expose raw or overly technical artifacts by default:

- Raw financial documents
- ZIP5
- Decrypted protected attributes beyond the normalized patient-facing status needed for explanation
- Raw proof hashes, signatures, ciphertext, IV, tags
- Internal issuer IDs unless needed in an advanced support view
- Raw ICD/CPT/HCPCS codes in the primary view
- Raw vitals/labs as explanation copy unless clinically and legally approved

### 5.4 Proposed patient result view model

Because no formal patient response contract exists yet, the dashboard should consume a derived result object with fields like:

```json
{
  "result_id": "uuid",
  "request_id": "uuid",
  "encounter_id": "string",
  "patient_pseudo_id": "uuid",
  "status": "PROCESSING | READY | NEEDS_VERIFICATION | UNDER_REVIEW | SUPERSEDED",
  "urgency": {
    "level": "EMERGENCY | URGENT | ROUTINE",
    "label": "Emergency care",
    "explanation": "Your visit qualified for emergency-level protection."
  },
  "estimate": {
    "patient_responsibility_cents": 45000,
    "currency": "USD",
    "cap_applied": true,
    "cap_rule_label": "10% annual affordability cap",
    "protection_amount_cents": 210000,
    "estimate_status": "VERIFIED | PROVISIONAL"
  },
  "eligibility": {
    "status": "ELIGIBLE | CONDITIONALLY_ELIGIBLE | NOT_VERIFIED | EXPIRED | REVOKED",
    "affordability_tier": "TIER-LOW",
    "verification_assurance_level": "HIGH",
    "manual_review_required": false,
    "proof_valid_to": "2027-06-30T00:00:00Z"
  },
  "timestamps": {
    "evaluated_at": "2026-07-01T12:00:00Z",
    "last_updated_at": "2026-07-01T12:01:10Z"
  },
  "actions": [
    "VERIFY_ELIGIBILITY",
    "REQUEST_REVIEW",
    "CONTACT_SUPPORT"
  ]
}
```

---

## 6. Wireframe Specifications

The dashboard should be **mobile-first**, then scale to tablet and desktop. In stressful situations, a narrow, single-column layout is preferable on first load.

### 6.1 Overall page layout

#### Mobile layout
1. Header
2. Reassurance/status strip
3. Urgency badge card
4. Estimated cost hero card
5. Cost breakdown card
6. Affordability protection / eligibility card
7. Next steps card
8. Dispute / verify section
9. Help and support footer

#### Tablet/Desktop layout
- Left column: urgency + estimate + actions
- Right column: breakdown + protections + status metadata + help

### 6.2 Component inventory

#### A. Header

**Purpose**
Provide orientation without overloading.

**Contents**
- Title: `Your Care Cost Estimate`
- Encounter reference: short human-readable encounter/date label
- Last updated timestamp
- Language switcher if available

**Rules**
- Do not show direct identity or MRN in the visible header by default.
- Keep support/help access reachable from header or sticky footer.

#### B. Reassurance / status strip

**Purpose**
Answer: “Is this final? Is this verified?”

**Variants**
- Verified estimate
- Temporary estimate
- Eligibility check needed
- Review in progress
- Updated estimate available

**Example copy**
- `Verified protections applied`
- `Temporary estimate — verify eligibility to confirm savings`
- `We’re reviewing your information`

#### C. Urgency Badge card

**Purpose**
Explain urgency classification in patient language.

**Contents**
- Badge: Emergency / Urgent / Routine
- Short sentence explaining implication for protections
- Optional “Why this matters” disclosure

**Visual rules**
- Emergency: strong but not alarming color treatment
- Urgent: medium emphasis
- Routine: neutral emphasis
- Must meet accessibility contrast standards

**Example structure**
- Title: `Urgency level`
- Badge: `Emergency care`
- Body: `Your visit qualified for emergency-level protection based on the care information received from your provider.`

#### D. Estimated Cost hero card

**Purpose**
Show the most important financial number.

**Contents**
- Large currency amount: `Estimated amount you may owe`
- Secondary text: `after protections and cost caps`
- Optional supporting values:
  - cost cap applied
  - amount reduced by subsidy/protection

**Rules**
- This is the visual focal point of the page.
- Must clearly say **estimated** unless legally safe to say final.

#### E. Cost Breakdown card

**Purpose**
Make the estimate feel explainable.

**Contents**
- Estimated starting amount considered
- Protection / subsidy reduction
- Cost cap effect
- Current patient responsibility

**Presentation**
Use a simple stacked list or vertical math layout, for example:
- Starting estimate
- Protection applied
- Cap applied
- You may owe

**Rules**
- Avoid billing-code jargon in primary view.
- Offer a “View details” expansion for advanced users.

#### F. Affordability Protection card

**Purpose**
Translate proof-based decisioning into understandable status.

**Contents**
- Affordability tier label
- Eligibility status label
- Verification freshness (`Valid through ...`)
- Review note if manual review required

**Friendly label mapping**
- `ELIGIBLE` → `Verified for financial protection`
- `CONDITIONALLY_ELIGIBLE` → `Likely eligible — some protections applied`
- `NOT_VERIFIED` → `Verification needed`
- `EXPIRED` → `Your financial verification has expired`
- `REVOKED` → `Your previous verification is no longer active`

**Rules**
- Do not expose encrypted proof internals.
- If support needs full proof metadata, that belongs behind a restricted staff workflow, not the patient UI.

#### G. Next Steps card

**Purpose**
Move the patient from fear to action.

**Contents**
- Primary action button
- Secondary actions
- Contextual steps based on status

**Action examples by state**
- Verified result:
  - `See estimate details`
  - `Get billing help`
- Verification needed:
  - `Verify eligibility`
  - `Continue with temporary estimate`
- Under review:
  - `Check review status`
  - `Contact support`

#### H. Dispute / Review section

**Purpose**
Provide agency when the result seems wrong.

**Contents**
- Link/button: `Request a review`
- Short explanation of when to use it
- Structured reasons:
  - insurance changed
  - household/benefits changed
  - estimate looks incorrect
  - care urgency seems misclassified

**Rules**
- Reason codes should be structured for auditability.
- Avoid free-form first as the only path; allow notes only as supplemental.

#### I. Help and Support footer

**Purpose**
Reduce abandonment in stressful cases.

**Contents**
- Financial counselor contact
- Support hours / response expectations
- Legal disclaimer about estimate vs final adjudication

### 6.3 Low-fidelity wireframe (mobile)

```text
--------------------------------------------------
[Your Care Cost Estimate]                [Help]
Encounter: Jul 1, 2026 • Updated 12:01 PM

[Verified protections applied]

[Urgency level]
[EMERGENCY CARE]
Your visit qualified for emergency-level protection.

[Estimated amount you may owe]
$450
After protections and cost caps

[Cost breakdown]
Starting estimate                    $2,550
Protection applied                  -$1,800
Cost cap adjustment                   -$300
-------------------------------------------
You may owe                           $450

[Financial protection status]
Verified for financial protection
Affordability tier: Lower-cost protection tier
Valid through Jun 30, 2027

[What you can do now]
[See estimate details]
[Request a review]
[Get billing help]

Need to verify your status or update your information?
[Verify eligibility]
--------------------------------------------------
```

### 6.4 Responsive behavior

- **320–480 px:** single column, sticky bottom action bar allowed
- **481–768 px:** single column with larger card spacing
- **769–1024 px:** two-column split
- **1025 px+:** desktop with right-rail metadata/help

---

## 7. Design Principles

### 7.1 Transparency

The dashboard should answer “why” without demanding that patients understand hospital finance.

**Design rules**
- Always label the result as estimated, verified, provisional, or under review.
- Show what protections were applied.
- Show when the estimate was last updated.
- Distinguish clearly between:
  - care urgency result
  - financial protection result
  - next operational step

**Do not**
- Hide uncertainty
- Pretend a provisional estimate is final
- Bury the review/dispute path

### 7.2 Empathy

This dashboard is used during or shortly after acute care.

**Design rules**
- Use calming, plain language.
- Prioritize reassurance before detail.
- Keep the first screen actionable and short.
- Avoid punitive wording such as “denied” unless legally required.

**Preferred tone**
- `We checked for financial protections`
- `You can request a review if something looks wrong`
- `We’ll let you know if we need anything else`

### 7.3 Clarity

Patients should not have to infer which number matters.

**Design rules**
- One dominant financial number
- One dominant urgency label
- One clear primary next step
- Progressive disclosure for advanced details

### 7.4 Trust through restraint

The best trust signal is often what the system intentionally does **not** show.

**Design rules**
- Do not expose raw proof internals or sensitive evidence.
- Do not expose ZIP5 or direct identifiers.
- Use normalized status labels derived from the proof model.

---

## 8. Interaction Design

### 8.1 Navigation model

The Patient Cost Dashboard should support simple, shallow navigation:

1. **Dashboard home** (summary)
2. **Estimate details**
3. **Eligibility verification / update**
4. **Request review / dispute**
5. **Help / support**

Patients should never have to traverse a deep menu tree in a crisis scenario.

### 8.2 Primary interactions

#### Interaction A: View estimate details
- Tap `See estimate details`
- Open an expanded panel or secondary screen
- Show:
  - estimate status
  - protections applied
  - timestamp
  - simplified explanation of calculation logic

#### Interaction B: Verify eligibility
- Tap `Verify eligibility`
- Open a guided flow explaining:
  - why verification matters
  - what type of reduced proof the system uses
  - that raw evidence is handled in a separate verifier boundary
- Show status options:
  - verified
  - pending
  - expired
  - needs review

**Important UX/security note**
The flow should not imply that raw evidence is permanently stored in the app. The copy should align with the proof protocol: evidence is verified externally, reduced to signed attributes, and sensitive fields are protected.

#### Interaction C: Request review / dispute
- Tap `Request a review`
- Present structured reason options:
  - `My insurance or coverage changed`
  - `My income or support eligibility changed`
  - `This estimate looks too high`
  - `The urgency classification looks wrong`
  - `I need help understanding this result`
- Optional text box for extra context
- Confirmation screen returns:
  - case/reference number
  - expected response window
  - current estimate handling policy

#### Interaction D: View status freshness
- Tap status or “Last updated” label
- Show detail sheet:
  - estimate generated at
  - verification valid through
  - whether a newer proof superseded an old one

### 8.3 Dispute and verification states

#### State 1: Eligibility not verified
**UI behavior**
- Show banner: `Verification needed`
- Cost estimate can still display if a provisional estimate exists
- Primary CTA becomes `Verify eligibility`

#### State 2: Eligibility expired
**UI behavior**
- Show banner: `Your verification has expired`
- Keep prior estimate visible but dimmed or labeled as outdated
- CTA: `Refresh verification`

#### State 3: Eligibility revoked or superseded
**UI behavior**
- Show status as inactive
- Explain that a previous verification is no longer active
- If a new proof exists, point to updated estimate

#### State 4: Review in progress
**UI behavior**
- Show progress strip
- Preserve prior estimate with caveat label
- Offer support contact, not repeated form submission

### 8.4 Accessibility interaction requirements

- All primary cards and buttons reachable by keyboard/switch navigation
- High-contrast urgency badges
- No meaning conveyed by color alone
- Large tap targets for stressed/mobile users
- Screen-reader-friendly labels for money amounts and status badges
- Plain-language reading level target: approximately grade 6–8 for summary copy

---

## 9. Content and Messaging Guidance

### 9.1 Plain-language replacements

| Technical/System concept | Patient-friendly label |
|---|---|
| Urgency classification | Care urgency level |
| Affordability tier | Financial protection level |
| Eligibility proof verified | Your financial protection was verified |
| Cost cap applied | Your amount was limited by protection rules |
| Manual review required | We need to review your information |
| Revoked / superseded proof | A previous verification is no longer active |

### 9.2 Example reassurance copy

- `We checked whether financial protections apply to your care.`
- `This is your current estimate based on information received from your provider and your verified protection status.`
- `If anything has changed, you can request a review.`

### 9.3 Example uncertainty copy

- `This estimate may change if your provider updates the care record or your protection status changes.`
- `Your current estimate is temporary until eligibility is verified.`

---

## 10. Audit, Privacy, and Security UX Requirements

### 10.1 Privacy-preserving display rules

The dashboard must follow the proof protocol and retention model:

- No raw financial evidence display
- No ZIP5 display by default
- No direct identity in shared or support-facing screenshots where avoidable
- No decrypted protected-attribute payloads exposed in client logs
- No proof internals stored in browser analytics or crash reporting

### 10.2 UX events that should be auditable

The following patient interactions should map to auditable product events:

- estimate viewed
- estimate details expanded
- verify eligibility started
- review/dispute submitted
- support contact initiated
- updated estimate acknowledged

These events should use minimized identifiers aligned with ledger practices.

### 10.3 Retention-aware UX behavior

- If proof validity expires, the UI should stop presenting the estimate as fully verified.
- If a result is superseded, previous estimates should be marked historical or hidden from default view.
- Download/export views should be privacy-reviewed so they do not include prohibited fields.

---

## 11. Open Questions for Downstream Design / Engineering

1. What is the canonical patient-facing urgency enum for F-01 output? The current artifacts describe urgency classification conceptually, but a formal response contract is still needed.
2. Will the patient result payload include both estimated total cost and patient responsibility, or only patient responsibility?
3. What exact support workflow handles disputes: case creation, secure messaging, or routed task queue?
4. Which eligibility statuses may be shown directly to patients versus summarized into friendlier labels?
5. Will there be a patient-visible history of estimate revisions per encounter?
6. What SLA should the UI promise for manual review turnaround?

---

## 12. Recommended Next Artifacts

1. **UI state model** for dashboard statuses and transitions
2. **Patient-facing result API schema** for the derived dashboard view model
3. **Low-fidelity wireframes** in visual form for mobile and desktop
4. **Content design sheet** for status labels, reassurance copy, and dispute wording
5. **Accessibility checklist** for high-stress medical-financial interfaces

---

## 13. Summary

The Patient Cost Dashboard should behave like a calm interpreter of a complex backend workflow.

It should:
- translate urgency classification into understandable reassurance,
- present one clear estimated patient cost,
- explain financial protections without exposing sensitive proof internals,
- give the patient a clear next step,
- and preserve trust by making verification and dispute paths obvious.

The most important UX outcome is that a patient can open the dashboard and quickly answer:

**“How serious is this, what might I owe, what protected me, and what can I do if this looks wrong?”**
