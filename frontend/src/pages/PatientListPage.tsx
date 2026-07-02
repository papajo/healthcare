/** Patient List — FHIR Patient search with card grid */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  Search,
  Activity,
  Calendar,
  Hash,
  User,
  ChevronRight,
  Phone,
} from 'lucide-react';

interface FhirPatient {
  id: string;
  resourceType: 'Patient';
  active?: boolean;
  name?: Array<{ family?: string; given?: string[]; use?: string }>;
  gender?: string;
  birthDate?: string;
  telecom?: Array<{ system?: string; value?: string; use?: string }>;
  address?: Array<{
    line?: string[];
    city?: string;
    state?: string;
    postalCode?: string;
  }>;
  identifier?: Array<{ system?: string; value?: string }>;
}

interface FhirBundle {
  resourceType: 'Bundle';
  total: number;
  entry: Array<{ resource: FhirPatient }>;
}

function formatName(name?: Array<{ family?: string; given?: string[] }>): string {
  if (!name || name.length === 0) return 'Unknown';
  const n = name[0];
  const given = (n.given || []).join(' ');
  return `${n.family || ''}, ${given}`.trim().replace(/^,\s*/, '');
}

function formatDob(dob?: string): string {
  if (!dob) return '—';
  return new Date(dob + 'T00:00:00').toLocaleDateString();
}

function getInitials(name?: Array<{ family?: string; given?: string[] }>): string {
  if (!name || name.length === 0) return '?';
  const n = name[0];
  const g = (n.given || []).map((c) => c[0]).join('');
  const f = n.family?.[0] || '';
  return (g + f).toUpperCase() || '?';
}

function getPhone(
  telecom?: Array<{ system?: string; value?: string }>
): string | undefined {
  if (!telecom) return undefined;
  const phone = telecom.find((t) => t.system === 'phone');
  return phone?.value;
}

function getMrn(
  identifier?: Array<{ system?: string; value?: string }>
): string | undefined {
  if (!identifier) return undefined;
  const mrn = identifier.find((i) => i.system?.includes('mrn'));
  return mrn?.value;
}

export default function PatientListPage() {
  const [patients, setPatients] = useState<FhirPatient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [total, setTotal] = useState(0);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/fhir/Patient?_count=100');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const bundle: FhirBundle = await res.json();
        setPatients(bundle.entry?.map((e) => e.resource) || []);
        setTotal(bundle.total || 0);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Failed to load patients');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = patients.filter((p) => {
    if (!search) return true;
    const q = search.toLowerCase();
    const name = formatName(p.name).toLowerCase();
    const mrn = getMrn(p.identifier)?.toLowerCase() || '';
    return name.includes(q) || mrn.includes(q) || p.id.includes(q);
  });

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-12 w-12 text-blue-600 dark:text-blue-400 animate-spin mx-auto" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading patients...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
          <p className="text-red-700 dark:text-red-400 font-medium">Failed to load patients</p>
          <p className="text-sm text-red-500 dark:text-red-400 mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Users className="h-6 w-6 text-gray-400" aria-hidden="true" />
            Patients
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {total} patient{total !== 1 ? 's' : ''} in system
          </p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
          <input
            type="text"
            placeholder="Search by name or MRN..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 pr-4 py-2 w-full sm:w-72 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            aria-label="Search patients"
          />
        </div>
      </div>

      {/* Patient Grid */}
      {filtered.length === 0 ? (
        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
          <Users className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto" aria-hidden="true" />
          <p className="mt-4 text-gray-500 dark:text-gray-400">
            {search ? 'No patients match your search.' : 'No patients found.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((patient) => (
            <Link
              key={patient.id}
              to={`/patients/${patient.id}`}
              className="group bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600 transition-all"
            >
              <div className="flex items-start gap-4">
                {/* Avatar */}
                <div className="h-12 w-12 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-400 text-sm font-bold shrink-0">
                  {getInitials(patient.name)}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-gray-900 dark:text-white truncate">
                      {formatName(patient.name)}
                    </h3>
                    <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-blue-500 transition-colors shrink-0" aria-hidden="true" />
                  </div>

                  <div className="mt-2 space-y-1">
                    <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                      <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
                      DOB: {formatDob(patient.birthDate)}
                    </div>
                    {getMrn(patient.identifier) && (
                      <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                        <Hash className="h-3.5 w-3.5" aria-hidden="true" />
                        {getMrn(patient.identifier)}
                      </div>
                    )}
                    <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                      <User className="h-3.5 w-3.5" aria-hidden="true" />
                      {patient.gender || 'Unknown'}
                    </div>
                    {getPhone(patient.telecom) && (
                      <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                        <Phone className="h-3.5 w-3.5" aria-hidden="true" />
                        {getPhone(patient.telecom)}
                      </div>
                    )}
                  </div>

                  {/* Status badge */}
                  <div className="mt-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        patient.active !== false
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                      }`}
                    >
                      {patient.active !== false ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
