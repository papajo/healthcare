/** Claims Management — full claims list with status filters and summary */

import { useState, useEffect } from 'react';
import {
  Receipt,
  Search,
  Activity,
  DollarSign,
  Filter,
  ChevronDown,
  ExternalLink,
} from 'lucide-react';
import { listClaims, getClaimSummary } from '../api/client';
import type { Claim, ClaimSummary } from '../types/api';

const STATUS_OPTIONS = [
  'ALL',
  'DRAFT',
  'SUBMITTED',
  'UNDER_REVIEW',
  'APPROVED',
  'PARTIAL',
  'DENIED',
  'APPEALED',
  'SETTLED',
  'VOIDED',
] as const;

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  SUBMITTED: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  UNDER_REVIEW:
    'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  APPROVED:
    'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  PARTIAL:
    'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  DENIED: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  APPEALED:
    'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  SETTLED:
    'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  VOIDED:
    'bg-gray-100 text-gray-400 line-through dark:bg-gray-700 dark:text-gray-500',
};

function formatCents(cents: number): string {
  return (cents / 100).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export default function ClaimsPage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [summary, setSummary] = useState<ClaimSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [search, setSearch] = useState('');
  const [total, setTotal] = useState(0);

  useEffect(() => {
    async function load() {
      try {
        const [claimsRes, summaryRes] = await Promise.allSettled([
          listClaims({ limit: 100 }),
          getClaimSummary(),
        ]);
        if (claimsRes.status === 'fulfilled') {
          setClaims(claimsRes.value.claims);
          setTotal(claimsRes.value.total);
        }
        if (summaryRes.status === 'fulfilled') {
          setSummary(summaryRes.value);
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Failed to load claims');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = claims.filter((claim) => {
    const matchesStatus =
      statusFilter === 'ALL' || claim.claim_status === statusFilter;
    if (!search) return matchesStatus;
    const q = search.toLowerCase();
    return (
      matchesStatus &&
      (claim.claim_id.toLowerCase().includes(q) ||
        claim.encounter_id.toLowerCase().includes(q) ||
        claim.payer_id.toLowerCase().includes(q) ||
        claim.patient_pseudo_id.toLowerCase().includes(q))
    );
  });

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-12 w-12 text-blue-600 dark:text-blue-400 animate-spin mx-auto" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading claims...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
          <p className="text-red-700 dark:text-red-400 font-medium">
            Failed to load claims
          </p>
          <p className="text-sm text-red-500 dark:text-red-400 mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Receipt className="h-6 w-6 text-gray-400" aria-hidden="true" />
            Claims
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {total} claim{total !== 1 ? 's' : ''} total
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <SummaryCard
            label="Total Charged"
            value={`$${formatCents(summary.total_charged_cents)}`}
            icon={<DollarSign className="h-5 w-5 text-gray-400" />}
          />
          <SummaryCard
            label="Insurance Owed"
            value={`$${formatCents(summary.total_insurance_responsibility_cents)}`}
            icon={<DollarSign className="h-5 w-5 text-blue-500" />}
            color="text-blue-600 dark:text-blue-400"
          />
          <SummaryCard
            label="Patient Owed"
            value={`$${formatCents(summary.total_patient_responsibility_cents)}`}
            icon={<DollarSign className="h-5 w-5 text-amber-500" />}
            color="text-amber-600 dark:text-amber-400"
          />
          <SummaryCard
            label="Subsidy Applied"
            value={`$${formatCents(summary.total_subsidy_applied_cents)}`}
            icon={<DollarSign className="h-5 w-5 text-green-500" />}
            color="text-green-600 dark:text-green-400"
          />
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400"
            aria-hidden="true"
          />
          <input
            type="text"
            placeholder="Search claims..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 pr-4 py-2 w-full sm:w-72 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            aria-label="Search claims"
          />
        </div>
        <div className="relative">
          <Filter
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400"
            aria-hidden="true"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="pl-10 pr-8 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none appearance-none"
            aria-label="Filter by status"
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s === 'ALL' ? 'All Statuses' : s.replace('_', ' ')}
              </option>
            ))}
          </select>
          <ChevronDown
            className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none"
            aria-hidden="true"
          />
        </div>
        <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
          Showing {filtered.length} of {total}
        </div>
      </div>

      {/* Claims Table */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Claim ID
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
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Items
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filtered.length === 0 ? (
                <tr>
                  <td
                    colSpan={9}
                    className="px-6 py-12 text-center text-gray-500 dark:text-gray-400"
                  >
                    {search || statusFilter !== 'ALL'
                      ? 'No claims match your filters.'
                      : 'No claims yet. Create an encounter to generate claims.'}
                  </td>
                </tr>
              ) : (
                filtered.map((claim) => (
                  <tr
                    key={claim.claim_id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  >
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[claim.claim_status] || 'bg-gray-100 text-gray-700'}`}
                      >
                        {claim.claim_status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-900 dark:text-gray-100">
                      <span className="flex items-center gap-1">
                        {claim.claim_id.slice(0, 12)}...
                        <ExternalLink className="h-3 w-3 text-gray-400" />
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-600 dark:text-gray-400">
                      {claim.encounter_id.slice(0, 12)}...
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
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {claim.line_items.length} item
                      {claim.line_items.length !== 1 ? 's' : ''}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  color?: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center gap-2">{icon}</div>
      <p
        className={`mt-2 text-xl font-bold ${color || 'text-gray-900 dark:text-white'}`}
      >
        {value}
      </p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{label}</p>
    </div>
  );
}
