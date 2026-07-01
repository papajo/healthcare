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
} from 'lucide-react';
import {
  getHealth,
  queryAuditEvents,
  verifyAuditIntegrity,
} from '../api/client';
import type { HealthStatus, AuditEvent } from '../types/api';

export default function Dashboard() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [integrity, setIntegrity] = useState<{
    chain_status: string;
    total_events: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [healthRes, auditRes, integrityRes] = await Promise.allSettled([
          getHealth(),
          queryAuditEvents({ limit: 20 }),
          verifyAuditIntegrity(),
        ]);

        if (healthRes.status === 'fulfilled') setHealth(healthRes.value);
        if (auditRes.status === 'fulfilled') setAuditEvents(auditRes.value.events);
        if (integrityRes.status === 'fulfilled') setIntegrity(integrityRes.value);
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

      {/* Stats */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Heart className="h-6 w-6 text-red-500" />}
            label="Urgency Classifications"
            value="—"
            subtitle="F-01"
          />
          <StatCard
            icon={<DollarSign className="h-6 w-6 text-green-500" />}
            label="Affordability Checks"
            value="—"
            subtitle="F-02"
          />
          <StatCard
            icon={<FileText className="h-6 w-6 text-blue-500" />}
            label="Subsidies Processed"
            value={integrity?.total_events?.toString() ?? '—'}
            subtitle="F-03"
          />
          <StatCard
            icon={<Shield className="h-6 w-6 text-purple-500" />}
            label="Audit Chain"
            value={integrity?.chain_status ?? '—'}
            subtitle="F-06"
            status={integrity?.chain_status === 'VALID' ? 'ok' : 'warning'}
          />
        </div>

        {/* Recent Audit Events */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
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
                    <td
                      colSpan={4}
                      className="px-6 py-8 text-center text-gray-500"
                    >
                      No audit events yet. Start an encounter flow to see data.
                    </td>
                  </tr>
                ) : (
                  auditEvents.map((event) => (
                    <tr key={event.event_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <EventTypeBadge type={event.event_type} />
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {event.entity?.entity_type || event.entity_type}: {(event.entity?.entity_id || event.entity_id || '').toString().slice(0, 8)}...
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

        {/* System Status */}
        <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            System Status
          </h2>
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
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-3">
        {icon}
        <span className="text-sm font-medium text-gray-500">{label}</span>
      </div>
      <p
        className={`mt-2 text-3xl font-bold ${
          status === 'ok'
            ? 'text-green-600'
            : status === 'warning'
              ? 'text-yellow-600'
              : 'text-gray-900'
        }`}
      >
        {value}
      </p>
      <p className="mt-1 text-xs text-gray-400">{subtitle}</p>
    </div>
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
