/** F-05 Patient Dashboard — Main Page */

import { useState, useEffect } from 'react';
import {
  Activity,
  DollarSign,
  FileText,
  Heart,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Receipt,
  TrendingUp,
} from 'lucide-react';
import {
  getHealth,
  queryAuditEvents,
  verifyAuditIntegrity,
  listClaims,
  getClaimSummary,
} from '../api/client';
import type { HealthStatus, AuditEvent, Claim, ClaimSummary } from '../types/api';

export default function Dashboard() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [integrity, setIntegrity] = useState<{
    chain_status: string;
    total_events: number;
  } | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [claimSummary, setClaimSummary] = useState<ClaimSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const results = await Promise.allSettled([
          getHealth(),
          queryAuditEvents({ limit: 20 }),
          verifyAuditIntegrity(),
          listClaims({ limit: 20 }),
          getClaimSummary(),
        ]);

        if (results[0].status === 'fulfilled') setHealth(results[0].value);
        if (results[1].status === 'fulfilled') setAuditEvents(results[1].value.events);
        if (results[2].status === 'fulfilled') setIntegrity(results[2].value);
        if (results[3].status === 'fulfilled') setClaims(results[3].value.claims);
        if (results[4].status === 'fulfilled') setClaimSummary(results[4].value);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-12 w-12 text-blue-600 animate-spin mx-auto" />
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Crisis-Cost Orchestrator
                </h1>
                <p className="text-sm text-gray-500">
                  Patient Financial Protection Dashboard
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {health?.status === 'healthy' ? (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 text-green-800 text-sm font-medium">
                  <CheckCircle className="h-4 w-4" /> Healthy
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-yellow-100 text-yellow-800 text-sm font-medium">
                  <AlertTriangle className="h-4 w-4" /> Degraded
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* ─── Stats Row ─────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <StatCard
            icon={<Heart className="h-5 w-5 text-red-500" />}
            label="Urgency"
            value="—"
            subtitle="F-01"
          />
          <StatCard
            icon={<DollarSign className="h-5 w-5 text-green-500" />}
            label="Affordability"
            value="—"
            subtitle="F-02"
          />
          <StatCard
            icon={<FileText className="h-5 w-5 text-blue-500" />}
            label="Subsidies"
            value={integrity?.total_events?.toString() ?? '—'}
            subtitle="F-03"
          />
          <StatCard
            icon={<Receipt className="h-5 w-5 text-amber-500" />}
            label="Claims"
            value={claimSummary?.total_claims?.toString() ?? '—'}
            subtitle="Claims"
          />
          <StatCard
            icon={<Shield className="h-5 w-5 text-purple-500" />}
            label="Audit Chain"
            value={integrity?.chain_status ?? '—'}
            subtitle="F-06"
            status={integrity?.chain_status === 'VALID' ? 'ok' : 'warning'}
          />
        </div>

        {/* ─── Claims Section ────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Claims Summary Cards */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">
                Claims Summary
              </h3>
              <div className="space-y-3">
                <SummaryRow
                  label="Total Charged"
                  value={claimSummary?.total_charged_cents ?? 0}
                  color="text-gray-900"
                />
                <SummaryRow
                  label="Insurance Owed"
                  value={claimSummary?.total_insurance_responsibility_cents ?? 0}
                  color="text-blue-600"
                />
                <SummaryRow
                  label="Patient Owed"
                  value={claimSummary?.total_patient_responsibility_cents ?? 0}
                  color="text-amber-600"
                />
                <SummaryRow
                  label="Subsidy Applied"
                  value={claimSummary?.total_subsidy_applied_cents ?? 0}
                  color="text-green-600"
                />
              </div>
            </div>

            {/* Claims by Status */}
            {claimSummary && Object.keys(claimSummary.by_status).length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
                <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">
                  By Status
                </h3>
                <div className="space-y-2">
                  {Object.entries(claimSummary.by_status).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between">
                      <ClaimStatusBadge status={status} />
                      <span className="text-sm font-medium text-gray-700">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Claims Table */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Receipt className="h-5 w-5 text-gray-400" />
                Claims
              </h2>
              <span className="text-sm text-gray-500">
                {claims.length} claim{claims.length !== 1 ? 's' : ''}
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Encounter
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Payer
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Charged
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Patient
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Subsidy
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {claims.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                        No claims yet. Run the demo to create sample claims.
                      </td>
                    </tr>
                  ) : (
                    claims.map((claim) => (
                      <tr key={claim.claim_id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <ClaimStatusBadge status={claim.claim_status} />
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 font-mono">
                          {claim.encounter_id.slice(0, 16)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {claim.payer_id}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                          ${formatCents(claim.total_charged_cents)}
                        </td>
                        <td className="px-4 py-3 text-sm text-amber-600 text-right">
                          ${formatCents(claim.patient_responsibility_cents)}
                        </td>
                        <td className="px-4 py-3 text-sm text-green-600 text-right">
                          ${formatCents(claim.subsidy_applied_cents)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {new Date(claim.service_date).toLocaleDateString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* ─── Audit Events ──────────────────────────────────────────────── */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Clock className="h-5 w-5 text-gray-400" />
              Recent Audit Events
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Event Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Entity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Timestamp
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {auditEvents.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                      No audit events yet.
                    </td>
                  </tr>
                ) : (
                  auditEvents.map((event) => (
                    <tr key={event.event_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <EventTypeBadge type={event.event_type} />
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {event.entity?.entity_type || event.entity_type}:{' '}
                        {(event.entity?.entity_id || event.entity_id || '')
                          .toString()
                          .slice(0, 8)}
                        ...
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {event.actor?.actor_type || event.actor_type}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(event.event_timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* ─── System Status ─────────────────────────────────────────────── */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {health?.services &&
              Object.entries(health.services).map(([name, ok]) => (
                <div
                  key={name}
                  className="flex items-center gap-2 p-3 rounded-lg bg-gray-50"
                >
                  {ok ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  )}
                  <span className="text-sm font-medium text-gray-700 capitalize">
                    {name}
                  </span>
                </div>
              ))}
          </div>
        </div>
      </main>
    </div>
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatCents(cents: number): string {
  return (cents / 100).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function StatCard({
  icon,
  label,
  value,
  subtitle,
  status,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtitle: string;
  status?: 'ok' | 'warning';
}) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-xs font-medium text-gray-500">{label}</span>
      </div>
      <p
        className={`mt-1 text-2xl font-bold ${
          status === 'ok'
            ? 'text-green-600'
            : status === 'warning'
              ? 'text-yellow-600'
              : 'text-gray-900'
        }`}
      >
        {value}
      </p>
      <p className="text-[10px] text-gray-400">{subtitle}</p>
    </div>
  );
}

function SummaryRow({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-600">{label}</span>
      <span className={`text-sm font-semibold ${color}`}>
        ${formatCents(value)}
      </span>
    </div>
  );
}

function ClaimStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    DRAFT: 'bg-gray-100 text-gray-700',
    SUBMITTED: 'bg-blue-100 text-blue-700',
    UNDER_REVIEW: 'bg-yellow-100 text-yellow-700',
    APPROVED: 'bg-green-100 text-green-700',
    PARTIAL: 'bg-orange-100 text-orange-700',
    DENIED: 'bg-red-100 text-red-700',
    APPEALED: 'bg-purple-100 text-purple-700',
    SETTLED: 'bg-emerald-100 text-emerald-700',
    VOIDED: 'bg-gray-100 text-gray-400 line-through',
  };

  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-700'}`}
    >
      {status}
    </span>
  );
}

function EventTypeBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    ENCOUNTER_RECEIVED: 'bg-blue-100 text-blue-800',
    URGENCY_CLASSIFIED: 'bg-orange-100 text-orange-800',
    AFFORDABILITY_CALCULATED: 'bg-green-100 text-green-800',
    SUBSIDY_CREATED: 'bg-purple-100 text-purple-800',
    SUBSIDY_SETTLED: 'bg-emerald-100 text-emerald-800',
    SUBSIDY_CANCELLED: 'bg-red-100 text-red-800',
  };

  return (
    <span
      className={`inline-block px-2 py-1 rounded text-xs font-medium ${colors[type] || 'bg-gray-100 text-gray-800'}`}
    >
      {type}
    </span>
  );
}
