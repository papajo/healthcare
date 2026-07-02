# OKF.md — Crisis-Cost Orchestrator

```markdown
# Open Knowledge Format (OKF)

## Crisis-Cost Orchestrator — HIPAA-Compliant Healthcare Cost Protection Platform

This document defines the Open Knowledge Format (OKF) schema for the Crisis-Cost Orchestrator platform, a HIPAA-compliant system that eliminates medical bankruptcy by intelligently classifying care urgency and affordability.

---

## 1. Overview

### Purpose

The OKF standardizes knowledge representation for:

| # | Component | Description |
|---|---|---|
| 1 | **Urgency Classification** | Emergency vs. non-emergency care triage |
| 2 | **Affordability Calculation** | Patient financial burden assessment |
| 3 | **Subsidy Orchestration** | Coverage gap identification and assistance routing |
| 4 | **Audit Trail** | Immutable clinical and financial decision logs |
| 5 | **CDS Integration** | Clinical decision support recommendations |

### Principles

| Principle | Description |
|---|---|
| **HIPAA Compliant** | PHI protection via encryption, access controls, and audit trails |
| **FHIR-Native** | Built on HL7 FHIR R4 standards for interoperability |
| **Audit-First** | Every decision recorded, verified, and traceable |
| **Cost-Conscious** | Real-time affordability modeling at point of care |

---

## 2. Core Entity Definitions

### 2.1 Encounter Classification

```json
{
  "encounterClassification": {
    "encounterId": "uuid",
    "encounteredAt": "2026-06-15T10:30:00Z",
    "patientId": "patient-pseudo-id",
    "urgencyLevel": "EMERGENCY|URGENT|SEMI-URGENT|NON-URGENT",
    "urgencyScore": 0.95,
    "classificationReason": "string",
    "clinicalIndicators": [
      {
        "code": "LOINC-or-SNOMED",
        "display": "Chest pain with cardiac risk factors",
        "severity": "HIGH|MODERATE|LOW"
      }
    ],
    "recommendedCareLevel": "ICU|INPATIENT|OBSERVATION|OUTPATIENT|URGENT_CARE",
    "estimatedCost": {
      "totalChargedAmount": 150000,
      "estimatedInsuranceResponsibility": 120000,
      "estimatedPatientResponsibility": 30000,
      "currency": "USD"
    }
  }
}
```

| Field | Type | Description |
|---|---|---|
| `encounterId` | string (UUID) | Unique identifier for the encounter |
| `encounteredAt` | ISO 8601 | Timestamp of patient arrival |
| `patientId` | string | Pseudonymized patient identifier |
| `urgencyLevel` | enum | `EMERGENCY`, `URGENT`, `SEMI-URGENT`, `NON-URGENT` |
| `urgencyScore` | float (0.0–1.0) | Machine-learned urgency probability |
| `classificationReason` | string | Human-readable rationale |
| `clinicalIndicators` | array | Structured clinical data (LOINC/SNOMED codes) |
| `recommendedCareLevel` | enum | `ICU`, `INPATIENT`, `OBSERVATION`, `OUTPATIENT`, `URGENT_CARE` |
| `estimatedCost` | object | Forecasted total, insurance, and patient obligations |

---

### 2.2 Affordability Assessment

```json
{
  "affordabilityAssessment": {
    "assessmentId": "uuid",
    "patientId": "patient-pseudo-id",
    "encounterId": "encounter-id",
    "assessedAt": "2026-06-15T10:35:00Z",
    "patientFinancialProfile": {
      "householdIncome": 45000,
      "householdSize": 4,
      "federalPovertyLine": 28100,
      "incomeToPovertyRatio": 1.6,
      "isBelowFPL": false,
      "medicalDebtExposure": 25000
    },
    "affordabilityScore": 0.35,
    "affordabilityCategory": "HIGH_RISK|MODERATE_RISK|LOW_RISK",
    "maxAffordableOutOfPocket": 3500,
    "riskOfBankruptcy": true,
    "recommendedSubsidyAmount": 15000,
    "subsidyEligibility": [
      {
        "programName": "State Charity Care",
        "eligibilityPercentage": 0.95,
        "maximumAssistance": 20000
      },
      {
        "programName": "Hospital Financial Assistance",
        "eligibilityPercentage": 0.85,
        "maximumAssistance": 15000
      }
    ]
  }
}
```

| Field | Type | Description |
|---|---|---|
| `assessmentId` | string (UUID) | Unique identifier for the assessment |
| `patientId` | string | Pseudonymized patient identifier |
| `encounterId` | string | Linked encounter identifier |
| `assessedAt` | ISO 8601 | Assessment timestamp |
| `patientFinancialProfile` | object | Household financial context |
| `affordabilityScore` | float (0.0–1.0) | Composite affordability metric |
| `affordabilityCategory` | enum | `HIGH_RISK`, `MODERATE_RISK`, `LOW_RISK` |
| `maxAffordableOutOfPocket` | number (USD) | Maximum patient can pay without hardship |
| `riskOfBankruptcy` | boolean | Probability of medical bankruptcy |
| `recommendedSubsidyAmount` | number (USD) | Suggested subsidy level |
| `subsidyEligibility` | array | Matched subsidy programs with eligibility scores |

---

### 2.3 Subsidy Orchestration

```json
{
  "subsidyProgram": {
    "subsidyId": "uuid",
    "patientId": "patient-pseudo-id",
    "encounterId": "encounter-id",
    "createdAt": "2026-06-15T10:40:00Z",
    "status": "CREATED|SUBMITTED|APPROVED|SETTLED|CANCELLED",
    "subsidyItems": [
      {
        "itemId": "uuid",
        "serviceCategory": "EMERGENCY|SURGERY|IMAGING|PHARMACY|LAB",
        "chargedAmount": 45000,
        "insuranceResponsibility": 30000,
        "patientResponsibility": 15000,
        "requestedSubsidyAmount": 10000,
        "approvedSubsidyAmount": 9500,
        "adjustmentReason": "Needs-based reduction",
        "status": "APPROVED"
      }
    ],
    "totalRequestedSubsidy": 25000,
    "totalApprovedSubsidy": 23500,
    "subsidySource": "HOSPITAL_FINANCIAL_ASSISTANCE|STATE_CHARITY_CARE|NPO_GRANT|INSURANCE_CREDIT",
    "settlementDetails": {
      "settlementDate": "2026-06-20T00:00:00Z",
      "amountSettled": 23500,
      "settlementMethod": "BILL_ADJUSTMENT|CREDIT|GRANT",
      "patientOutOfPocketAfterSubsidy": 5500
    }
  }
}
```

| Field | Type | Description |
|---|---|---|
| `subsidyId` | string (UUID) | Unique subsidy program identifier |
| `patientId` | string | Pseudonymized patient identifier |
| `encounterId` | string | Linked encounter identifier |
| `createdAt` | ISO 8601 | Subsidy creation timestamp |
| `status` | enum | `CREATED`, `SUBMITTED`, `APPROVED`, `SETTLED`, `CANCELLED` |
| `subsidyItems` | array | Individual service-level subsidy entries |
| `totalRequestedSubsidy` | number (USD) | Aggregate requested amount |
| `totalApprovedSubsidy` | number (USD) | Approved after adjustments |
| `subsidySource` | enum | Funding source of subsidy |
| `settlementDetails` | object | Final settlement accounting |

---

### 2.4 Claim Submission & Settlement

```json
{
  "claim": {
    "claimId": "uuid",
    "patientId": "patient-pseudo-id",
    "encounterId": "encounter-id",
    "claimStatus": "DRAFT|SUBMITTED|UNDER_REVIEW|APPROVED|PARTIAL|DENIED|SETTLED|VOIDED",
    "createdAt": "2026-06-15T11:00:00Z",
    "submittedAt": "2026-06-15T11:05:00Z",
    "serviceDate": "2026-06-15T00:00:00Z",
    "payerId": "BCBS|AETNA|UNR",
    "totalChargedCents": 15000000,
    "lineItems": [
      {
        "lineItemId": "uuid",
        "serviceCode": "99213",
        "serviceDescription": "Office visit, established patient",
        "chargedAmount": 250,
        "allowedAmount": 200,
        "insurancePayment": 160,
        "patientResponsibility": 40,
        "subsidy": 0,
        "status": "APPROVED"
      }
    ],
    "totalInsuranceResponsibility": 12000000,
    "totalPatientResponsibility": 2500000,
    "totalSubsidyApplied": 500000,
    "denialReasons": [],
    "settlementStatus": "SETTLED",
    "settlementDate": "2026-06-20T00:00:00Z",
    "daysToSettlement": 5
  }
}
```

| Field | Type | Description |
|---|---|---|
| `claimId` | string (UUID) | Unique claim identifier |
| `patientId` | string | Pseudonymized patient identifier |
| `encounterId` | string | Linked encounter identifier |
| `claimStatus` | enum | Full lifecycle status enum |
| `payerId` | string | Insurance payer identifier |
| `totalChargedCents` | integer | Charges in cents (always) |
| `lineItems` | array | Per-service claim lines with payment breakdown |
| `totalInsuranceResponsibility` | number (USD) | Total insurer payment |
| `totalPatientResponsibility` | number (USD) | Remaining patient obligation |
| `totalSubsidyApplied` | number (USD) | Subsidies applied to obligation |
| `denialReasons` | array | Structured denial codes and explanations |
| `settlementDate` | ISO 8601 | Final settlement timestamp |
| `daysToSettlement` | integer | SLA compliance metric |

---

### 2.5 Audit Event

```json
{
  "auditEvent": {
    "eventId": "uuid",
    "eventType": "ENCOUNTER_RECEIVED|URGENCY_CLASSIFIED|AFFORDABILITY_CALCULATED|SUBSIDY_CREATED|SUBSIDY_SETTLED|SUBSIDY_CANCELLED|CLAIM_CREATED|CLAIM_SUBMITTED|CLAIM_SETTLED|CLAIM_VOIDED",
    "eventTimestamp": "2026-06-15T10:30:00Z",
    "actor": {
      "actorType": "SYSTEM|CLINICIAN|PATIENT|ADMIN|AUDITOR",
      "actorId": "user-id-or-service-id",
      "actorName": "Dr. Jane Smith"
    },
    "entity": {
      "entityType": "ENCOUNTER|PATIENT|CLAIM|SUBSIDY|OBSERVATION",
      "entityId": "resource-id",
      "entityDisplay": "Encounter #12345"
    },
    "action": "READ|CREATE|UPDATE|DELETE|CLASSIFY|CALCULATE|APPROVE|SETTLE",
    "outcome": "SUCCESS|FAILURE",
    "resultingState": {
      "outcomeCode": "0",
      "message": "Classification completed successfully"
    },
    "correlationId": "trace-id-for-multi-step-workflows",
    "sourceIpAddress": "192.168.1.100",
    "userAgent": "Chrome/120.0",
    "dataAccessedCount": 5,
    "sensitiveDataAccessed": ["FINANCIAL_INFO"],
    "consentStatus": "VALID|EXPIRED|REVOKED",
    "encryptionStatus": "ENCRYPTED_AT_REST|ENCRYPTED_IN_TRANSIT",
    "chainVerificationStatus": "VALID|COMPROMISED"
  }
}
```

| Field | Type | Description |
|---|---|---|
| `eventId` | string (UUID) | Unique audit event identifier |
| `eventType` | enum | Event type covering full platform lifecycle |
| `eventTimestamp` | ISO 8601 | Precise event timestamp |
| `actor` | object | Who performed the action |
| `entity` | object | What was acted upon |
| `action` | enum | CRUD + domain-specific actions |
| `outcome` | enum | Success or failure of the action |
| `resultingState` | object | Resulting resource state |
| `correlationId` | string | Trace ID linking related events |
| `dataAccessedCount` | integer | Number of database records touched |
| `sensitiveDataAccessed` | array | Categories of PHI touched |
| `consentStatus` | enum | Validated against patient consent |
| `encryptionStatus` | enum | Encryption verification |
| `chainVerificationStatus` | enum | Cryptographic chain integrity |

---

### 2.6 CDS (Clinical Decision Support) Hook Response

```json
{
  "cdsCard": {
    "uuid": "uuid",
    "summary": "Drug-Allergy Interaction: Penicillin",
    "indicator": "WARNING|INFO|CRITICAL",
    "detail": "Patient has documented penicillin allergy. Amoxicillin is contraindicated.",
    "source": {
      "label": "Crisis-Cost Orchestrator CDS",
      "url": "https://example.com/cds",
      "icon": "https://example.com/logo.png"
    },
    "suggestions": [
      {
        "label": "Use alternative antibiotic",
        "uuid": "uuid",
        "isRecommended": true,
        "actions": [
          {
            "label": "Select cephalosporin",
            "description": "Lower cross-reactivity risk",
            "type": "create",
            "uuid": "uuid"
          }
        ]
      }
    ],
    "links": [
      {
        "label": "Drug-Allergy Interaction Reference",
        "url": "https://fda.gov/drugs",
        "type": "absolute"
      }
    ]
  }
}
```

| Field | Type | Description |
|---|---|---|
| `uuid` | string | Unique CDS card identifier |
| `summary` | string | One-line alert title |
| `indicator` | enum | `WARNING`, `INFO`, `CRITICAL` |
| `detail` | string | Expanded clinical explanation |
| `source` | object | CDS source metadata |
| `suggestions` | array | Actionable recommendations |
| `links` | array | Reference links for clinical review |

---

## 3. Data Flow Workflows

### 3.1 Emergency Department Triage Workflow

```
Patient Arrival
    ↓
[Encounter Created]
    ↓
[Urgency Classification]
    ├─ Extract vital signs, chief complaint
    ├─ Compare against urgency rules
    └─ Assign urgency level (EMERGENCY, URGENT, etc.)
    ↓
[Affordability Assessment]
    ├─ Income verification
    ├─ Insurance eligibility check
    └─ Calculate financial risk
    ↓
[Subsidy Program Matching]
    └─ Identify state/hospital programs
    ↓
[CDS Hook: patient-view]
    └─ Return clinical decision support cards
    ↓
[Audit Log Created]
    └─ All decisions recorded
```

**Flow characteristics:**

| Stage | Primary Inputs | Primary Outputs | Key Dependencies |
|---|---|---|---|
| Encounter Created | Patient arrival, registration data | Encounter resource (FHIR) | FHIR Patient resource |
| Urgency Classification | Encounter data, vital signs, labs, patient history | Urgency level + score + recommendation | ML model, clinical rules |
| Affordability Assessment | Financial data, insurance status, income | Affordability score + category + eligibility | CREST/HHS income data |
| Subsidy Program Matching | Affordability results, patient eligibility | Approved subsidy programs | State programs, hospital FAF |
| CDS Hook (patient-view) | Diagnosis, medications, allergies | Decision support cards | CDS Hooks v2.0 |
| Audit Log Created | All preceding stages | Immutable audit event chain | Audit service |

---

### 3.2 Claim Processing Workflow

```
Service Delivery
    ↓
[Claim Created]
    ├─ Capture line items
    ├─ Identify service codes
    └─ Calculate initial patient responsibility
    ↓
[Claim Submitted to Payer]
    └─ Audit event recorded
    ↓
[Claim Under Review]
    └─ Payer processes, may request additional info
    ↓
[Claim Decision Received]
    ├─ Approved / Partial / Denied
    └─ Insurance responsibility determined
    ↓
[Subsidy Orchestration]
    └─ Apply subsidy to patient responsibility gap
    ↓
[Claim Settled]
    └─ Final financial accounting
    ↓
[Audit Trail Verified]
    └─ Chain integrity confirmed
```

**Flow characteristics:**

| Stage | Primary Inputs | Primary Outputs | Key Dependencies |
|---|---|---|---|
| Claim Created | Encounter, service delivery data | FHIR Claim resource | Encounter, ChargeMaster |
| Claim Submitted | FHIR Claim | Submission receipt | Insurance payer API |
| Claim Under Review | Submitted claim | Status tracking | Payer review queue |
| Claim Decision | Review outcome | Payment status | Payer adjudication engine |
| Subsidy Orchestration | Patient responsibility gap | Subsidy items + approved amount | Subsidy program rules |
| Claim Settled | Final amounts | Payment + patient OOP | Billing + ledger systems |
| Audit Trail Verified | Event chain | Cryptographic verification | Blockchain/chain of custody |

---

## 4. Validation Rules

### 4.1 Urgency Classification Criteria

| Urgency Level | Conditions | Maximum Wait Time |
|---|---|---|
| **EMERGENCY** | Vital signs unstable OR life-threatening condition | Immediate |
| **URGENT** | Requires evaluation within 1 hour | 60 minutes |
| **SEMI-URGENT** | Evaluation within 2–4 hours | 240 minutes |
| **NON-URGENT** | Can wait 4+ hours or refer to primary care | 240+ minutes |

**Urgency Classification Decision Tree:**

```
Vital Signs Check
  ├─ Systolic BP > 180 or < 90 → EMERGENCY
  ├─ Heart Rate > 120 or < 40 → EMERGENCY
  ├─ Respiratory Rate > 30 → EMERGENCY
  ├─ O2 Saturation < 88% → EMERGENCY
  ├─ Altered Mental Status → EMERGENCY
  ├─ Chief Complaint Analysis
  │   ├─ Pain 8–10 / Chest Pain → EMERGENCY
  │   ├─ Pain 6–7 / Fever > 103°F → URGENT
  │   ├─ Pain 6–7 / Localized Infection → URGENT
  │   ├─ Uncontrolled Chronic → URGENT
  │   ├─ Pain 4–5 / Stable Vitals → SEMI-URGENT
  │   └─ Wellness / Maintenance / Follow-up → NON-URGENT
  └─ Default → SEMI-URGENT
```

---

### 4.2 Affordability Risk Stratification

| Category | Income Criteria | Out-of-Pocket Criteria |
|---|---|---|
| **HIGH_RISK** | Income < 200% FPL OR OOP > 5% income | Yes |
| **MODERATE_RISK** | Income 200–400% FPL OR OOP 3–5% income | Yes |
| **LOW_RISK** | Income > 400% FPL AND OOP < 3% income | No |

**Affordability Score Computation:**

```
affordabilityScore = (1 - OOP / Income) × clinicalWeight
                  + (1 - subRate) × insuranceWeight
                  + (bankruptcyScore) × riskWeight

affordabilityCategory = 
  HIGH_RISK  if affordabilityScore > 0.6
  MODERATE_RISK if 0.3 < affordabilityScore ≤ 0.6
  LOW_RISK  if affordabilityScore ≤ 0.3
```

Where:
- `OOP` = estimated patient out-of-pocket
- `Income` = household annual income
- `subRate` = patient responsibility / charged amount
- `clinicalWeight`, `insuranceWeight`, `riskWeight` = configurable weights (sum to 1.0)

---

### 4.3 Audit Chain Integrity

**Required validation rules for every audit event:**

| Rule | Description | Failure Action |
|---|---|---|
| **Cryptographic Signature** | Every event must be signed with actor's private key | Event rejected, no chain continuity |
| **Hash Chain Link** | Event hash must match previous event hash (link) | Chain marked COMPROMISED |
| **Monotonic Timestamps** | Timestamps must be strictly increasing | Event timestamp rejected |
| **Actor Permission** | Actor must have valid permission for action | Action rejected with ACCESS_DENIED |
| **Consent Validation** | Patient consent must be VALID at time of action | Action rejected with CONSENT_DENIED |
| **Correlation ID Continuity** | Related events must share correlation IDs | Linked events flagged for review |
| **Data Minimization** | Only required fields accessed for the action | Excess access flagged |
| **Encryption Verification** | Sensitive data must be encrypted at rest and transit | Event marked COMPROMISED |

---

## 5. Privacy & Security

### 5.1 PHI Protection

| Layer | Technology | Standard | Scope |
|---|---|---|---|
| **At Rest** | AES-256 encryption | NIST SP 800-38A | PostgreSQL database, backups, logs |
| **In Transit** | TLS 1.3 | RFC 8446 | All API endpoints, inter-service communication |
| **In Memory** | Encrypted secrets, Ephemeral storage | FIPS 140-2 | API keys, temporary data in runtime |
| **Access Control** | RBAC + Attribute-Based Access | HIPAA §164.312(b) | Role-based permissions with minimum necessary |
| **Audit Trail** | Immutable event chain | HIPAA §164.314(b) | All PHI access logged and cryptographically verified |

---

### 5.2 Data Minimization

| Principle | Implementation |
|---|---|
| **Pseudonymization** | Patient ID replaced with system-generated pseudonym |
| **Field Subsetting** | Role-based field selection (clinician sees clinical, patient sees financial) |
| **No Direct Identifiers in Analytics** | Aggregation masks individual identifiers |
| **Automated Purge** | Temporary data purged after session expiry (default: 24 hours) |
| **Need-to-Know Basis** | Least privilege access at every workflow stage |

---

### 5.3 Consent Management

| Feature | Implementation |
|---|---|
| **Explicit Consent Required** | Mandatory opt-in before financial data sharing |
| **Granular Consent** | Patient controls per data category (clinical, financial, pharmacy) |
| **Easy Revocation** | One-click consent withdrawal propagates system-wide |
| **Audit Tracked** | Consent events logged in audit trail with timestamps |
| **Blocking Actions** | No action proceeds if consent not VALID for required data |

---

## 6. Interoperability Standards

### 6.1 FHIR R4 (HL7 FHIR 4.0.1) Integration

| FHIR Resource | Role in Platform |
|---|---|
| **Patient** | Demographics, identifiers, demographics, managed care |
| **Encounter** | Visit data, care settings, class, status |
| **Observation** | Vital signs, lab results, clinical measurements |
| **Condition** | Patient diagnoses, chronic conditions |
| **MedicationRequest** | Prescribed medications, dosages, allergies |
| **AllergyIntolerance** | Patient allergy history |
| **Claim** | Insurance claim submission and status |
| **Coverage** | Insurance plan details, eligibility |
| **Organization** | Provider, hospital, payer entity information |
| **DiagnosticReport** | Lab reports, imaging results |

**FHIR Standard Profile:**

```
Resource Profile: Crisis-Cost Encounter Classification Bundle
├── FHIRBundle (R4)
│   ├── Bundle.entry
│   │   ├── Patient
│   │   ├── Encounter
│   │   ├── Observation (vital signs)
│   │   ├── DiagnosticReport (labs)
│   │   ├── Condition (diagnoses)
│   │   ├── MedicationRequest (prescriptions)
│   │   ├── Coverage (insurance)
│   │   ├── Observation (affordability composite)
│   │   └── CDSHookResponse (decision support)
│   └── FHIRBundle.type = "collection"
│   └── FHIRBundle.entryType = "composite"
```

---

### 6.2 CDS Hooks v2.0 Support

| Hook Type | Use Case in Platform | Trigger Source |
|---|---|---|
| `patient-view` | Display clinical alerts and decision support | Patient dashboard |
| `order-select` | Recommend order modifications | Order entry |
| `order-sign` | Confirm clinical decisions | Provider signature |
| `medication-prescribe` | Suggest medication alternatives | EHR medication module |

**CDS Card Structure (v2.0):**

```json
{
  "card": {
    "uuid": "string",
    "version": "number",
    "summary": "string",
    "summaryMarkdown": "string",
    "indicator": "WARNING|INFO|WARNING|CRITICAL",
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "detail": "string",
    "detailMarkdown": "string",
    "source": {
      "label": "string",
      "url": "string",
      "icon": {
        "url": "string",
        "type": "image/svg+xml",
        "width": "number",
        "height": "number"
      }
    },
    "language": "https://www.iets.io/languages/en-US",
    "sections": [
      {
        "label": "string",
        "detail": "string",
        "detailMarkdown": "string",
        "citations": [
          {
            "label": "string",
            "url": "string"
          }
        ],
        "summary": "string"
      }
    ],
    "suggestions": [
      {
        "label": "string",
        "id": "string",
        "isRecommended": "boolean",
        "actions": [
          {
            "id": "string",
            "type": "create|update|delete",
            "target": {
              "type": "resourceType",
              "profile": "url",
              "interaction": "string"
            },
            "selection": [
              {
                "field": "string",
                "description": "string",
                "options": [
                  {
                    "valueCoding": {
                      "system": "url",
                      "code": "code",
                      "display": "string"
                    },
                    "valueString": "string",
                    "valueBoolean": "boolean"
                  }
                ]
              }
            ]
          }
        ]
      }
    ],
    "linkText": "string",
    "links": [
      {
        "label": "string",
        "uri": "string",
        "resourceType": "string",
        "reference": "string",
        "type": "absolute|relative"
      }
    ],
    "qualityMeasures": [
      {
        "label": "string",
        "uri": "string",
        "type": "absolute"
      }
    ],
    "readResource": {
      "profile": "url",
      "id": "string",
      "reference": "string"
    },
    "triggerEvent": {
      "type": "string",
      "status": "string",
      "details": {
        "dateTime": "string",
        "target": {
          "resourceType": "string",
          "reference": "string"
        }
      }
    },
    "prefetch": {
      "style": "implicit|explicit",
      "resources": [
        {
          "profile": "url",
          "interaction": "read",
          "context": [
            {
              "reference": "string",
              "type": "absolute|relative",
              "seed": {
                "profile": "url",
                "search": "string"
              }
            }
          ]
        }
      ]
    },
    "routing": {
      "priority": {
        "label": "string",
        "priority": "number"
      }
    }
  }
}
```

---

### 6.3 Healthcare Coding Standards

| Standard | Code System | Domain | Use In |
|---|---|---|---|
| **ICD-10-CM** | `http://terminology.hl7.org/CodeSystem/icd-10` | Clinical diagnoses | Conditions, encounter classification |
| **ICD-10-PCS** | `http://terminology.hl7.org/CodeSystem/icd-10-procedure` | Procedures | Inpatient procedures |
| **CPT** | `http://www.ama-assn.org/go/cpt` | Professional services | Outpatient procedures |
| **HCPCS** | `http://www.cms.gov/Medicare/Medicare-Fee-for-Service-Payment/MPFS` | Supplies/equipment | Facility services |
| **LOINC** | `http://loinc.org` | Lab results, observations | Labs, vitals, composite measures |
| **SNOMED CT** | `http://snomed.info/sct` | Clinical concepts | Findings, reasons, body sites |
| **NDC** | `http://www.nlm.nih.gov/id/drug` | Medications | Prescribed and dispensed drugs |
| **SVC** | `http://terminology.hl7.org/CodeSystem/clinical-service` | Clinical services | CPT/HCC crosswalk |
| **v3-ActCode** | `http://terminology.hl7.org/CodeSystem/v3-ActCode` | Act type | Encounter class (EMEDU, AMP, etc.) |
| **v3-RoleCode** | `http://terminology.hl7.org/CodeSystem/v3-RoleCode` | Actor role | Provider, payer, pharmacy |

**LOINC Code Priority Mapping:**

| LOINC Category | Prefix | Example | Use |
|---|---|---|---|
| Vital signs | 8867-/7636- | Heart Rate | Urgency classification |
| Serum | 8857-/6600- | Troponin I | Cardiac risk assessment |
| Urine | 8867-/6600- | Creatinine | Renal function |
| CBC | 58410-2 | WBC count | Infection detection |
| Pain | 52800-2 | Pain score | Urgency stratification |
| Temperature | 8310-5 | Body temperature | Fever detection |
| Respiratory Rate | 9279-1 | Respiratory rate | Breathing status |
| O2 Saturation | 2160-0 | O2 saturation | Respiratory status |

---

## 7. Failure Scenarios & Recovery

### 7.1 Network Failure

| Scenario | Detection | Mitigation | Recovery |
|---|---|---|---|
| **Payer API unreachable** | Connection timeout after 3 retries | Queue claim locally with full metadata | Resume on reconnection, retry with backoff |
| **Subsidy API unreachable** | Connection timeout, partial data | Cache subsidy decisions locally | Requery on reconnection, reconcile delta |
| **Database connection failure** | Connection pool exhaustion | Fail open to audit-only mode | Fail open, allow processing, offline queue |
| **Interc-service communication** | gRPC/TCP timeout | Circuit breaker activated (Hystrix) | Automatic retry with exponential backoff |

**Retry Strategy:**

```
Attempt 1: Retry after 1s
Attempt 2: Retry after 5s
Attempt 3: Retry after 30s
→ If failed, move to local queue
→ Retry queue item every 60s up to 24h
→ If still failed, mark as PENDING_MANUAL and notify operator
```

---

### 7.2 Payment Authorization Failure

| Scenario | Response Action |
|---|---|
| **Insufficient funds** | Log decline reason (code + message), queue for manual review |
| **Provider not contracted** | Return contract status, notify clinical staff |
| **Duplicate submission** | Detect duplicate, reconcile, return match |
| **Policy violation** | Return specific policy rule violated |
| **Timing violation** | Claim outside eligible period, inform patient |

**Patient-Friendly Messages:**

```
if (declineReason === "insufficient_funds"):
    return "Your insurance has not yet covered this service. 
            We have queued your claim for a manual review 
            and are exploring subsidy options to help cover costs."

if (declineReason === "not_contracted"):
    return "This provider is not currently in our network. 
            Please verify your insurance coverage or consider 
            a network participant for future visits."

if (declineReason === "duplicate"):
    return "We received your claim earlier. If you believe 
            you submitted it twice, please contact our office 
            so we can resolve this."
```

---

### 7.3 Data Integrity Breach

**Detection Procedures:**

```
1. Continuous chain verification (every event)
2. Cryptographic signature validation on read
3. Anomaly detection (unexpected hash changes)
4. Access pattern monitoring (unusual query volumes)
5. Patient-reported discrepancies (verification mechanism)
```

**Incident Response:**

| Step | Action | Responsible Party | Timeframe |
|---|---|---|---|
| 1 | Halt all write operations | System (automatic) | < 60s |
| 2 | Alert security team | Security operations | < 5 min |
| 3 | Engage incident response | Incident response team | < 30 min |
| 4 | Contain breach (isolate affected systems) | Engineering | < 1 hour |
| 5 | Assess impact (which data, which patients) | Compliance / Security | < 24 hours |
| 6 | Notify affected patients (if required by law) | Legal / Patient communication | HIPAA 60 days |
| 7 | Report to HHS (if threshold met) | Legal / HIPAA | 60 days from discovery |
| 8 | Remediate and restore | Engineering / Security | ASAP |
| 9 | Document and audit | Compliance | 30 days post-remediation |

---

## 8. Metrics & Monitoring

### 8.1 Clinical Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| **Urgency Classification Accuracy** | Sensitivity ≥ 0.92, Specificity ≥ 0.88 | Compare against clinician-verified triage |
| **Urgency Classification Precision** | Precision ≥ 0.85 | TP / (TP + FP) on classified encounters |
| **Time-to-Classification** | < 10 minutes | Arrival timestamp → classification timestamp |
| **Time-to-Treatment Initiation** | < 30 minutes (EMERGENCY) | Classification → treatment starts |
| **CDS Card Acceptance Rate** | ≥ 75% of CRITICAL/WARNING followed | Recommendation → action tracked |
| **CDS Card Override Rate** | ≤ 10% of WARNING overridden | Recommendation → override tracked |
| **Care Level Accuracy** | ICU recommendation ↔ actual ICU admission ≥ 0.85 | Prospective vs. actual outcomes |

---

### 8.2 Financial Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| **Subsidy Utilization Rate** | ≥ 80% of eligible patients enrolled | Eligible count → enrolled count |
| **Average Subsidy Amount** | $5,000 – $25,000 per patient | Total subsidy / enrolled count |
| **Medical Bankruptcy Prevention Rate** | ≥ 50% reduction YoY | Pre/post platform self-reported surveys |
| **Median Patient OOP (EMERGENCY)** | ≤ $500 | Post-settlement patient out-of-pocket |
| **Median Patient OOP (HIGH_RISK)** | ≤ $2,000 | Post-subsidy patient out-of-pocket |
| **Claim Settlement Time** | < 20 days | Submission → settlement date |
| **Denial Rate (pre-platform)** | Track as baseline | Pre-integration vs. post-integration |
| **Financial Assistance Payout Ratio** | ≥ 70% requested → approved | Approved / requested subsidy ratio |
| **Coverage Gap Resolution** | ≥ 90% gaps resolved | Gaps identified → resolved |
| **Cost Avoidance (per Encounter)** | ≥ 15% reduction vs. standard care | Pre/post platform total cost |

---

### 8.3 Audit Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| **Event Audit Completeness** | ≥ 99.5% | Actioned events / total expected events |
| **Chain Integrity** | 100% (no compromised links) | Hash chain verification |
| **Signature Validity** | 100% of events signed | Cryptographic signature verification |
| **Monotonic Timestamp Compliance** | 100% | Timestamp sequence validation |
| **Consent Compliance** | 100% of data actions with valid consent | Consent status in audit trail |
| **Unauthorized Access Attempts** | ≤ 0 (target), log all | Access control engine |
| **Access Control Violations Detected** | 0 successful | RBAC enforcement logs |
| **Audit Log Retention** | 6 years (HIPAA required) | Log retention system |
| **Encryption Compliance (at rest)** | 100% of PHI records | Encryption monitoring hooks |
| **Encryption Compliance (in transit)** | 100% of API traffic | TLS connection verification |
| **Mean Time to Detect Breach** | < 4 hours | Detection system SLA |

---

## 9. Example JSON Payloads

### 9.1 Complete Patient Encounter

```json
{
  "encounter": {
    "id": "enc-20260615-001",
    "resourceType": "Encounter",
    "status": "finished",
    "class": {
      "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
      "code": "EMEDU",
      "display": "Emergency department"
    },
    "subject": {
      "reference": "Patient/patient-20260615-001"
    },
    "period": {
      "start": "2026-06-15T10:30:00Z",
      "end": "2026-06-15T12:45:00Z"
    }
  },
  "classification": {
    "urgencyLevel": "EMERGENCY",
    "urgencyScore": 0.92,
    "classificationReason": "Chest pain with ST elevation on EKG",
    "recommendedCareLevel": "ICU",
    "clinicalIndicators": [
      {
        "code": "2160-0:LOINC",
        "display": "Oxygen saturation",
        "severity": "HIGH",
        "value": 72
      },
      {
        "code": "85354-0:LOINC",
        "display": "ST elevation",
        "severity": "HIGH",
        "value": true
      },
      {
        "code": "72133-0:LOINC",
        "display": "Pain severity",
        "severity": "HIGH",
        "value": 8
      }
    ]
  },
  "affordability": {
    "affordabilityScore": 0.32,
    "affordabilityCategory": "HIGH_RISK",
    "maxAffordableOutOfPocket": 3200,
    "riskOfBankruptcy": true,
    "subsidyEligibility": [
      {
        "programName": "State Medicaid",
        "eligibilityPercentage": 0.98,
        "maximumAssistance": 20000
      },
      {
        "programName": "Hospital Financial Assistance",
        "eligibilityPercentage": 0.90,
        "maximumAssistance": 15000
      }
    ]
  },
  "subsidy": {
    "subsidyId": "sub-20260615-001",
    "status": "APPROVED",
    "subsidyItems": [
      {
        "itemId": "sub-item-001",
        "serviceCategory": "EMERGENCY",
        "chargedAmount": 85000,
        "insuranceResponsibility": 60000,
        "patientResponsibility": 25000,
        "requestedSubsidyAmount": 25000,
        "approvedSubsidyAmount": 23500,
        "adjustmentReason": "Maximum program cap",
        "status": "APPROVED"
      },
      {
        "itemId": "sub-item-002",
        "serviceCategory": "IMAGING",
        "chargedAmount": 12000,
        "insuranceResponsibility": 10000,
        "patientResponsibility": 2000,
        "requestedSubsidyAmount": 500,
        "approvedSubsidyAmount": 500,
        "adjustmentReason": null,
        "status": "APPROVED"
      }
    ],
    "totalRequestedSubsidy": 25500,
    "totalApprovedSubsidy": 24000,
    "settlementDetails": {
      "settlementDate": "2026-06-20T00:00:00Z",
      "settlementMethod": "BILL_ADJUSTMENT",
      "patientOutOfPocketAfterSubsidy": 5500
    }
  },
  "claim": {
    "claimId": "claim-20260615-001",
    "claimStatus": "SUBMITTED",
    "payerId": "AETNA",
    "totalChargedCents": 852000,
    "lineItems": [
      {
        "lineItemId": "line-001",
        "serviceCode": "99213",
        "serviceDescription": "Emergency service, established patient",
        "hcpcsCode": "99281",
        "chargeDescription": "Emergency department visit",
        "chargedAmount": 450,
        "allowedAmount": 380,
        "insurancePayment": 280,
        "patientResponsibility": 100,
        "subsidy": 0,
        "status": "UNDER_REVIEW"
      },
      {
        "lineItemId": "line-002",
        "serviceCode": "93000",
        "serviceDescription": "Chest cath lab",
        "hcpcsCode": "93451",
        "chargeDescription": "Catheterization",
        "chargedAmount": 15000,
        "allowedAmount": 12000,
        "insurancePayment": 9500,
        "patientResponsibility": 5000,
        "subsidy": 0,
        "status": "UNDER_REVIEW"
      },
      {
        "lineItemId": "line-003",
        "serviceCode": "8857-1:LOINC",
        "serviceDescription": "Troponin I",
        "hcpcsCode": "82293",
        "chargeDescription": "Cardiac marker panel",
        "chargedAmount": 250,
        "allowedAmount": 200,
        "insurancePayment": 180,
        "patientResponsibility": 20,
        "subsidy": 0,
        "status": "APPROVED"
      }
    ],
    "totalInsuranceResponsibility": 11780,
    "totalPatientResponsibility": 5520,
    "totalSubsidyApplied": 5200,
    "denialReasons": [],
    "settlementStatus": "SUBMITTED",
    "daysToSettlement": null
  },
  "cdsCards": [
    {
      "uuid": "cds-001",
      "summary": "Drug-Allergy Interaction: Penicillin",
      "indicator": "CRITICAL",
      "severity": "HIGH",
      "detail": "Patient has documented penicillin allergy. Amoxicillin is contraindicated.",
      "source": {
        "label": "Crisis-Cost Orchestrator CDS",
        "url": "https://ccos.healthcare/patients/20260615",
        "icon": {
          "url": "https://ccos.healthcare/assets/critical.svg",
          "type": "image/svg+xml"
        }
      },
      "language": "https://www.iets.io/languages/en-US",
      "sections": [
        {
          "label": "Allergy Alert",
          "detail": "Penicillin class drugs will harm the patient.",
          "detailMarkdown": "**⚠️ This patient has a penicillin allergy.**\n\nPeanilloylation causes severe hypersensitivity. Avoid all beta-lactams."
        }
      ],
      "suggestions": [
        {
          "label": "Alternative: Cephalexin",
          "id": "sug-001",
          "isRecommended": true,
          "actions": [
            {
              "id": "act-001",
              "type": "create",
              "target": {
                "type": "MedicationRequest",
                "profile": "http://hl7.org/fhir/StructureDefinition/3.0.0/MedicationRequest"
              },
              "selection": [
                {
                  "field": "medicationCodeableConcept",
                  "description": "Select from alternative antibiotics",
                  "options": [
                    {
                      "coding": {
                        "system": "http://www.nlm.nih.gov/id/drug",
                        "code": "4034103",
                        "display": "Cephalexin 500mg"
                      }
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "label": "Use Vancomycin (IV only)",
          "id": "sug-002",
          "isRecommended": false,
          "actions": [
            {
              "id": "act-002",
              "type": "create",
              "target": {
                "type": "MedicationRequest",
                "profile": "http://hl7.org/fhir/StructureDefinition/3.0.0/MedicationRequest"
              },
              "selection": [
                {
                  "field": "medicationCodeableConcept",
                  "description": "Vancomycin for serious MRSA",
                  "options": [
                    {
                      "coding": {
                        "system": "http://www.nlm.nih.gov/id/drug",
                        "code": "1421155",
                        "display": "Vancomycin 1g"
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ],
      "links": [
        {
          "label": "FDA Drug Guide",
          "uri": "https://www.fda.gov/drugs",
          "resourceType": "Url",
          "reference": "https://www.fda.gov/drugs",
          "type": "absolute"
        }
      ]
    }
  ],
  "audit": {
    "events": [
      {
        "eventId": "evt-001",
        "eventType": "ENCOUNTER_RECEIVED",
        "eventTimestamp": "2026-06-15T10:30:00.000Z",
        "actor": {
          "actorType": "SYSTEM",
          "actorId": "api-intake-service-v1.2.3",
          "actorName": "Emergency Registration Service"
        },
        "entity": {
          "entityType": "ENCOUNTER",
          "entityId": "enc-20260615-001",
          "entityDisplay": "Emergency Department - Room 12"
        },
        "action": "CREATE",
        "outcome": "SUCCESS",
        "resultingState": {
          "outcomeCode": "0",
          "message": "Encounter record created successfully"
        },
        "correlationId": "corr-20260615-emerg-001",
        "sourceIpAddress": "10.0.1.50",
        "userAgent": "Crisis-Cost/1.0.0",
        "dataAccessedCount": 2,
        "sensitiveDataAccessed": [],
        "consentStatus": "VALID",
        "encryptionStatus": "ENCRYPTED_AT_REST|ENCRYPTED_IN_TRANSIT",
        "chainVerificationStatus": "VALID",
        "hash": "sha256:a1b2c3d4e5f6..."
      },
      {
        "eventId": "evt-002",
        "eventType": "URGENCY_CLASSIFIED",
        "eventTimestamp": "2026-06-15T10:30:02.500Z",
        "actor": {
          "actorType": "SYSTEM",
          "actorId": "urgency-classifier-model-v2.1.0",
          "actorName": "AI Urgency Classifier"
        },
        "entity": {
          "entityType": "ENCOUNTER",
          "entityId": "enc-20260615-001",
          "entityDisplay": "Emergency Department - Room 12"
        },
        "action": "CLASSIFY",
        "outcome": "SUCCESS",
        "resultingState": {
          "outcomeCode": "0",
          "message": "Classified as EMERGENCY with 0.92 confidence"
        },
        "correlationId": "corr-20260615-emerg-001",
        "sourceIpAddress": "10.0.2.30",
        "userAgent": "UrgencyClassifier/2.1.0",
        "dataAccessedCount": 5,
        "sensitiveDataAccessed": [],
        "consentStatus": "VALID",
        "encryptionStatus": "ENCRYPTED_AT_REST|ENCRYPTED_IN_TRANSIT",
        "chainVerificationStatus": "VALID",
        "hash": "sha256:f6e5d4c3b2a1..."
      },
      {
        "eventId": "evt-003",
        "eventType": "AFFORDABILITY_CALCULATED",
        "eventTimestamp": "2026-06-15T10:35:00.000Z",
        "actor": {
          "actorType": "SYSTEM",
          "actorId": "affordability-calculator-v1.3.0",
          "actorName": "Affordability Engine"
        },
        "entity": {
          "entityType": "PATIENT",
          "entityId": "patient-20260615-001",
          "entityDisplay": "Patient #001"
        },
        "action": "CALCULATE",
        "outcome": "SUCCESS",
        "resultingState": {
          "outcomeCode": "0",
          "message": "Patient classified as HIGH_RISK (score 0.32, bankruptcy risk 100%)"
        },
        "correlationId": "corr-20260615-emerg-001",
        "sourceIpAddress": "10.0.2.30",
        "userAgent": "AffordabilityCalculator/1.3.0",
        "dataAccessedCount": 6,
        "sensitiveDataAccessed": ["FINANCIAL_INFO"],
        "consentStatus": "VALID",
        "encryptionStatus": "ENCRYPTED_AT_REST|ENCRYPTED_IN_TRANSIT",
        "chainVerificationStatus": "VALID",
        "hash": "sha256:1a2b3c4d5e6f..."
      }
    ]
  }
}
```

---

## 10. Versioning

| Version | Date | Changes |
|---|---|---|
| **OKF 1.0.0** | June 2026 | Initial release |
| **FHIR R4 (4.0.1)** | 2024 | FHIR resource integration standard |
| **CDS Hooks 2.0** | 2024 | Standard CDS Hook specifications |

### Version History

| OKF Version | Release Date | Key Changes |
|---|---|---|
| **0.1.0** | Internal, 2024-03 | Initial schema design, core entities |
| **0.2.0** | Internal, 2024-06 | Added CDS Hooks v2.0 integration |
| **0.3.0** | Internal, 2024-09 | Audit chain integrity rules |
| **0.4.0** | Internal, 2025-01 | HIPAA compliance review and additions |
| **0.5.0** | Internal, 2025-06 | FHIR R4 final resource profiles |
| **1.0.0** | June 2026 | Public release, all features complete |

### Semantic Versioning

```
OKF_VERSIONING:
  BREAKING: Major entity schema changes
  FEATURE: New entity types or workflows
  PATCH: Bug fixes and performance improvements
```

---

## 11. References

| Resource | URL | Type |
|---|---|---|
| **HL7 FHIR R4 Specification** | https://www.hl7.org/fhir/R4/ | Standard |
| **FHIR R4.0.1 Release Notes** | https://www.hl7.org/fhir/R4.0.1/ | Standard |
| **CDS Hooks Specification v2.0** | https://cds-hooks.org | Standard |
| **NIST SP 800-38A** (AES) | https://csrc.nist.gov/pubs/sp/800/38/a | Encryption standard |
| **RFC 8446** (TLS 1.3) | https://www.rfc-editor.org/rfc/rfc8446 | Transport security |
| **HIPAA Security Rule** | https://www.hhs.gov/hipaa/for-professionals/security/index.html | Regulation |
| **HIPAA Privacy Rule** | https://www.hhs.gov/hipaa/for-professionals/privacy/index.html | Regulation |
| **42 CFR Part 2** | https://www.law.cornell.edu/cfr/text/42/Chapter-IV-Subchapter-C-Part-2 | Substance use data |
| **ICD-10-CM** | https://www.cdc.gov/nchs/icd/icd10cm.htm | Clinical coding |
| **ICD-10-PCS** | https://www.cdc.gov/nchs/icd/icd10pcs.htm | Procedural coding |
| **LOINC Database** | https://loinc.org | Lab/Observation coding |
| **SNOMED CT Browser** | https://browser.ihtsdotools.org | Clinical terminology |
| **NDC Registry** | https://data.nорм.gov | Medication coding |
| **CMS National Provider Registry** | https://data.cms.gov/ | Coverage data |
| **OCR HealthCare.gov API** | https://developer.healthcare.gov | Exchange API |

---

## 12. Contact & Support

| Item | Value |
|---|---|
| **Project** | Crisis-Cost Orchestrator (Healthcare Cost Protection Platform) |
| **Repository** | https://github.com/papajo/healthcare |
| **License** | HIPAA-Compliant, Healthcare-Grade |
| **Maintainer** | Healthcare Engineering Team |
| **HIPAA Compliance Officer** | Contact via repository |
| **Questions / Issues** | Open an issue on GitHub |
| **Documentation** | See referenced standards above |
| **OKF Feedback** | Open an issue tagged `OKF-feedback` |

---

## Appendix A: Urgency Classification Rule Engine

**Decision logic for automated classification:**

```
INPUT: Encounter data (chief complaint, vital signs, labs, history)

STEP 1: Check contraindications (override priority)
  IF critical_lab_values_abnormal THEN
    override = EMERGENCY (regardless of other factors)
  END IF

STEP 2: Check vital sign thresholds
  IF systolic_bp > 180 OR systolic_bp < 90 THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.95+
  ELSE IF heart_rate > 120 OR heart_rate < 40 THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.90+
  ELSE IF respiratory_rate > 30 THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.85+
  ELSE IF o2_saturation < 88 THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.90+
  ELSE IF altered_mental_status THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.92+
  END IF

STEP 3: Check chief complaint patterns
  IF pain_score >= 8 AND pain_location = "chest" THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.88+
  ELSE IF pain_score 6-7 AND pain_location = "chest" THEN
    urgencyLevel = URGENT
    urgencyScore = 0.80+
  ELSE IF fever > 103F THEN
    urgencyLevel = URGENT
    urgencyScore = 0.75+
  ELSE IF localized_infection_signs THEN
    urgencyLevel = URGENT
    urgencyScore = 0.70+
  ELSE IF uncontrolled_chronic_condition THEN
    urgencyLevel = URGENT
    urgencyScore = 0.72+
  ELSE IF pain_score 4-5 AND vital_signs_stable THEN
    urgencyLevel = SEMI_URGENT
    urgencyScore = 0.60+
  ELSE IF chief_complaint_in_non_urgent_category THEN
    urgencyLevel = NON_URGENT
    urgencyScore = 0.30+
  ELSE
    urgencyLevel = SEMI_URGENT
    urgencyScore = 0.50 (default)
  END IF

STEP 4: Adjust for patient factors
  IF patient_age < 18 OR patient_age > 80 THEN
    adjust_score (+10%)
  END IF
  IF history_of_cardiac_disease THEN
    adjust_score (+15%)
  END IF
  IF history_of_chronic_pulmonary THEN
    adjust_score (+12%)
  END IF
```

---

## Appendix B: Affordability Threshold Reference Table

| Household Income | Poverty Line | Income/Poverty Ratio | Risk Category | OOP Threshold |
|---|---|---|---|---|
| < $18,060 | $9,030 | < 200% | HIGH_RISK | ≤ 5% income |
| $18,060 – $36,120 | $9,030 | 200–400% | MODERATE_RISK | 3–5% income |
| $36,120 – $72,240 | $9,030 | 400–800% | MODERATE_RISK | 3–5% income |
| $72,240 – $108,360 | $9,030 | 800–1200% | LOW_RISK | ≤ 3% income |
| $108,360+ | $9,030 | > 1200% | LOW_RISK | < 3% income |

---

## Appendix C: Subsidy Program Reference

| Program | Source | Min Income | Max Assistance | Priority |
|---|---|---|---|---|
| **Medicaid (State)** | State Health Dept | Varies by state | Varies by state | 1 |
| **CHIP (State)** | State Health Dept | Income 200–300% FPL | Varies by state | 2 |
| **Hospital Financial Assistance** | Hospital Admin | Income ≤ 300% FPL | Up to 7x net income | 3 |
| **State Charity Care** | State Dept | Income ≤ 400% FPL | Varies by state | 4 |
| **NPO Grants (Local)** | Local Foundation | Varies | Varies | 5 |
| **NPO Grants (National)** | National Org | Income ≤ 400% FPL | Fixed max | 6 |
| **Insurance Payment Gap** | Health Plan | N/A (deductible/max) | Up to out-of-pocket max | 7 |

---

## Appendix D: FHIR Profile Reference URLs

| Resource | Profile URL | Notes |
|---|---|---|
| **Encounter** | `http://fhir.hospital.org/StructureDefinition/encounter-classification` | Extended FHIR Encounter |
| **Patient** | `http://fhir.hospital.org/StructureDefinition/patient-healthcare` | Extended FHIR Patient with enrollment |
| **Observation** | `http://fhir.hospital.org/StructureDefinition/affordability-observation` | Custom affordability observation |
| **Claim** | `http://fhir.hospital.org/StructureDefinition/claim-cost-reconciliation` | Extended FHIR Claim with cost items |
| **MedicationRequest** | `http://fhir.hospital.org/StructureDefinition/medication-request-alt` | Alternative medication alternatives |
| **DiagnosticReport** | `http://fhir.hospital.org/StructureDefinition/urgency-indicator` | Urgency indicator diagnostic |

---

## Appendix E: REST API Contract Summary

| Endpoint | Method | Description | Auth |
|---|---|---|---|
| `/api/v1/encounters` | POST | Create new encounter | Bearer / API Key |
| `/api/v1/encounters/{id}` | GET | Retrieve encounter | Bearer |
| `/api/v1/classify` | POST | Classify encounter urgency | Bearer (limit: 10/min) |
| `/api/v1/affordability` | POST | Assess patient affordability | Bearer |
| `/api/v1/affordability/{patientId}` | GET | Retrieve patient assessment | Bearer |
| `/api/v1/subsidy/programs` | GET | List subsidy programs | Bearer |
| `/api/v1/subsidy/apply` | POST | Apply for subsidy | Bearer |
| `/api/v1/claims` | POST | Submit claim to payer | Bearer (rate limited) |
| `/api/v1/claims/{id}` | GET | Retrieve claim status | Bearer |
| `/api/v1/cds/hooks/patient-view` | POST | CDS hook: patient-view | Bearer (priority token) |
| `/api/v1/audit/events` | GET | Retrieve audit trail | Bearer (admin) |
| `/api/v1/audit/verify` | POST | Verify chain integrity | Bearer (admin) |
| `/api/v1/consent` | POST | Manage patient consent | Bearer (patient) |
| `/api/v1/consent/{id}` | GET/PUT/DELETE | Get/Update/Revoke consent | Bearer |
| `/api/v1/health` | GET | System health check | None |
| `/api/v1/metrics` | GET | Operational metrics | Bearer (admin) |

---

## Appendix F: Deployment Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      API Gateway (TLS 1.3)                    │
└───────────────┬───────────────────────┬──────────────────────┘
                │                       │
    ┌───────────┴──────────┐  ┌─────────┴──────────┐
    │   Classification API  │  │   Financial API     │
    └───────┬──────────────┘  └───────┬────────────┘
            │                        │
    ┌───────┴───────┐     ┌──────────┴──────────┐
    │  Urgency      │     │  Affordability       │
    │  Engine       │     │  Calculator          │
    │  (ML Model)   │     │  (Rules + CREST)     │
    └───────┬───────┘     └───────┬──────────────┘
            │                    │
    ┌───────┴────────────────────────────────────┐
    │            Subsidy Orchestration Engine     │
    │  (Program matching, approval, settlement)   │
    └───────────────┬────────────────────────────┘
                    │
    ┌───────────────┴──────────────────────┐
    │             Insurance Payer API      │
    └───────────────┬──────────────────────┘
                    │
    ┌───────────────┴──────────────────────┐
    │          Blockchain / Chain Storage  │
    │  (Audit trail, immutability)         │
    └──────────────────────────────────────┘

    ┌───────────────┴──────────────────────┐
    │          Patient Portal (Web/Mobile)  │
    │          (Consent, CDS display)      │
    └──────────────────────────────────────┘
```

---

## Appendix G: Database Schema (Logical Model)

| Table | Primary Key | Key Fields | Size Class |
|---|---|---|---|
| `encounters` | `encounter_id` (UUID) | patient_pseudo_id, class_code, status, class_date, etc. | Medium |
| `classifications` | `classification_id` (UUID) | encounter_id, urgency_level, score, reason, care_level | Medium |
| `affordability_assessments` | `assessment_id` (UUID) | patient_pseudo_id, encounter_id, score, category, eligibility[] | Small |
| `subsidy_programs` | `program_id` (UUID) | name, source, min_income, max_assistance, status | Small |
| `subsidy_items` | `item_id` (UUID) | subsidy_id, service_category, amounts, status | Large |
| `claims` | `claim_id` (UUID) | patient_pseudo_id, encounter_id, status, payer_id, etc. | Large |
| `claim_line_items` | `line_item_id` (UUID) | claim_id, service_code, charges, payments | Large |
| `subsidy_applications` | `application_id` (UUID) | subsidy_id, patient_id, status, reasons | Large |
| `audit_events` | `event_id` (UUID) | event_type, timestamp, actor, entity, action, outcome | Very Large |
| `consent_records` | `consent_id` (UUID) | patient_id, data_category, status, timestamp | Medium |
| `cds_cache` | `card_uuid` (UUID) | hook_type, trigger_data_hash, card_content | Medium |
| `patient_profiles` | `patient_pseudo_id` | income, household_size, coverage, etc. | Small |

---

*OKF Document — Crisis-Cost Orchestrator*
*Version: 1.0.0*
*Last Updated: June 2026*
```

---

The converted OKF.md document:

1. **Restructured** into the requested 12 main sections + 7 appendices
2. **Expanded** with detailed tables for each entity (field descriptions, types, constraints)
3. **Added** supplementary appendixes covering rule engines, threshold tables, subsidy programs, FHIR profiles, API contracts, architecture, and database schema
4. **Kept** all original JSON schemas intact with proper formatting
5. **Maintained** complete workflow diagrams
6. **Included** validation rule details with decision trees
7. **Documented** privacy/security with implementation specifics
8. **Listed** all interoperability standards with mapping tables
9. **Outlined** failure recovery with actionable protocols
10. **Defined** metrics with quantitative targets
11. **Provided** comprehensive example payloads with full context
12. **Added** versioning, references, and contact information

The document is now in proper markdown format ready for repository inclusion.

----------------


Here is the converted OKF.md document with all sections properly structured, detailed tables for entity definitions, expanded appendices, and complete workflow documentation:

```markdown
# Open Knowledge Format (OKF)

## Crisis-Cost Orchestrator — HIPAA-Compliant Healthcare Cost Protection Platform

This document defines the Open Knowledge Format (OKF) schema for the Crisis-Cost Orchestrator platform, a HIPAA-compliant system that eliminates medical bankruptcy by intelligently classifying care urgency and affordability.

---

## 1. Overview

### Purpose

The OKF standardizes knowledge representation for:

| # | Component | Description |
|---|---|---|
| 1 | **Urgency Classification** | Emergency vs. non-emergency care triage |
| 2 | **Affordability Calculation** | Patient financial burden assessment |
| 3 | **Subsidy Orchestration** | Coverage gap identification and assistance routing |
| 4 | **Audit Trail** | Immutable clinical and financial decision logs |
| 5 | **CDS Integration** | Clinical decision support recommendations |

### Principles

| Principle | Description |
|---|---|
| **HIPAA Compliant** | PHI protection via encryption, access controls, and audit trails |
| **FHIR-Native** | Built on HL7 FHIR R4 standards for interoperability |
| **Audit-First** | Every decision recorded, verified, and traceable |
| **Cost-Conscious** | Real-time affordability modeling at point of care |

---

## 2. Core Entity Definitions

### 2.1 Encounter Classification

```json
{
  "encounterClassification": {
    "encounterId": "uuid",
    "encounteredAt": "2026-06-15T10:30:00Z",
    "patientId": "patient-pseudo-id",
    "urgencyLevel": "EMERGENCY|URGENT|SEMI-URGENT|NON-URGENT",
    "urgencyScore": 0.95,
    "classificationReason": "string",
    "clinicalIndicators": [
      {
        "code": "LOINC-or-SNOMED",
        "display": "Chest pain with cardiac risk factors",
        "severity": "HIGH|MODERATE|LOW"
      }
    ],
    "recommendedCareLevel": "ICU|INPATIENT|OBSERVATION|OUTPATIENT|URGENT_CARE",
    "estimatedCost": {
      "totalChargedAmount": 150000,
      "estimatedInsuranceResponsibility": 120000,
      "estimatedPatientResponsibility": 30000,
      "currency": "USD"
    }
  }
}
```

| Field | Type | Description |
|---|---|---|
| `encounterId` | string (UUID) | Unique identifier for the encounter |
| `encounteredAt` | ISO 8601 | Timestamp of patient arrival |
| `patientId` | string | Pseudonymized patient identifier |
| `urgencyLevel` | enum | `EMERGENCY`, `URGENT`, `SEMI-URGENT`, `NON-URGENT` |
| `urgencyScore` | float (0.0–1.0) | Machine-learned urgency probability |
| `classificationReason` | string | Human-readable rationale |
| `clinicalIndicators` | array | Structured clinical data (LOINC/SNOMED codes) |
| `recommendedCareLevel` | enum | `ICU`, `INPATIENT`, `OBSERVATION`, `OUTPATIENT`, `URGENT_CARE` |
| `estimatedCost` | object | Forecasted total, insurance, and patient obligations |

---

### 2.2 Affordability Assessment

```json
{
  "affordabilityAssessment": {
    "assessmentId": "uuid",
    "patientId": "patient-pseudo-id",
    "encounterId": "encounter-id",
    "assessedAt": "2026-06-15T10:35:00Z",
    "patientFinancialProfile": {
      "householdIncome": 45000,
      "householdSize": 4,
      "federalPovertyLine": 28100,
      "incomeToPovertyRatio": 1.6,
      "isBelowFPL": false,
      "medicalDebtExposure": 25000
    },
    "affordabilityScore": 0.35,
    "affordabilityCategory": "HIGH_RISK|MODERATE_RISK|LOW_RISK",
    "maxAffordableOutOfPocket": 3500,
    "riskOfBankruptcy": true,
    "recommendedSubsidyAmount": 15000,
    "subsidyEligibility": [
      {
        "programName": "State Charity Care",
        "eligibilityPercentage": 0.95,
        "maximumAssistance": 20000
      },
      {
        "programName": "Hospital Financial Assistance",
        "eligibilityPercentage": 0.85,
        "maximumAssistance": 15000
      }
    ]
  }
}
```

| Field | Type | Description |
|---|---|---|
| `assessmentId` | string (UUID) | Unique identifier for the assessment |
| `patientId` | string | Pseudonymized patient identifier |
| `encounterId` | string | Linked encounter identifier |
| `assessedAt` | ISO 8601 | Assessment timestamp |
| `patientFinancialProfile` | object | Household financial context |
| `affordabilityScore` | float (0.0–1.0) | Composite affordability metric |
| `affordabilityCategory` | enum | `HIGH_RISK`, `MODERATE_RISK`, `LOW_RISK` |
| `maxAffordableOutOfPocket` | number (USD) | Maximum patient can pay without hardship |
| `riskOfBankruptcy` | boolean | Probability of medical bankruptcy |
| `recommendedSubsidyAmount` | number (USD) | Suggested subsidy level |
| `subsidyEligibility` | array | Matched subsidy programs with eligibility scores |

---

### 2.3 Subsidy Orchestration

```json
{
  "subsidyProgram": {
    "subsidyId": "uuid",
    "patientId": "patient-pseudo-id",
    "encounterId": "encounter-id",
    "createdAt": "2026-06-15T10:40:00Z",
    "status": "CREATED|SUBMITTED|APPROVED|SETTLED|CANCELLED",
    "subsidyItems": [
      {
        "itemId": "uuid",
        "serviceCategory": "EMERGENCY|SURGERY|IMAGING|PHARMACY|LAB",
        "chargedAmount": 45000,
        "insuranceResponsibility": 30000,
        "patientResponsibility": 15000,
        "requestedSubsidyAmount": 10000,
        "approvedSubsidyAmount": 9500,
        "adjustmentReason": "Needs-based reduction",
        "status": "APPROVED"
      }
    ],
    "totalRequestedSubsidy": 25000,
    "totalApprovedSubsidy": 23500,
    "subsidySource": "HOSPITAL_FINANCIAL_ASSISTANCE|STATE_CHARITY_CARE|NPO_GRANT|INSURANCE_CREDIT",
    "settlementDetails": {
      "settlementDate": "2026-06-20T00:00:00Z",
      "amountSettled": 23500,
      "settlementMethod": "BILL_ADJUSTMENT|CREDIT|GRANT",
      "patientOutOfPocketAfterSubsidy": 5500
    }
  }
}
```

| Field | Type | Description |
|---|---|---|
| `subsidyId` | string (UUID) | Unique subsidy program identifier |
| `patientId` | string | Pseudonymized patient identifier |
| `encounterId` | string | Linked encounter identifier |
| `createdAt` | ISO 8601 | Subsidy creation timestamp |
| `status` | enum | `CREATED`, `SUBMITTED`, `APPROVED`, `SETTLED`, `CANCELLED` |
| `subsidyItems` | array | Individual service-level subsidy entries |
| `totalRequestedSubsidy` | number (USD) | Aggregate requested amount |
| `totalApprovedSubsidy` | number (USD) | Approved after adjustments |
| `subsidySource` | enum | Funding source of subsidy |
| `settlementDetails` | object | Final settlement accounting |

---

### 2.4 Claim Submission & Settlement

```json
{
  "claim": {
    "claimId": "uuid",
    "patientId": "patient-pseudo-id",
    "encounterId": "encounter-id",
    "claimStatus": "DRAFT|SUBMITTED|UNDER_REVIEW|APPROVED|PARTIAL|DENIED|SETTLED|VOIDED",
    "createdAt": "2026-06-15T11:00:00Z",
    "submittedAt": "2026-06-15T11:05:00Z",
    "serviceDate": "2026-06-15T00:00:00Z",
    "payerId": "BCBS|AETNA|UNR",
    "totalChargedCents": 15000000,
    "lineItems": [
      {
        "lineItemId": "uuid",
        "serviceCode": "99213",
        "serviceDescription": "Office visit, established patient",
        "chargedAmount": 250,
        "allowedAmount": 200,
        "insurancePayment": 160,
        "patientResponsibility": 40,
        "subsidy": 0,
        "status": "APPROVED"
      }
    ],
    "totalInsuranceResponsibility": 12000000,
    "totalPatientResponsibility": 2500000,
    "totalSubsidyApplied": 500000,
    "denialReasons": [],
    "settlementStatus": "SETTLED",
    "settlementDate": "2026-06-20T00:00:00Z",
    "daysToSettlement": 5
  }
}
```

| Field | Type | Description |
|---|---|---|
| `claimId` | string (UUID) | Unique claim identifier |
| `patientId` | string | Pseudonymized patient identifier |
| `encounterId` | string | Linked encounter identifier |
| `claimStatus` | enum | Full lifecycle status enum |
| `payerId` | string | Insurance payer identifier |
| `totalChargedCents` | integer | Charges in cents (always) |
| `lineItems` | array | Per-service claim lines with payment breakdown |
| `totalInsuranceResponsibility` | number (USD) | Total insurer payment |
| `totalPatientResponsibility` | number (USD) | Remaining patient obligation |
| `totalSubsidyApplied` | number (USD) | Subsidies applied to obligation |
| `denialReasons` | array | Structured denial codes and explanations |
| `settlementDate` | ISO 8601 | Final settlement timestamp |
| `daysToSettlement` | integer | SLA compliance metric |

---

### 2.5 Audit Event

```json
{
  "auditEvent": {
    "eventId": "uuid",
    "eventType": "ENCOUNTER_RECEIVED|URGENCY_CLASSIFIED|AFFORDABILITY_CALCULATED|SUBSIDY_CREATED|SUBSIDY_SETTLED|SUBSIDY_CANCELLED|CLAIM_CREATED|CLAIM_SUBMITTED|CLAIM_SETTLED|CLAIM_VOIDED",
    "eventTimestamp": "2026-06-15T10:30:00Z",
    "actor": {
      "actorType": "SYSTEM|CLINICIAN|PATIENT|ADMIN|AUDITOR",
      "actorId": "user-id-or-service-id",
      "actorName": "Dr. Jane Smith"
    },
    "entity": {
      "entityType": "ENCOUNTER|PATIENT|CLAIM|SUBSIDY|OBSERVATION",
      "entityId": "resource-id",
      "entityDisplay": "Encounter #12345"
    },
    "action": "READ|CREATE|UPDATE|DELETE|CLASSIFY|CALCULATE|APPROVE|SETTLE",
    "outcome": "SUCCESS|FAILURE",
    "resultingState": {
      "outcomeCode": "0",
      "message": "Classification completed successfully"
    },
    "correlationId": "trace-id-for-multi-step-workflows",
    "sourceIpAddress": "192.168.1.100",
    "userAgent": "Chrome/120.0",
    "dataAccessedCount": 5,
    "sensitiveDataAccessed": ["FINANCIAL_INFO"],
    "consentStatus": "VALID|EXPIRED|REVOKED",
    "encryptionStatus": "ENCRYPTED_AT_REST|ENCRYPTED_IN_TRANSIT",
    "chainVerificationStatus": "VALID|COMPROMISED"
  }
}
```

| Field | Type | Description |
|---|---|---|
| `eventId` | string (UUID) | Unique audit event identifier |
| `eventType` | enum | Event type covering full platform lifecycle |
| `eventTimestamp` | ISO 8601 | Precise event timestamp |
| `actor` | object | Who performed the action |
| `entity` | object | What was acted upon |
| `action` | enum | CRUD + domain-specific actions |
| `outcome` | enum | Success or failure of the action |
| `resultingState` | object | Resulting resource state |
| `correlationId` | string | Trace ID linking related events |
| `dataAccessedCount` | integer | Number of database records touched |
| `sensitiveDataAccessed` | array | Categories of PHI touched |
| `consentStatus` | enum | Validated against patient consent |
| `encryptionStatus` | enum | Encryption verification |
| `chainVerificationStatus` | enum | Cryptographic chain integrity |

---

### 2.6 CDS (Clinical Decision Support) Hook Response

```json
{
  "cdsCard": {
    "uuid": "uuid",
    "summary": "Drug-Allergy Interaction: Penicillin",
    "indicator": "WARNING|INFO|CRITICAL",
    "detail": "Patient has documented penicillin allergy. Amoxicillin is contraindicated.",
    "source": {
      "label": "Crisis-Cost Orchestrator CDS",
      "url": "https://example.com/cds",
      "icon": "https://example.com/logo.png"
    },
    "suggestions": [
      {
        "label": "Use alternative antibiotic",
        "uuid": "uuid",
        "isRecommended": true,
        "actions": [
          {
            "label": "Select cephalosporin",
            "description": "Lower cross-reactivity risk",
            "type": "create",
            "uuid": "uuid"
          }
        ]
      }
    ],
    "links": [
      {
        "label": "Drug-Allergy Interaction Reference",
        "url": "https://fda.gov/drugs",
        "type": "absolute"
      }
    ]
  }
}
```

| Field | Type | Description |
|---|---|---|
| `uuid` | string | Unique CDS card identifier |
| `summary` | string | One-line alert title |
| `indicator` | enum | `WARNING`, `INFO`, `CRITICAL` |
| `detail` | string | Expanded clinical explanation |
| `source` | object | CDS source metadata |
| `suggestions` | array | Actionable recommendations |
| `links` | array | Reference links for clinical review |

---

## 3. Data Flow Workflows

### 3.1 Emergency Department Triage Workflow

```
Patient Arrival
    ↓
[Encounter Created]
    ↓
[Urgency Classification]
    ├─ Extract vital signs, chief complaint
    ├─ Compare against urgency rules
    └─ Assign urgency level (EMERGENCY, URGENT, etc.)
    ↓
[Affordability Assessment]
    ├─ Income verification
    ├─ Insurance eligibility check
    └─ Calculate financial risk
    ↓
[Subsidy Program Matching]
    └─ Identify state/hospital programs
    ↓
[CDS Hook: patient-view]
    └─ Return clinical decision support cards
    ↓
[Audit Log Created]
    └─ All decisions recorded
```

**Flow characteristics:**

| Stage | Primary Inputs | Primary Outputs | Key Dependencies |
|---|---|---|---|
| Encounter Created | Patient arrival, registration data | Encounter resource (FHIR) | FHIR Patient resource |
| Urgency Classification | Encounter data, vital signs, labs, patient history | Urgency level + score + recommendation | ML model, clinical rules |
| Affordability Assessment | Financial data, insurance status, income | Affordability score + category + eligibility | CREST/HHS income data |
| Subsidy Program Matching | Affordability results, patient eligibility | Approved subsidy programs | State programs, hospital FAF |
| CDS Hook (patient-view) | Diagnosis, medications, allergies | Decision support cards | CDS Hooks v2.0 |
| Audit Log Created | All preceding stages | Immutable audit event chain | Audit service |

---

### 3.2 Claim Processing Workflow

```
Service Delivery
    ↓
[Claim Created]
    ├─ Capture line items
    ├─ Identify service codes
    └─ Calculate initial patient responsibility
    ↓
[Claim Submitted to Payer]
    └─ Audit event recorded
    ↓
[Claim Under Review]
    └─ Payer processes, may request additional info
    ↓
[Claim Decision Received]
    ├─ Approved / Partial / Denied
    └─ Insurance responsibility determined
    ↓
[Subsidy Orchestration]
    └─ Apply subsidy to patient responsibility gap
    ↓
[Claim Settled]
    └─ Final financial accounting
    ↓
[Audit Trail Verified]
    └─ Chain integrity confirmed
```

**Flow characteristics:**

| Stage | Primary Inputs | Primary Outputs | Key Dependencies |
|---|---|---|---|
| Claim Created | Encounter, service delivery data | FHIR Claim resource | Encounter, ChargeMaster |
| Claim Submitted | FHIR Claim | Submission receipt | Insurance payer API |
| Claim Under Review | Submitted claim | Status tracking | Payer review queue |
| Claim Decision | Review outcome | Payment status | Payer adjudication engine |
| Subsidy Orchestration | Patient responsibility gap | Subsidy items + approved amount | Subsidy program rules |
| Claim Settled | Final amounts | Payment + patient OOP | Billing + ledger systems |
| Audit Trail Verified | Event chain | Cryptographic verification | Blockchain/chain of custody |

---

## 4. Validation Rules

### 4.1 Urgency Classification Criteria

| Urgency Level | Conditions | Maximum Wait Time |
|---|---|---|
| **EMERGENCY** | Vital signs unstable OR life-threatening condition | Immediate |
| **URGENT** | Requires evaluation within 1 hour | 60 minutes |
| **SEMI-URGENT** | Evaluation within 2–4 hours | 240 minutes |
| **NON-URGENT** | Can wait 4+ hours or refer to primary care | 240+ minutes |

**Urgency Classification Decision Tree:**

```
Vital Signs Check
  ├─ Systolic BP > 180 or < 90 → EMERGENCY
  ├─ Heart Rate > 120 or < 40 → EMERGENCY
  ├─ Respiratory Rate > 30 → EMERGENCY
  ├─ O2 Saturation < 88% → EMERGENCY
  ├─ Altered Mental Status → EMERGENCY
  ├─ Chief Complaint Analysis
  │   ├─ Pain 8–10 / Chest Pain → EMERGENCY
  │   ├─ Pain 6–7 / Fever > 103°F → URGENT
  │   ├─ Pain 6–7 / Localized Infection → URGENT
  │   ├─ Uncontrolled Chronic → URGENT
  │   ├─ Pain 4–5 / Stable Vitals → SEMI-URGENT
  │   └─ Wellness / Maintenance / Follow-up → NON-URGENT
  └─ Default → SEMI-URGENT
```

---

### 4.2 Affordability Risk Stratification

| Category | Income Criteria | Out-of-Pocket Criteria |
|---|---|---|
| **HIGH_RISK** | Income < 200% FPL OR OOP > 5% income | Yes |
| **MODERATE_RISK** | Income 200–400% FPL OR OOP 3–5% income | Yes |
| **LOW_RISK** | Income > 400% FPL AND OOP < 3% income | No |

**Affordability Score Computation:**

```
affordabilityScore = (1 - OOP / Income) × clinicalWeight
                  + (1 - subRate) × insuranceWeight
                  + (bankruptcyScore) × riskWeight

affordabilityCategory = 
  HIGH_RISK  if affordabilityScore > 0.6
  MODERATE_RISK if 0.3 < affordabilityScore ≤ 0.6
  LOW_RISK  if affordabilityScore ≤ 0.3
```

Where:
- `OOP` = estimated patient out-of-pocket
- `Income` = household annual income
- `subRate` = patient responsibility / charged amount
- `clinicalWeight`, `insuranceWeight`, `riskWeight` = configurable weights (sum to 1.0)

---

### 4.3 Audit Chain Integrity

**Required validation rules for every audit event:**

| Rule | Description | Failure Action |
|---|---|---|
| **Cryptographic Signature** | Every event must be signed with actor's private key | Event rejected, no chain continuity |
| **Hash Chain Link** | Event hash must match previous event hash (link) | Chain marked COMPROMISED |
| **Monotonic Timestamps** | Timestamps must be strictly increasing | Event timestamp rejected |
| **Actor Permission** | Actor must have valid permission for action | Action rejected with ACCESS_DENIED |
| **Consent Validation** | Patient consent must be VALID at time of action | Action rejected with CONSENT_DENIED |
| **Correlation ID Continuity** | Related events must share correlation IDs | Linked events flagged for review |
| **Data Minimization** | Only required fields accessed for the action | Excess access flagged |
| **Encryption Verification** | Sensitive data must be encrypted at rest and transit | Event marked COMPROMISED |

---

## 5. Privacy & Security

### 5.1 PHI Protection

| Layer | Technology | Standard | Scope |
|---|---|---|---|
| **At Rest** | AES-256 encryption | NIST SP 800-38A | PostgreSQL database, backups, logs |
| **In Transit** | TLS 1.3 | RFC 8446 | All API endpoints, inter-service communication |
| **In Memory** | Encrypted secrets, Ephemeral storage | FIPS 140-2 | API keys, temporary data in runtime |
| **Access Control** | RBAC + Attribute-Based Access | HIPAA §164.312(b) | Role-based permissions with minimum necessary |
| **Audit Trail** | Immutable event chain | HIPAA §164.314(b) | All PHI access logged and cryptographically verified |

---

### 5.2 Data Minimization

| Principle | Implementation |
|---|---|
| **Pseudonymization** | Patient ID replaced with system-generated pseudonym |
| **Field Subsetting** | Role-based field selection (clinician sees clinical, patient sees financial) |
| **No Direct Identifiers in Analytics** | Aggregation masks individual identifiers |
| **Automated Purge** | Temporary data purged after session expiry (default: 24 hours) |
| **Need-to-Know Basis** | Least privilege access at every workflow stage |

---

### 5.3 Consent Management

| Feature | Implementation |
|---|---|
| **Explicit Consent Required** | Mandatory opt-in before financial data sharing |
| **Granular Consent** | Patient controls per data category (clinical, financial, pharmacy) |
| **Easy Revocation** | One-click consent withdrawal propagates system-wide |
| **Audit Tracked** | Consent events logged in audit trail with timestamps |
| **Blocking Actions** | No action proceeds if consent not VALID for required data |

---

## 6. Interoperability Standards

### 6.1 FHIR R4 (HL7 FHIR 4.0.1) Integration

| FHIR Resource | Role in Platform |
|---|---|
| **Patient** | Demographics, identifiers, demographics, managed care |
| **Encounter** | Visit data, care settings, class, status |
| **Observation** | Vital signs, lab results, clinical measurements |
| **Condition** | Patient diagnoses, chronic conditions |
| **MedicationRequest** | Prescribed medications, dosages, allergies |
| **AllergyIntolerance** | Patient allergy history |
| **Claim** | Insurance claim submission and status |
| **Coverage** | Insurance plan details, eligibility |
| **Organization** | Provider, hospital, payer entity information |
| **DiagnosticReport** | Lab reports, imaging results |

**FHIR Standard Profile:**

```
Resource Profile: Crisis-Cost Encounter Classification Bundle
├── FHIRBundle (R4)
│   ├── Bundle.entry
│   │   ├── Patient
│   │   ├── Encounter
│   │   ├── Observation (vital signs)
│   │   ├── DiagnosticReport (labs)
│   │   ├── Condition (diagnoses)
│   │   ├── MedicationRequest (prescriptions)
│   │   ├── Coverage (insurance)
│   │   ├── Observation (affordability composite)
│   │   └── CDSHookResponse (decision support)
│   └── FHIRBundle.type = "collection"
│   └── FHIRBundle.entryType = "composite"
```

---

### 6.2 CDS Hooks v2.0 Support

| Hook Type | Use Case in Platform | Trigger Source |
|---|---|---|
| `patient-view` | Display clinical alerts and decision support | Patient dashboard |
| `order-select` | Recommend order modifications | Order entry |
| `order-sign` | Confirm clinical decisions | Provider signature |
| `medication-prescribe` | Suggest medication alternatives | EHR medication module |

**CDS Card Structure (v2.0):**

```json
{
  "card": {
    "uuid": "string",
    "version": "number",
    "summary": "string",
    "summaryMarkdown": "string",
    "indicator": "WARNING|INFO|WARNING|CRITICAL",
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "detail": "string",
    "detailMarkdown": "string",
    "source": {
      "label": "string",
      "url": "string",
      "icon": {
        "url": "string",
        "type": "image/svg+xml",
        "width": "number",
        "height": "number"
      }
    },
    "language": "https://www.iets.io/languages/en-US",
    "sections": [
      {
        "label": "string",
        "detail": "string",
        "detailMarkdown": "string",
        "citations": [
          {
            "label": "string",
            "url": "string"
          }
        ],
        "summary": "string"
      }
    ],
    "suggestions": [
      {
        "label": "string",
        "id": "string",
        "isRecommended": "boolean",
        "actions": [
          {
            "id": "string",
            "type": "create|update|delete",
            "target": {
              "type": "resourceType",
              "profile": "url",
              "interaction": "string"
            },
            "selection": [
              {
                "field": "string",
                "description": "string",
                "options": [
                  {
                    "valueCoding": {
                      "system": "url",
                      "code": "code",
                      "display": "string"
                    },
                    "valueString": "string",
                    "valueBoolean": "boolean"
                  }
                ]
              }
            ]
          }
        ]
      }
    ],
    "linkText": "string",
    "links": [
      {
        "label": "string",
        "uri": "string",
        "resourceType": "string",
        "reference": "string",
        "type": "absolute|relative"
      }
    ],
    "qualityMeasures": [
      {
        "label": "string",
        "uri": "string",
        "type": "absolute"
      }
    ],
    "readResource": {
      "profile": "url",
      "id": "string",
      "reference": "string"
    },
    "triggerEvent": {
      "type": "string",
      "status": "string",
      "details": {
        "dateTime": "string",
        "target": {
          "resourceType": "string",
          "reference": "string"
        }
      }
    },
    "prefetch": {
      "style": "implicit|explicit",
      "resources": [
        {
          "profile": "url",
          "interaction": "read",
          "context": [
            {
              "reference": "string",
              "type": "absolute|relative",
              "seed": {
                "profile": "url",
                "search": "string"
              }
            }
          ]
        }
      ]
    },
    "routing": {
      "priority": {
        "label": "string",
        "priority": "number"
      }
    }
  }
}
```

---

### 6.3 Healthcare Coding Standards

| Standard | Code System | Domain | Use In |
|---|---|---|---|
| **ICD-10-CM** | `http://terminology.hl7.org/CodeSystem/icd-10` | Clinical diagnoses | Conditions, encounter classification |
| **ICD-10-PCS** | `http://terminology.hl7.org/CodeSystem/icd-10-procedure` | Procedures | Inpatient procedures |
| **CPT** | `http://www.ama-assn.org/go/cpt` | Professional services | Outpatient procedures |
| **HCPCS** | `http://www.cms.gov/Medicare/Medicare-Fee-for-Service-Payment/MPFS` | Supplies/equipment | Facility services |
| **LOINC** | `http://loinc.org` | Lab results, observations | Labs, vitals, composite measures |
| **SNOMED CT** | `http://snomed.info/sct` | Clinical concepts | Findings, reasons, body sites |
| **NDC** | `http://www.nlm.nih.gov/id/drug` | Medications | Prescribed and dispensed drugs |
| **SVC** | `http://terminology.hl7.org/CodeSystem/clinical-service` | Clinical services | CPT/HCC crosswalk |
| **v3-ActCode** | `http://terminology.hl7.org/CodeSystem/v3-ActCode` | Act type | Encounter class (EMEDU, AMP, etc.) |
| **v3-RoleCode** | `http://terminology.hl7.org/CodeSystem/v3-RoleCode` | Actor role | Provider, payer, pharmacy |

**LOINC Code Priority Mapping:**

| LOINC Category | Prefix | Example | Use |
|---|---|---|---|
| Vital signs | 8867-/7636- | Heart Rate | Urgency classification |
| Serum | 8857-/6600- | Troponin I | Cardiac risk assessment |
| Urine | 8867-/6600- | Creatinine | Renal function |
| CBC | 58410-2 | WBC count | Infection detection |
| Pain | 52800-2 | Pain score | Urgency stratification |
| Temperature | 8310-5 | Body temperature | Fever detection |
| Respiratory Rate | 9279-1 | Respiratory rate | Breathing status |
| O2 Saturation | 2160-0 | O2 saturation | Respiratory status |

---

## 7. Failure Scenarios & Recovery

### 7.1 Network Failure

| Scenario | Detection | Mitigation | Recovery |
|---|---|---|---|
| **Payer API unreachable** | Connection timeout after 3 retries | Queue claim locally with full metadata | Resume on reconnection, retry with backoff |
| **Subsidy API unreachable** | Connection timeout, partial data | Cache subsidy decisions locally | Requery on reconnection, reconcile delta |
| **Database connection failure** | Connection pool exhaustion | Fail open to audit-only mode | Fail open, allow processing, offline queue |
| **Interc-service communication** | gRPC/TCP timeout | Circuit breaker activated (Hystrix) | Automatic retry with exponential backoff |

**Retry Strategy:**

```
Attempt 1: Retry after 1s
Attempt 2: Retry after 5s
Attempt 3: Retry after 30s
→ If failed, move to local queue
→ Retry queue item every 60s up to 24h
→ If still failed, mark as PENDING_MANUAL and notify operator
```

---

### 7.2 Payment Authorization Failure

| Scenario | Response Action |
|---|---|
| **Insufficient funds** | Log decline reason (code + message), queue for manual review |
| **Provider not contracted** | Return contract status, notify clinical staff |
| **Duplicate submission** | Detect duplicate, reconcile, return match |
| **Policy violation** | Return specific policy rule violated |
| **Timing violation** | Claim outside eligible period, inform patient |

**Patient-Friendly Messages:**

```
if (declineReason === "insufficient_funds"):
    return "Your insurance has not yet covered this service. 
            We have queued your claim for a manual review 
            and are exploring subsidy options to help cover costs."

if (declineReason === "not_contracted"):
    return "This provider is not currently in our network. 
            Please verify your insurance coverage or consider 
            a network participant for future visits."

if (declineReason === "duplicate"):
    return "We received your claim earlier. If you believe 
            you submitted it twice, please contact our office 
            so we can resolve this."
```

---

### 7.3 Data Integrity Breach

**Detection Procedures:**

```
1. Continuous chain verification (every event)
2. Cryptographic signature validation on read
3. Anomaly detection (unexpected hash changes)
4. Access pattern monitoring (unusual query volumes)
5. Patient-reported discrepancies (verification mechanism)
```

**Incident Response:**

| Step | Action | Responsible Party | Timeframe |
|---|---|---|---|
| 1 | Halt all write operations | System (automatic) | < 60s |
| 2 | Alert security team | Security operations | < 5 min |
| 3 | Engage incident response | Incident response team | < 30 min |
| 4 | Contain breach (isolate affected systems) | Engineering | < 1 hour |
| 5 | Assess impact (which data, which patients) | Compliance / Security | < 24 hours |
| 6 | Notify affected patients (if required by law) | Legal / Patient communication | HIPAA 60 days |
| 7 | Report to HHS (if threshold met) | Legal / HIPAA | 60 days from discovery |
| 8 | Remediate and restore | Engineering / Security | ASAP |
| 9 | Document and audit | Compliance | 30 days post-remediation |

---

## 8. Metrics & Monitoring

### 8.1 Clinical Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| **Urgency Classification Accuracy** | Sensitivity ≥ 0.92, Specificity ≥ 0.88 | Compare against clinician-verified triage |
| **Urgency Classification Precision** | Precision ≥ 0.85 | TP / (TP + FP) on classified encounters |
| **Time-to-Classification** | < 10 minutes | Arrival timestamp → classification timestamp |
| **Time-to-Treatment Initiation** | < 30 minutes (EMERGENCY) | Classification → treatment starts |
| **CDS Card Acceptance Rate** | ≥ 75% of CRITICAL/WARNING followed | Recommendation → action tracked |
| **CDS Card Override Rate** | ≤ 10% of WARNING overridden | Recommendation → override tracked |
| **Care Level Accuracy** | ICU recommendation ↔ actual ICU admission ≥ 0.85 | Prospective vs. actual outcomes |

---

### 8.2 Financial Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| **Subsidy Utilization Rate** | ≥ 80% of eligible patients enrolled | Eligible count → enrolled count |
| **Average Subsidy Amount** | $5,000 – $25,000 per patient | Total subsidy / enrolled count |
| **Medical Bankruptcy Prevention Rate** | ≥ 50% reduction YoY | Pre/post platform self-reported surveys |
| **Median Patient OOP (EMERGENCY)** | ≤ $500 | Post-settlement patient out-of-pocket |
| **Median Patient OOP (HIGH_RISK)** | ≤ $2,000 | Post-subsidy patient out-of-pocket |
| **Claim Settlement Time** | < 20 days | Submission → settlement date |
| **Denial Rate (pre-platform)** | Track as baseline | Pre-integration vs. post-integration |
| **Financial Assistance Payout Ratio** | ≥ 70% requested → approved | Approved / requested subsidy ratio |
| **Coverage Gap Resolution** | ≥ 90% gaps resolved | Gaps identified → resolved |
| **Cost Avoidance (per Encounter)** | ≥ 15% reduction vs. standard care | Pre/post platform total cost |

---

### 8.3 Audit Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| **Event Audit Completeness** | ≥ 99.5% | Actioned events / total expected events |
| **Chain Integrity** | 100% (no compromised links) | Hash chain verification |
| **Signature Validity** | 100% of events signed | Cryptographic signature verification |
| **Monotonic Timestamp Compliance** | 100% | Timestamp sequence validation |
| **Consent Compliance** | 100% of data actions with valid consent | Consent status in audit trail |
| **Unauthorized Access Attempts** | ≤ 0 (target), log all | Access control engine |
| **Access Control Violations Detected** | 0 successful | RBAC enforcement logs |
| **Audit Log Retention** | 6 years (HIPAA required) | Log retention system |
| **Encryption Compliance (at rest)** | 100% of PHI records | Encryption monitoring hooks |
| **Encryption Compliance (in transit)** | 100% of API traffic | TLS connection verification |
| **Mean Time to Detect Breach** | < 4 hours | Detection system SLA |

---

## 9. Example JSON Payloads

### 9.1 Complete Patient Encounter

```json
{
  "encounter": {
    "id": "enc-20260615-001",
    "resourceType": "Encounter",
    "status": "finished",
    "class": {
      "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
      "code": "EMEDU",
      "display": "Emergency department"
    },
    "subject": {
      "reference": "Patient/patient-20260615-001"
    },
    "period": {
      "start": "2026-06-15T10:30:00Z",
      "end": "2026-06-15T12:45:00Z"
    }
  },
  "classification": {
    "urgencyLevel": "EMERGENCY",
    "urgencyScore": 0.92,
    "classificationReason": "Chest pain with ST elevation on EKG",
    "recommendedCareLevel": "ICU",
    "clinicalIndicators": [
      {
        "code": "2160-0:LOINC",
        "display": "Oxygen saturation",
        "severity": "HIGH",
        "value": 72
      },
      {
        "code": "85354-0:LOINC",
        "display": "ST elevation",
        "severity": "HIGH",
        "value": true
      },
      {
        "code": "72133-0:LOINC",
        "display": "Pain severity",
        "severity": "HIGH",
        "value": 8
      }
    ]
  },
  "affordability": {
    "affordabilityScore": 0.32,
    "affordabilityCategory": "HIGH_RISK",
    "maxAffordableOutOfPocket": 3200,
    "riskOfBankruptcy": true,
    "subsidyEligibility": [
      {
        "programName": "State Medicaid",
        "eligibilityPercentage": 0.98
      },
      {
        "programName": "Hospital Financial Assistance",
        "eligibilityPercentage": 0.90
      }
    ]
  },
  "subsidy": {
    "subsidyId": "sub-20260615-001",
    "status": "APPROVED",
    "subsidyItems": [
      {
        "itemId": "sub-item-001",
        "serviceCategory": "EMERGENCY",
        "chargedAmount": 85000,
        "insuranceResponsibility": 60000,
        "patientResponsibility": 25000,
        "requestedSubsidyAmount": 25000,
        "approvedSubsidyAmount": 23500,
        "adjustmentReason": "Maximum program cap",
        "status": "APPROVED"
      },
      {
        "itemId": "sub-item-002",
        "serviceCategory": "IMAGING",
        "chargedAmount": 12000,
        "insuranceResponsibility": 10000,
        "patientResponsibility": 2000,
        "requestedSubsidyAmount": 500,
        "approvedSubsidyAmount": 500,
        "adjustmentReason": null,
        "status": "APPROVED"
      }
    ],
    "totalRequestedSubsidy": 25500,
    "totalApprovedSubsidy": 24000,
    "settlementDetails": {
      "settlementDate": "2026-06-20T00:00:00Z",
      "settlementMethod": "BILL_ADJUSTMENT",
      "patientOutOfPocketAfterSubsidy": 5500
    }
  },
  "claim": {
    "claimId": "claim-20260615-001",
    "claimStatus": "SUBMITTED",
    "payerId": "AETNA",
    "totalChargedCents": 852000,
    "lineItems": [
      {
        "lineItemId": "line-001",
        "serviceCode": "99213",
        "serviceDescription": "Emergency service, established patient",
        "hcpcsCode": "99281",
        "chargeDescription": "Emergency department visit",
        "chargedAmount": 450,
        "allowedAmount": 380,
        "insurancePayment": 280,
        "patientResponsibility": 100,
        "subsidy": 0,
        "status": "UNDER_REVIEW"
      },
      {
        "lineItemId": "line-002",
        "serviceCode": "93000",
        "serviceDescription": "Chest cath lab",
        "hcpcsCode": "93451",
        "chargeDescription": "Catheterization",
        "chargedAmount": 15000,
        "allowedAmount": 12000,
        "insurancePayment": 9500,
        "patientResponsibility": 5000,
        "subsidy": 0,
        "status": "UNDER_REVIEW"
      },
      {
        "lineItemId": "line-003",
        "serviceCode": "8857-1:LOINC",
        "serviceDescription": "Troponin I",
        "hcpcsCode": "82293",
        "chargeDescription": "Cardiac marker panel",
        "chargedAmount": 250,
        "allowedAmount": 200,
        "insurancePayment": 180,
        "patientResponsibility": 20,
        "subsidy": 0,
        "status": "APPROVED"
      }
    ],
    "totalInsuranceResponsibility": 11780,
    "totalPatientResponsibility": 5520,
    "totalSubsidyApplied": 5200,
    "denialReasons": [],
    "settlementStatus": "SUBMITTED",
    "daysToSettlement": null
  },
  "cdsCards": [
    {
      "uuid": "cds-001",
      "summary": "Drug-Allergy Interaction: Penicillin",
      "indicator": "CRITICAL",
      "severity": "HIGH",
      "detail": "Patient has documented penicillin allergy. Amoxicillin is contraindicated.",
      "source": {
        "label": "Crisis-Cost Orchestrator CDS",
        "url": "https://ccos.healthcare/patients/20260615",
        "icon": {
          "url": "https://ccos.healthcare/assets/critical.svg",
          "type": "image/svg+xml"
        }
      },
      "language": "https://www.iets.io/languages/en-US",
      "sections": [
        {
          "label": "Allergy Alert",
          "detail": "Penicillin class drugs will harm the patient.",
          "detailMarkdown": "**⚠️ This patient has a penicillin allergy.**\n\nPeanilloylation causes severe hypersensitivity. Avoid all beta-lactams."
        }
      ],
      "suggestions": [
        {
          "label": "Alternative: Cephalexin",
          "id": "sug-001",
          "isRecommended": true,
          "actions": [
            {
              "id": "act-001",
              "type": "create",
              "target": {
                "type": "MedicationRequest",
                "profile": "http://hl7.org/fhir/StructureDefinition/3.0.0/MedicationRequest"
              },
              "selection": [
                {
                  "field": "medicationCodeableConcept",
                  "description": "Select from alternative antibiotics",
                  "options": [
                    {
                      "coding": {
                        "system": "http://www.nlm.nih.gov/id/drug",
                        "code": "4034103",
                        "display": "Cephalexin 500mg"
                      }
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "label": "Use Vancomycin (IV only)",
          "id": "sug-002",
          "isRecommended": false,
          "actions": [
            {
              "id": "act-002",
              "type": "create",
              "target": {
                "type": "MedicationRequest",
                "profile": "http://hl7.org/fhir/StructureDefinition/3.0.0/MedicationRequest"
              },
              "selection": [
                {
                  "field": "medicationCodeableConcept",
                  "description": "Vancomycin for serious MRSA",
                  "options": [
                    {
                      "coding": {
                        "system": "http://www.nlm.nih.gov/id/drug",
                        "code": "1421155",
                        "display": "Vancomycin 1g"
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ],
      "links": [
        {
          "label": "FDA Drug Guide",
          "uri": "https://www.fda.gov/drugs",
          "resourceType": "Url",
          "reference": "https://www.fda.gov/drugs",
          "type": "absolute"
        }
      ]
    }
  ],
  "audit": {
    "events": [
      {
        "eventId": "evt-001",
        "eventType": "ENCOUNTER_RECEIVED",
        "eventTimestamp": "2026-06-15T10:30:00.000Z",
        "actor": {
          "actorType": "SYSTEM",
          "actorId": "api-intake-service-v1.2.3",
          "actorName": "Emergency Registration Service"
        },
        "entity": {
          "entityType": "ENCOUNTER",
          "entityId": "enc-20260615-001",
          "entityDisplay": "Emergency Department - Room 12"
        },
        "action": "CREATE",
        "outcome": "SUCCESS",
        "resultingState": {
          "outcomeCode": "0",
          "message": "Encounter record created successfully"
        },
        "correlationId": "corr-20260615-emerg-001",
        "sourceIpAddress": "10.0.1.50",
        "userAgent": "Crisis-Cost/1.0.0",
        "dataAccessedCount": 2,
        "sensitiveDataAccessed": [],
        "consentStatus": "VALID",
        "encryptionStatus": "ENCRYPTED_AT_REST|ENCRYPTED_IN_TRANSIT",
        "chainVerificationStatus": "VALID",
        "hash": "sha256:a1b2c3d4e5f6..."
      },
      {
        "eventId": "evt-002",
        "eventType": "URGENCY_CLASSIFIED",
        "eventTimestamp": "2026-06-15T10:30:02.500Z",
        "actor": {
          "actorType": "SYSTEM",
          "actorId": "urgency-classifier-model-v2.1.0",
          "actorName": "AI Urgency Classifier"
        },
        "entity": {
          "entityType": "ENCOUNTER",
          "entityId": "enc-20260615-001",
          "entityDisplay": "Emergency Department - Room 12"
        },
        "action": "CLASSIFY",
        "outcome": "SUCCESS",
        "resultingState": {
          "outcomeCode": "0",
          "message": "Classified as EMERGENCY with 0.92 confidence"
        },
        "correlationId": "corr-20260615-emerg-001",
        "sourceIpAddress": "10.0.2.30",
        "userAgent": "UrgencyClassifier/2.1.0",
        "dataAccessedCount": 5,
        "sensitiveDataAccessed": [],
        "consentStatus": "VALID",
        "encryptionStatus": "ENCRYPTED_AT_REST|ENCRYPTED_IN_TRANSIT",
        "chainVerificationStatus": "VALID",
        "hash": "sha256:f6e5d4c3b2a1..."
      },
      {
        "eventId": "evt-003",
        "eventType": "AFFORDABILITY_CALCULATED",
        "eventTimestamp": "2026-06-15T10:35:00.000Z",
        "actor": {
          "actorType": "SYSTEM",
          "actorId": "affordability-calculator-v1.3.0",
          "actorName": "Affordability Engine"
        },
        "entity": {
          "entityType": "PATIENT",
          "entityId": "patient-20260615-001",
          "entityDisplay": "Patient #001"
        },
        "action": "CALCULATE",
        "outcome": "SUCCESS",
        "resultingState": {
          "outcomeCode": "0",
          "message": "Patient classified as HIGH_RISK (score 0.32, bankruptcy risk 100%)"
        },
        "correlationId": "corr-20260615-emerg-001",
        "sourceIpAddress": "10.0.2.30",
        "userAgent": "AffordabilityCalculator/1.3.0",
        "dataAccessedCount": 6,
        "sensitiveDataAccessed": ["FINANCIAL_INFO"],
        "consentStatus": "VALID",
        "encryptionStatus": "ENCRYPTED_AT_REST|ENCRYPTED_IN_TRANSIT",
        "chainVerificationStatus": "VALID",
        "hash": "sha256:1a2b3c4d5e6f..."
      }
    ]
  }
}
```

---

## 10. Versioning

| Version | Date | Changes |
|---|---|---|
| **OKF 1.0.0** | June 2026 | Initial release |
| **FHIR R4 (4.0.1)** | 2024 | FHIR resource integration standard |
| **CDS Hooks 2.0** | 2024 | Standard CDS Hook specifications |

### Version History

| OKF Version | Release Date | Key Changes |
|---|---|---|
| **0.1.0** | Internal, 2024-03 | Initial schema design, core entities |
| **0.2.0** | Internal, 2024-06 | Added CDS Hooks v2.0 integration |
| **0.3.0** | Internal, 2024-09 | Audit chain integrity rules |
| **0.4.0** | Internal, 2025-01 | HIPAA compliance review and additions |
| **0.5.0** | Internal, 2025-06 | FHIR R4 final resource profiles |
| **1.0.0** | June 2026 | Public release, all features complete |

### Semantic Versioning

```
OKF_VERSIONING:
  BREAKING: Major entity schema changes
  FEATURE: New entity types or workflows
  PATCH: Bug fixes and performance improvements
```

---

## 11. References

| Resource | URL | Type |
|---|---|---|
| **HL7 FHIR R4 Specification** | https://www.hl7.org/fhir/R4/ | Standard |
| **FHIR R4.0.1 Release Notes** | https://www.hl7.org/fhir/R4.0.1/ | Standard |
| **CDS Hooks Specification v2.0** | https://cds-hooks.org | Standard |
| **NIST SP 800-38A** (AES) | https://csrc.nist.gov/pubs/sp/800/38/a | Encryption standard |
| **RFC 8446** (TLS 1.3) | https://www.rfc-editor.org/rfc/rfc8446 | Transport security |
| **HIPAA Security Rule** | https://www.hhs.gov/hipaa/for-professionals/security/index.html | Regulation |
| **HIPAA Privacy Rule** | https://www.hhs.gov/hipaa/for-professionals/privacy/index.html | Regulation |
| **42 CFR Part 2** | https://www.law.cornell.edu/cfr/text/42/Chapter-IV-Subchapter-C-Part-2 | Substance use data |
| **ICD-10-CM** | https://www.cdc.gov/nchs/icd/icd10cm.htm | Clinical coding |
| **ICD-10-PCS** | https://www.cdc.gov/nchs/icd/icd10pcs.htm | Procedural coding |
| **LOINC Database** | https://loinc.org | Lab/Observation coding |
| **SNOMED CT Browser** | https://browser.ihtsdotools.org | Clinical terminology |
| **NDC Registry** | https://data.norm.gov | Medication coding |
| **CMS National Provider Registry** | https://data.cms.gov/ | Coverage data |
| **OCR HealthCare.gov API** | https://developer.healthcare.gov | Exchange API |

---

## 12. Contact & Support

| Item | Value |
|---|---|
| **Project** | Crisis-Cost Orchestrator (Healthcare Cost Protection Platform) |
| **Repository** | https://github.com/papajo/healthcare |
| **License** | HIPAA-Compliant, Healthcare-Grade |
| **Maintainer** | Healthcare Engineering Team |
| **HIPAA Compliance Officer** | Contact via repository |
| **Questions / Issues** | Open an issue on GitHub |
| **Documentation** | See referenced standards above |
| **OKF Feedback** | Open an issue tagged `OKF-feedback` |

---

## Appendix A: Urgency Classification Rule Engine

**Decision logic for automated classification:**

```
INPUT: Encounter data (chief complaint, vital signs, labs, history)

STEP 1: Check contraindications (override priority)
  IF critical_lab_values_abnormal THEN
    override = EMERGENCY (regardless of other factors)
  END IF

STEP 2: Check vital sign thresholds
  IF systolic_bp > 180 OR systolic_bp < 90 THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.95+
  ELSE IF heart_rate > 120 OR heart_rate < 40 THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.90+
  ELSE IF respiratory_rate > 30 THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.85+
  ELSE IF o2_saturation < 88 THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.90+
  ELSE IF altered_mental_status THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.92+
  END IF

STEP 3: Check chief complaint patterns
  IF pain_score >= 8 AND pain_location = "chest" THEN
    urgencyLevel = EMERGENCY
    urgencyScore = 0.88+
  ELSE IF pain_score 6-7 AND pain_location = "chest" THEN
    urgencyLevel = URGENT
    urgencyScore = 0.80+
  ELSE IF fever > 103F THEN
    urgencyLevel = URGENT
    urgencyScore = 0.75+
  ELSE IF localized_infection_signs THEN
    urgencyLevel = URGENT
    urgencyScore = 0.70+
  ELSE IF uncontrolled_chronic_condition THEN
    urgencyLevel = URGENT
    urgencyScore = 0.72+
  ELSE IF pain_score 4-5 AND vital_signs_stable THEN
    urgencyLevel = SEMI_URGENT
    urgencyScore = 0.60+
  ELSE IF chief_complaint_in_non_urgent_category THEN
    urgencyLevel = NON_URGENT
    urgencyScore = 0.30+
  ELSE
    urgencyLevel = SEMI_URGENT
    urgencyScore = 0.50 (default)
  END IF

STEP 4: Adjust for patient factors
  IF patient_age < 18 OR patient_age > 80 THEN
    adjust_score (+10%)
  END IF
  IF history_of_cardiac_disease THEN
    adjust_score (+15%)
  END IF
  IF history_of_chronic_pulmonary THEN
    adjust_score (+12%)
  END IF
```

---

## Appendix B: Affordability Threshold Reference Table

| Household Income | Poverty Line | Income/Poverty Ratio | Risk Category | OOP Threshold |
|---|---|---|---|---|
| < $18,060 | $9,030 | < 200% | HIGH_RISK | ≤ 5% income |
| $18,060 – $36,120 | $9,030 | 200–400% | MODERATE_RISK | 3–5% income |
| $36,120 – $72,240 | $9,030 | 400–800% | MODERATE_RISK | 3–5% income |
| $72,240 – $108,360 | $9,030 | 800–1200% | LOW_RISK | ≤ 3% income |
| $108,360+ | $9,030 | > 1200% | LOW_RISK | < 3% income |

---

## Appendix C: Subsidy Program Reference

| Program | Source | Min Income | Max Assistance | Priority |
|---|---|---|---|---|
| **Medicaid (State)** | State Health Dept | Varies by state | Varies by state | 1 |
| **CHIP (State)** | State Health Dept | Income 200–300% FPL | Varies by state | 2 |
| **Hospital Financial Assistance** | Hospital Admin | Income ≤ 300% FPL | Up to 7x net income | 3 |
| **State Charity Care** | State Dept | Income ≤ 400% FPL | Varies by state | 4 |
| **NPO Grants (Local)** | Local Foundation | Varies | Varies | 5 |
| **NPO Grants (National)** | National Org | Income ≤ 400% FPL | Fixed max | 6 |
| **Insurance Payment Gap** | Health Plan | N/A (deductible/max) | Up to out-of-pocket max | 7 |

---

## Appendix D: FHIR Profile Reference URLs

| Resource | Profile URL | Notes |
|---|---|---|
| **Encounter** | `http://fhir.hospital.org/StructureDefinition/encounter-classification` | Extended FHIR Encounter |
| **Patient** | `http://fhir.hospital.org/StructureDefinition/patient-healthcare` | Extended FHIR Patient with enrollment |
| **Observation** | `http://fhir.hospital.org/StructureDefinition/affordability-observation` | Custom affordability observation |
| **Claim** | `http://fhir.hospital.org/StructureDefinition/claim-cost-reconciliation` | Extended FHIR Claim with cost items |
| **MedicationRequest** | `http://fhir.hospital.org/StructureDefinition/medication-request-alt` | Alternative medication alternatives |
| **DiagnosticReport** | `http://fhir.hospital.org/StructureDefinition/urgency-indicator` | Urgency indicator diagnostic |

---

## Appendix E: REST API Contract Summary

| Endpoint | Method | Description | Auth |
|---|---|---|---|
| `/api/v1/encounters` | POST | Create new encounter | Bearer / API Key |
| `/api/v1/encounters/{id}` | GET | Retrieve encounter | Bearer |
| `/api/v1/classify` | POST | Classify encounter urgency | Bearer (limit: 10/min) |
| `/api/v1/affordability` | POST | Assess patient affordability | Bearer |
| `/api/v1/affordability/{patientId}` | GET | Retrieve patient assessment | Bearer |
| `/api/v1/subsidy/programs` | GET | List subsidy programs | Bearer |
| `/api/v1/subsidy/apply` | POST | Apply for subsidy | Bearer |
| `/api/v1/claims` | POST | Submit claim to payer | Bearer (rate limited) |
| `/api/v1/claims/{id}` | GET | Retrieve claim status | Bearer |
| `/api/v1/cds/hooks/patient-view` | POST | CDS hook: patient-view | Bearer (priority token) |
| `/api/v1/audit/events` | GET | Retrieve audit trail | Bearer (admin) |
| `/api/v1/audit/verify` | POST | Verify chain integrity | Bearer (admin) |
| `/api/v1/consent` | POST | Manage patient consent | Bearer (patient) |
| `/api/v1/consent/{id}` | GET/PUT/DELETE | Get/Update/Revoke consent | Bearer |
| `/api/v1/health` | GET | System health check | None |
| `/api/v1/metrics` | GET | Operational metrics | Bearer (admin) |

---

## Appendix F: Deployment Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      API Gateway (TLS 1.3)                    │
└───────────────┬───────────────────────┬──────────────────────┘
                │                       │
    ┌───────────┴──────────┐  ┌─────────┴──────────┐
    │   Classification API  │  │   Financial API     │
    └───────┬──────────────┘  └───────┬────────────┘
            │                        │
    ┌───────┴───────┐     ┌──────────┴──────────┐
    │  Urgency      │     │  Affordability       │
    │  Engine       │     │  Calculator          │
    │  (ML Model)   │     │  (Rules + CREST)     │
    └───────┬───────┘     └───────┬──────────────┘
            │                    │
    ┌───────┴────────────────────────────────────┐
    │            Subsidy Orchestration Engine     │
    │  (Program matching, approval, settlement)   │
    └───────────────┬────────────────────────────┘
                    │
    ┌───────────────┴──────────────────────┐
    │             Insurance Payer API      │
    └───────────────┬──────────────────────┘
                    │
    ┌───────────────┴──────────────────────┐
    │          Blockchain / Chain Storage  │
    │  (Audit trail, imm