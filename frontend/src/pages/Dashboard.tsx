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
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-12 w-12 text-blue-600 dark:text-blue-400 animate-spin mx-auto" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Health Status Banner */}
      <div className="flex items-center justify-end">
        {health?.status === 'healthy' ? (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 text-sm font-medium">
            <CheckCircle className="h-4 w-4" aria-hidden="true" /> Healthy
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400 text-sm font-medium">
            <AlertTriangle className="h-4 w-4" aria-hidden="true" /> Degraded
          </span>
        )}
      </div>

      {/* ─── Stats Row ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
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
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Claims Summary Cards */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-3">
              Claims Summary
            </h3>
            <div className="space-y-3">
              <SummaryRow
                label="Total Charged"
                value={claimSummary?.total_charged_cents ?? 0}
                color="text-gray-900 dark:text-white"
              />
              <SummaryRow
                label="Insurance Owed"
                value={claimSummary?.total_insurance_responsibility_cents ?? 0}
                color="text-blue-600 dark:text-blue-400"
              />
              <SummaryRow
                label="Patient Owed"
                value={claimSummary?.total_patient_responsibility_cents ?? 0}
                color="text-amber-600 dark:text-amber-400"
              />
              <SummaryRow
                label="Subsidy Applied"
                value={claimSummary?.total_subsidy_applied_cents ?? 0}
                color="text-green-600 dark:text-green-400"
              />
            </div>
          </div>

          {/* Claims by Status */}
          {claimSummary && Object.keys(claimSummary.by_status).length > 0 && (
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-3">
                By Status
              </h3>
              <div className="space-y-2">
                {Object.entries(claimSummary.by_status).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between">
                    <ClaimStatusBadge status={status} />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Claims Table */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-4 sm:px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Receipt className="h-5 w-5 text-gray-400" aria-hidden="true" />
              Claims
            </h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {claims.length} claim{claims.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Encounter
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Payer
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Charged
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Patient
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Subsidy
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {claims.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                      No claims yet. Run the demo to create sample claims.
                    </td>
                  </tr>
                ) : (
                  claims.map((claim) => (
                    <tr key={claim.claim_id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <td className="px-4 py-3">
                        <ClaimStatusBadge status={claim.claim_status} />
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 font-mono">
                        {claim.encounter_id.slice(0, 16)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                        {claim.payer_id}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-white text-right font-medium">
                        ${formatCents(claim.total_charged_cents)}
                      </td>
                      <td className="px-4 py-3 text-sm text-amber-600 dark:text-amber-400 text-right">
                        ${formatCents(claim.patient_responsibility_cents)}
                      </td>
                      <td className="px-4 py-3 text-sm text-green-600 dark:text-green-400 text-right">
                        ${formatCents(claim.subsidy_applied_cents)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
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
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="px-4 sm:px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Clock className="h-5 w-5 text-gray-400" aria-hidden="true" />
            Recent Audit Events
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-4 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Event Type
                </th>
                <th className="px-4 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Entity
                </th>
                <th className="px-4 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Actor
                </th>
                <th className="px-4 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Timestamp
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {auditEvents.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                    No audit events yet.
                  </td>
                </tr>
              ) : (
                auditEvents.map((event) => (
                  <tr key={event.event_id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-4 sm:px-6 py-4">
                      <EventTypeBadge type={event.event_type} />
                    </td>
                    <td className="px-4 sm:px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                      {event.entity?.entity_type || event.entity_type}:{' '}
                      {(event.entity?.entity_id || event.entity_id || '')
                        .toString()
                        .slice(0, 8)}
                      ...
                    </td>
                    <td className="px-4 sm:px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                      {event.actor?.actor_type || event.actor_type}
                    </td>
                    <td className="px-4 sm:px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
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
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">System Status</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {health?.services &&
            Object.entries(health.services).map(([name, ok]) => (
              <div
                key={name}
                className="flex items-center gap-2 p-3 rounded-lg bg-gray-50 dark:bg-gray-800"
              >
                {ok ? (
                  <CheckCircle className="h-4 w-4 text-green-500" aria-hidden="true" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-yellow-500" aria-hidden="true" />
                )}
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                  {name}
                </span>
              </div>
            ))}
        </div>
      </div>
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
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">{label}</span>
      </div>
      <p
        className={`mt-1 text-2xl font-bold ${
          status === 'ok'
            ? 'text-green-600 dark:text-green-400'
            : status === 'warning'
              ? 'text-yellow-600 dark:text-yellow-400'
              : 'text-gray-900 dark:text-white'
        }`}
      >
        {value}
      </p>
      <p className="text-[10px] text-gray-400 dark:text-gray-500">{subtitle}</p>
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
      <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
      <span className={`text-sm font-semibold ${color}`}>
        ${formatCents(value)}
      </span>
    </div>
  );
}

function ClaimStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    DRAFT: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    SUBMITTED: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    UNDER_REVIEW: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    APPROVED: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    PARTIAL: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    DENIED: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    APPEALED: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    SETTLED: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    VOIDED: 'bg-gray-100 text-gray-400 line-through dark:bg-gray-700 dark:text-gray-500',
  };

  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}
    >
      {status}
    </span>
  );
}

function EventTypeBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    ENCOUNTER_RECEIVED: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    URGENCY_CLASSIFIED: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
    AFFORDABILITY_CALCULATED: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    SUBSIDY_CREATED: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
    SUBSIDY_SETTLED: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
    SUBSIDY_CANCELLED: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  };

  return (
    <span
      className={`inline-block px-2 py-1 rounded text-xs font-medium ${colors[type] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}`}
    >
      {type}
    </span>
  );
}
