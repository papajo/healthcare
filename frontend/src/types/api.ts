/** Crisis-Cost Orchestrator API types */

export type UrgencyLabel =
  | 'CRITICAL'
  | 'EMERGENT'
  | 'URGENT'
  | 'SEMI-URGENT'
  | 'ROUTINE'
  | 'ELECTIVE'
  | 'NON-URGENT';

export type AffordabilityTier =
  | 'TIER-CRITICAL'
  | 'TIER-LOW'
  | 'TIER-STANDARD'
  | 'TIER-MODERATE'
  | 'TIER-UNVERIFIED';

export type SubsidyStatus =
  | 'PENDING'
  | 'VALIDATING'
  | 'INITIATING_PAYMENT'
  | 'PAYMENT_PROCESSING'
  | 'PAYMENT_SETTLED'
  | 'PAYMENT_FAILED'
  | 'CANCELLED';

export type PaymentMethod = 'ACH' | 'WIRE' | 'STABLECOIN';

export interface Encounter {
  encounter_id: string;
  patient_pseudo_id: string;
  provider_org_id: string;
  encounter_class: string;
  complaint_text: string;
  complaint_code?: string;
  acuity_level?: number;
  clinical_flags?: Record<string, boolean>;
  vitals?: Record<string, number>;
  lab_results?: Record<string, number>;
  medications?: string[];
}

export interface UrgencyClassification {
  urgency_label: UrgencyLabel;
  confidence: number;
  path: 'rule_based' | 'llm';
  evidence: string[];
}

export interface AffordabilityResult {
  encounter_id: string;
  patient_pseudo_id: string;
  estimated_total_cents: number;
  patient_responsibility_cents: number;
  subsidy_amount_cents: number;
  tier_applied: AffordabilityTier;
  urgency_override: boolean;
}

export interface Subsidy {
  subsidy_id: string;
  encounter_id: string;
  patient_pseudo_id: string;
  provider_org_id: string;
  subsidy_amount_cents: number;
  subsidy_status: SubsidyStatus;
  payment_method: PaymentMethod | null;
  payment_reference: string | null;
  created_at: string;
  settled_at: string | null;
  updated_at: string;
}

export interface AuditEvent {
  event_id: string;
  event_type: string;
  event_timestamp: string;
  actor?: { actor_type: string; actor_id: string };
  entity?: { entity_type: string; entity_id: string };
  actor_type?: string;
  actor_id?: string;
  entity_type?: string;
  entity_id?: string;
  payload: Record<string, unknown>;
  correlation_id: string | null;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded';
  services: Record<string, boolean>;
  timestamp: string;
}

export interface EncounterFlow {
  encounter: Encounter;
  urgency: UrgencyClassification;
  affordability: AffordabilityResult;
  subsidy: Subsidy;
  audit_events: AuditEvent[];
}

// ─── Claims ──────────────────────────────────────────────────────────────────

export type ClaimStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'PARTIAL'
  | 'DENIED'
  | 'APPEALED'
  | 'SETTLED'
  | 'VOIDED';

export interface ClaimLineItem {
  line_item_id: string;
  service_code: string;
  description: string;
  quantity: number;
  unit_price_cents: number;
  total_cents: number;
}

export interface Claim {
  claim_id: string;
  encounter_id: string;
  patient_pseudo_id: string;
  provider_org_id: string;
  payer_id: string;
  claim_type: string;
  claim_status: ClaimStatus;
  service_date: string;
  line_items: ClaimLineItem[];
  diagnosis_codes: string[];
  total_charged_cents: number;
  insurance_responsibility_cents: number;
  patient_responsibility_cents: number;
  subsidy_applied_cents: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
  settled_at: string | null;
}

export interface ClaimSummary {
  total_claims: number;
  by_status: Record<string, number>;
  total_charged_cents: number;
  total_insurance_responsibility_cents: number;
  total_patient_responsibility_cents: number;
  total_subsidy_applied_cents: number;
}
