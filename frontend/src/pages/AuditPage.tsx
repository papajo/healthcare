/** Audit Log — query and verify audit events */

import { useState, useEffect } from 'react';
import {
  Shield,
  Search,
  Activity,
  CheckCircle,
  AlertTriangle,
  Filter,
  ChevronDown,
  Clock,
  RefreshCw,
} from 'lucide-react';
import { queryAuditEvents, verifyAuditIntegrity } from '../api/client';
import type { AuditEvent } from '../types/api';

const EVENT_TYPE_OPTIONS = [
  'ALL',
  'ENCOUNTER_RECEIVED',
  'URGENCY_CLASSIFIED',
  'AFFORDABILITY_CALCULATED',
  'SUBSIDY_CREATED',
  'SUBSIDY_SETTLED',
  'SUBSIDY_CANCELLED',
  'CLAIM_CREATED',
  'CLAIM_SUBMITTED',
  'CLAIM_SETTLED',
  'CLAIM_VOIDED',
] as const;

const EVENT_TYPE_COLORS: Record<string, string> = {
  ENCOUNTER_RECEIVED:
    'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  URGENCY_CLASSIFIED:
    'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  AFFORDABILITY_CALCULATED:
    'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  SUBSIDY_CREATED:
    'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  SUBSIDY_SETTLED:
    'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  SUBSIDY_CANCELLED:
    'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  CLAIM_CREATED:
    'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
  CLAIM_SUBMITTED:
    'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400',
  CLAIM_SETTLED:
    'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400',
  CLAIM_VOIDED:
    'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
};

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [integrity, setIntegrity] = useState<{
    chain_status: string;
    total_events: number;
    invalid_events: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('ALL');
  const [entityTypeFilter, setEntityTypeFilter] = useState('');
  const [search, setSearch] = useState('');
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params: {
        event_type?: string;
        entity_type?: string;
        limit: number;
      } = { limit: 200 };
      if (eventTypeFilter !== 'ALL') params.event_type = eventTypeFilter;
      if (entityTypeFilter) params.entity_type = entityTypeFilter;

      const [eventsRes, integrityRes] = await Promise.allSettled([
        queryAuditEvents(params),
        verifyAuditIntegrity(),
      ]);

      if (eventsRes.status === 'fulfilled') {
        setEvents(eventsRes.value.events);
        setTotal(eventsRes.value.total);
      }
      if (integrityRes.status === 'fulfilled') {
        setIntegrity(integrityRes.value);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load audit events');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [eventTypeFilter, entityTypeFilter]);

  const filtered = events.filter((event) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      event.event_type.toLowerCase().includes(q) ||
      event.event_id.toLowerCase().includes(q) ||
      (event.entity?.entity_type || event.entity_type || '')
        .toLowerCase()
        .includes(q) ||
      (event.entity?.entity_id || event.entity_id || '')
        .toLowerCase()
        .includes(q) ||
      (event.actor?.actor_type || event.actor_type || '')
        .toLowerCase()
        .includes(q)
    );
  });

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Shield className="h-6 w-6 text-gray-400" aria-hidden="true" />
            Audit Log
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {total} event{total !== 1 ? 's' : ''} recorded
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
        >
          <RefreshCw
            className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`}
            aria-hidden="true"
          />
          Refresh
        </button>
      </div>

      {/* Integrity Banner */}
      {integrity && (
        <div
          className={`flex items-center gap-3 p-4 rounded-xl border ${
            integrity.chain_status === 'VALID'
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
              : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
          }`}
        >
          {integrity.chain_status === 'VALID' ? (
            <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 shrink-0" />
          ) : (
            <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 shrink-0" />
          )}
          <div className="flex-1">
            <p
              className={`text-sm font-medium ${
                integrity.chain_status === 'VALID'
                  ? 'text-green-800 dark:text-green-300'
                  : 'text-yellow-800 dark:text-yellow-300'
              }`}
            >
              Chain integrity:{' '}
              <span className="font-bold">{integrity.chain_status}</span>
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              {integrity.total_events} events verified
              {integrity.invalid_events > 0 &&
                ` — ${integrity.invalid_events} invalid`}
            </p>
          </div>
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
            placeholder="Search events..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 pr-4 py-2 w-full sm:w-72 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            aria-label="Search audit events"
          />
        </div>
        <div className="relative">
          <Filter
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400"
            aria-hidden="true"
          />
          <select
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="pl-10 pr-8 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none appearance-none"
            aria-label="Filter by event type"
          >
            {EVENT_TYPE_OPTIONS.map((t) => (
              <option key={t} value={t}>
                {t === 'ALL' ? 'All Event Types' : t.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
          <ChevronDown
            className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none"
            aria-hidden="true"
          />
        </div>
        <div className="relative">
          <input
            type="text"
            placeholder="Entity type..."
            value={entityTypeFilter}
            onChange={(e) => setEntityTypeFilter(e.target.value)}
            className="pl-4 pr-4 py-2 w-full sm:w-48 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            aria-label="Filter by entity type"
          />
        </div>
        <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
          Showing {filtered.length}
        </div>
      </div>

      {/* Events Table */}
      {error ? (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
          <p className="text-red-700 dark:text-red-400 font-medium">
            Failed to load audit events
          </p>
          <p className="text-sm text-red-500 dark:text-red-400 mt-1">{error}</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
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
                    Correlation
                  </th>
                  <th className="px-4 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Timestamp
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filtered.length === 0 ? (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-6 py-12 text-center text-gray-500 dark:text-gray-400"
                    >
                      {search || eventTypeFilter !== 'ALL' || entityTypeFilter
                        ? 'No events match your filters.'
                        : 'No audit events yet.'}
                    </td>
                  </tr>
                ) : (
                  filtered.map((event) => (
                    <tr
                      key={event.event_id}
                      className="hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer"
                      onClick={() =>
                        setExpandedEvent(
                          expandedEvent === event.event_id
                            ? null
                            : event.event_id
                        )
                      }
                    >
                      <td className="px-4 sm:px-6 py-4">
                        <span
                          className={`inline-block px-2 py-1 rounded text-xs font-medium ${EVENT_TYPE_COLORS[event.event_type] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}`}
                        >
                          {event.event_type.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-4 sm:px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                        <span className="font-medium">
                          {event.entity?.entity_type || event.entity_type}
                        </span>
                        <span className="text-gray-400 dark:text-gray-500 mx-1">
                          :
                        </span>
                        <span className="font-mono text-xs">
                          {(event.entity?.entity_id || event.entity_id || '')
                            .toString()
                            .slice(0, 10)}
                          ...
                        </span>
                      </td>
                      <td className="px-4 sm:px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                        {event.actor?.actor_type || event.actor_type}
                        <span className="text-gray-400 dark:text-gray-500 mx-1">
                          :
                        </span>
                        <span className="font-mono text-xs">
                          {(event.actor?.actor_id || event.actor_id || '')
                            .toString()
                            .slice(0, 8)}
                          ...
                        </span>
                      </td>
                      <td className="px-4 sm:px-6 py-4 text-xs font-mono text-gray-400 dark:text-gray-500">
                        {event.correlation_id
                          ? event.correlation_id.slice(0, 12) + '...'
                          : '—'}
                      </td>
                      <td className="px-4 sm:px-6 py-4 text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">
                        <Clock className="h-3.5 w-3.5 inline mr-1" aria-hidden="true" />
                        {new Date(event.event_timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
