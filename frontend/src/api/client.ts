/** API client for Crisis-Cost Orchestrator backend */

import type {
  Encounter,
  UrgencyClassification,
  AffordabilityResult,
  Subsidy,
  AuditEvent,
  HealthStatus,
  Claim,
  ClaimSummary,
} from '../types/api';

const API_BASE = '/v1';

function getAuthToken(): string | null {
  return localStorage.getItem('cco_access_token');
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ─── Health ──────────────────────────────────────────────────────────────────

export async function getHealth(): Promise<HealthStatus> {
  return fetchJson<HealthStatus>('/health');
}

export async function getReadiness(): Promise<HealthStatus> {
  return fetchJson<HealthStatus>('/ready');
}

// ─── Urgency (F-01) ─────────────────────────────────────────────────────────

export async function classifyUrgency(
  encounter: Encounter
): Promise<UrgencyClassification> {
  return fetchJson<UrgencyClassification>(`${API_BASE}/urgency/classify`, {
    method: 'POST',
    body: JSON.stringify(encounter),
  });
}

// ─── Affordability (F-02) ───────────────────────────────────────────────────

export async function calculateAffordability(params: {
  encounter_id: string;
  patient_pseudo_id: string;
  urgency_label: string;
  estimated_total_cents: number;
  encounter_class: string;
  eligibility_proof?: Record<string, unknown>;
}): Promise<AffordabilityResult> {
  return fetchJson<AffordabilityResult>(
    `${API_BASE}/affordability/calculate`,
    {
      method: 'POST',
      body: JSON.stringify(params),
    }
  );
}

// ─── Subsidies (F-03) ───────────────────────────────────────────────────────

export async function createSubsidy(params: {
  encounter_id: string;
  patient_pseudo_id: string;
  provider_org_id: string;
  subsidy_amount_cents: number;
}): Promise<Subsidy> {
  return fetchJson<Subsidy>(`${API_BASE}/subsidies`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getSubsidy(subsidyId: string): Promise<Subsidy> {
  return fetchJson<Subsidy>(`${API_BASE}/subsidies/${subsidyId}`);
}

export async function settleSubsidy(subsidyId: string): Promise<Subsidy> {
  return fetchJson<Subsidy>(`${API_BASE}/subsidies/${subsidyId}/settle`, {
    method: 'POST',
  });
}

export async function cancelSubsidy(
  subsidyId: string,
  reason: string
): Promise<Subsidy> {
  return fetchJson<Subsidy>(
    `${API_BASE}/subsidies/${subsidyId}/cancel?reason=${encodeURIComponent(reason)}`,
    { method: 'POST' }
  );
}

// ─── Audit (F-06) ───────────────────────────────────────────────────────────

export async function queryAuditEvents(params?: {
  event_type?: string;
  entity_type?: string;
  entity_id?: string;
  limit?: number;
}): Promise<{ total: number; events: AuditEvent[] }> {
  const query = new URLSearchParams();
  if (params?.event_type) query.set('event_type', params.event_type);
  if (params?.entity_type) query.set('entity_type', params.entity_type);
  if (params?.entity_id) query.set('entity_id', params.entity_id);
  if (params?.limit) query.set('limit', String(params.limit));

  return fetchJson(`${API_BASE}/audit/events?${query.toString()}`);
}

export async function verifyAuditIntegrity(): Promise<{
  chain_status: string;
  total_events: number;
  invalid_events: number;
}> {
  return fetchJson(`${API_BASE}/audit/verify`);
}

// ─── Claims ──────────────────────────────────────────────────────────────────

export async function listClaims(params?: {
  patient_pseudo_id?: string;
  claim_status?: string;
  limit?: number;
}): Promise<{ total: number; claims: Claim[] }> {
  const query = new URLSearchParams();
  if (params?.patient_pseudo_id) query.set('patient_pseudo_id', params.patient_pseudo_id);
  if (params?.claim_status) query.set('claim_status', params.claim_status);
  if (params?.limit) query.set('limit', String(params.limit));

  return fetchJson(`${API_BASE}/claims?${query.toString()}`);
}

export async function getClaim(claimId: string): Promise<Claim> {
  return fetchJson<Claim>(`${API_BASE}/claims/${claimId}`);
}

export async function getClaimSummary(): Promise<ClaimSummary> {
  return fetchJson<ClaimSummary>(`${API_BASE}/claims/summary`);
}

export async function createClaim(params: {
  encounter_id: string;
  patient_pseudo_id: string;
  provider_org_id: string;
  payer_id: string;
  service_date: string;
  line_items: Array<{
    line_item_id: string;
    service_code: string;
    description: string;
    quantity: number;
    unit_price_cents: number;
    total_cents: number;
  }>;
  diagnosis_codes: string[];
}): Promise<Claim> {
  return fetchJson<Claim>(`${API_BASE}/claims`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function submitClaim(claimId: string): Promise<Claim> {
  return fetchJson<Claim>(`${API_BASE}/claims/${claimId}/submit`, {
    method: 'POST',
  });
}

export async function settleClaim(claimId: string): Promise<Claim> {
  return fetchJson<Claim>(`${API_BASE}/claims/${claimId}/settle`, {
    method: 'POST',
  });
}

export async function voidClaim(claimId: string): Promise<Claim> {
  return fetchJson<Claim>(`${API_BASE}/claims/${claimId}/void`, {
    method: 'POST',
  });
}

// ─── Consent ─────────────────────────────────────────────────────────────────

export interface ConsentRecord {
  consent_id: string;
  patient_id: string;
  category: string;
  status: string;
  granted_to: string[];
  granted_by: string;
  created_at: string;
  expires_at: string | null;
  revoked_at: string | null;
  scope_note: string | null;
}

export async function listConsents(params?: {
  patient_id?: string;
  category?: string;
  include_expired?: boolean;
}): Promise<ConsentRecord[]> {
  const query = new URLSearchParams();
  if (params?.patient_id) query.set('patient_id', params.patient_id);
  if (params?.category) query.set('category', params.category);
  if (params?.include_expired) query.set('include_expired', 'true');

  return fetchJson<ConsentRecord[]>(
    `${API_BASE}/consent?${query.toString()}`
  );
}

export async function grantConsent(params: {
  patient_id: string;
  category: string;
  granted_to?: string[];
  expires_at?: string;
}): Promise<ConsentRecord> {
  return fetchJson<ConsentRecord>(`${API_BASE}/consent`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function revokeConsent(
  consentId: string,
  reason?: string
): Promise<ConsentRecord> {
  return fetchJson<ConsentRecord>(
    `${API_BASE}/consent/${consentId}/revoke`,
    {
      method: 'POST',
      body: JSON.stringify({ reason: reason || 'User revoked' }),
    }
  );
}

export async function checkConsent(params: {
  patient_id: string;
  category: string;
  actor_id?: string;
}): Promise<{ consent_valid: boolean }> {
  const query = new URLSearchParams();
  query.set('patient_id', params.patient_id);
  query.set('category', params.category);
  if (params.actor_id) query.set('actor_id', params.actor_id);

  return fetchJson<{ consent_valid: boolean }>(
    `${API_BASE}/consent/check?${query.toString()}`
  );
}

// ─── Subsidy Programs ───────────────────────────────────────────────────────

export interface SubsidyProgram {
  program_id: string;
  name: string;
  source: string;
  min_income_fpl_percent: number;
  max_income_fpl_percent: number;
  max_assistance_usd: number;
  priority: number;
  description: string;
}

export async function listSubsidyPrograms(params?: {
  source?: string;
}): Promise<{ programs: SubsidyProgram[]; total: number }> {
  const query = new URLSearchParams();
  if (params?.source) query.set('source', params.source);

  return fetchJson<{ programs: SubsidyProgram[]; total: number }>(
    `${API_BASE}/subsidies/programs?${query.toString()}`
  );
}

// ─── Metrics ─────────────────────────────────────────────────────────────────

export async function getMetrics(): Promise<{
  audit_events_total: number;
  fhir_resources: Record<string, number>;
  timestamp: string;
}> {
  return fetchJson('/v1/metrics');
}
