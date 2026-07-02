/** Subsidy Programs — browse and apply for financial assistance */

import { useState, useEffect } from 'react';
import {
  DollarSign,
  Building2,
  Heart,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  ExternalLink,
} from 'lucide-react';
import { listSubsidyPrograms } from '../api/client';
import type { SubsidyProgram } from '../api/client';

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  STATE: <Building2 className="w-5 h-5 text-blue-600" />,
  HOSPITAL: <Heart className="w-5 h-5 text-red-600" />,
  NPO: <DollarSign className="w-5 h-5 text-emerald-600" />,
  INSURANCE: <CheckCircle className="w-5 h-5 text-purple-600" />,
};

const SOURCE_COLORS: Record<string, string> = {
  STATE: 'bg-blue-50 border-blue-200',
  HOSPITAL: 'bg-red-50 border-red-200',
  NPO: 'bg-emerald-50 border-emerald-200',
  INSURANCE: 'bg-purple-50 border-purple-200',
};

export default function SubsidyProgramsPage() {
  const [programs, setPrograms] = useState<SubsidyProgram[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('ALL');

  const loadPrograms = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listSubsidyPrograms(
        filter !== 'ALL' ? { source: filter } : undefined
      );
      setPrograms(data.programs);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load programs'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPrograms();
  }, [filter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Subsidy Programs</h1>
        <p className="text-sm text-gray-500 mt-1">
          Financial assistance programs to prevent medical bankruptcy
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 text-sm">{error}</span>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2">
        {['ALL', 'STATE', 'HOSPITAL', 'NPO', 'INSURANCE'].map((src) => (
          <button
            key={src}
            onClick={() => setFilter(src)}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors ${
              filter === src
                ? 'bg-indigo-600 text-white border-indigo-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            {src === 'ALL' ? 'All Programs' : src}
          </button>
        ))}
      </div>

      {/* Programs Grid */}
      {loading ? (
        <div className="text-center py-12">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-gray-400" />
          <p className="text-gray-500 text-sm">Loading programs...</p>
        </div>
      ) : programs.length === 0 ? (
        <div className="text-center py-12">
          <DollarSign className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-gray-500">No programs found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {programs.map((program) => (
            <div
              key={program.program_id}
              className={`rounded-xl border-2 p-5 hover:shadow-md transition-shadow ${
                SOURCE_COLORS[program.source] || 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  {SOURCE_ICONS[program.source] || (
                    <DollarSign className="w-5 h-5 text-gray-600" />
                  )}
                  <span className="text-xs font-medium text-gray-500 uppercase">
                    {program.source}
                  </span>
                </div>
                <span className="text-xs text-gray-400">
                  Priority #{program.priority}
                </span>
              </div>

              <h3 className="text-base font-semibold text-gray-900 mb-2">
                {program.name}
              </h3>
              <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                {program.description}
              </p>

              <div className="space-y-2 text-xs text-gray-500">
                <div className="flex justify-between">
                  <span>Income Range:</span>
                  <span className="font-medium text-gray-700">
                    {program.min_income_fpl_percent}% –{' '}
                    {program.max_income_fpl_percent}% FPL
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Max Assistance:</span>
                  <span className="font-medium text-emerald-700">
                    ${program.max_assistance_usd.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
