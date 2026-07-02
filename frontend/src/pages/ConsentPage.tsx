/** Consent Management — granular patient consent for data categories */

import { useState, useEffect } from 'react';
import {
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  Plus,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import {
  listConsents,
  grantConsent,
  revokeConsent,
} from '../api/client';
import type { ConsentRecord } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const CATEGORIES = [
  'CLINICAL',
  'FINANCIAL',
  'PHARMACY',
  'LAB_RESULTS',
  'IMAGING',
  'MENTAL_HEALTH',
  'SUBSTANCE_USE',
] as const;

const CATEGORY_LABELS: Record<string, string> = {
  CLINICAL: 'Clinical Data',
  FINANCIAL: 'Financial Information',
  PHARMACY: 'Pharmacy Records',
  LAB_RESULTS: 'Lab Results',
  IMAGING: 'Imaging Results',
  MENTAL_HEALTH: 'Mental Health Records',
  SUBSTANCE_USE: 'Substance Use Records',
};

const STATUS_COLORS: Record<string, string> = {
  VALID: 'text-emerald-600 bg-emerald-50',
  EXPIRED: 'text-amber-600 bg-amber-50',
  REVOKED: 'text-red-600 bg-red-50',
};

export default function ConsentPage() {
  const { user } = useAuth();
  const [consents, setConsents] = useState<ConsentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showGrant, setShowGrant] = useState(false);
  const [grantForm, setGrantForm] = useState({
    patient_id: user?.fhir_patient_id || '',
    category: 'CLINICAL',
    scope_note: '',
  });
  const [granting, setGranting] = useState(false);

  const loadConsents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listConsents();
      setConsents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load consents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConsents();
  }, []);

  const handleGrant = async () => {
    setGranting(true);
    try {
      await grantConsent({
        patient_id: grantForm.patient_id,
        category: grantForm.category,
      });
      setShowGrant(false);
      setGrantForm({ patient_id: user?.fhir_patient_id || '', category: 'CLINICAL', scope_note: '' });
      loadConsents();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to grant consent');
    } finally {
      setGranting(false);
    }
  };

  const handleRevoke = async (consentId: string) => {
    try {
      await revokeConsent(consentId, 'User revoked via dashboard');
      loadConsents();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke consent');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Consent Management</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage data access permissions for patient records
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadConsents}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowGrant(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            <Plus className="w-4 h-4" />
            Grant Consent
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500" />
          <span className="text-red-700 text-sm">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Grant Modal */}
      {showGrant && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Grant Consent
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Patient ID
                </label>
                <input
                  type="text"
                  value={grantForm.patient_id}
                  onChange={(e) =>
                    setGrantForm({ ...grantForm, patient_id: e.target.value })
                  }
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="patient-001"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Data Category
                </label>
                <select
                  value={grantForm.category}
                  onChange={(e) =>
                    setGrantForm({ ...grantForm, category: e.target.value })
                  }
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {CATEGORY_LABELS[cat]}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowGrant(false)}
                className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleGrant}
                disabled={granting || !grantForm.patient_id}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {granting ? 'Granting...' : 'Grant'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Consent List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-900">
            Active Consents ({consents.filter((c) => c.status === 'VALID').length})
          </h2>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
            Loading consents...
          </div>
        ) : consents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Shield className="w-10 h-10 mx-auto mb-3 text-gray-300" />
            <p>No consent records found</p>
            <p className="text-xs mt-1">Grant consent to allow data access</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {consents.map((consent) => (
              <div
                key={consent.consent_id}
                className="px-6 py-4 flex items-center justify-between hover:bg-gray-50"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                    <Shield className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900">
                        {CATEGORY_LABELS[consent.category] || consent.category}
                      </span>
                      <span
                        className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                          STATUS_COLORS[consent.status] || 'text-gray-600 bg-gray-50'
                        }`}
                      >
                        {consent.status}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      Patient: {consent.patient_id} | Granted by: {consent.granted_by}
                    </div>
                    {consent.scope_note && (
                      <div className="text-xs text-gray-400 mt-0.5">
                        Note: {consent.scope_note}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400">
                    {new Date(consent.created_at).toLocaleDateString()}
                  </span>
                  {consent.status === 'VALID' && (
                    <button
                      onClick={() => handleRevoke(consent.consent_id)}
                      className="px-3 py-1.5 text-xs font-medium text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
                    >
                      Revoke
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
