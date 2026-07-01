import { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  User,
  Calendar,
  Hash,
  Activity,
  Pill,
  AlertTriangle,
  FlaskConical,
  Stethoscope,
  Heart,
  Clock,
} from 'lucide-react';

type Tab = 'overview' | 'medications' | 'allergies' | 'labs' | 'conditions';

const tabs: { id: Tab; label: string; icon: typeof Activity }[] = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'medications', label: 'Medications', icon: Pill },
  { id: 'allergies', label: 'Allergies', icon: AlertTriangle },
  { id: 'labs', label: 'Labs', icon: FlaskConical },
  { id: 'conditions', label: 'Conditions', icon: Stethoscope },
];

interface MockPatient {
  name: string;
  dob: string;
  mrn: string;
  status: 'Active' | 'Inactive' | 'Discharged';
  gender: string;
  phone: string;
  insurance: string;
  vitals: { label: string; value: string; unit: string; status: 'normal' | 'high' | 'low' }[];
  encounters: { date: string; type: string; provider: string }[];
  medications: { name: string; dosage: string; frequency: string; prescriber: string; startDate: string }[];
  allergies: { allergen: string; severity: string; reaction: string; status: string }[];
  labs: { test: string; result: string; referenceRange: string; date: string; flag: 'normal' | 'high' | 'low' }[];
  conditions: { name: string; onsetDate: string; status: string; clinicalStatus: string }[];
}

const mockPatient: MockPatient = {
  name: 'Jane Doe',
  dob: '1985-03-15',
  mrn: 'MRN-001234',
  status: 'Active',
  gender: 'Female',
  phone: '(555) 123-4567',
  insurance: 'Blue Cross PPO',
  vitals: [
    { label: 'Blood Pressure', value: '128/82', unit: 'mmHg', status: 'high' },
    { label: 'Heart Rate', value: '72', unit: 'bpm', status: 'normal' },
    { label: 'Temperature', value: '98.6', unit: 'F', status: 'normal' },
    { label: 'SpO2', value: '97', unit: '%', status: 'normal' },
    { label: 'Weight', value: '165', unit: 'lbs', status: 'normal' },
    { label: 'Height', value: "5'6\"", unit: '', status: 'normal' },
  ],
  encounters: [
    { date: '2026-06-28', type: 'Follow-up', provider: 'Dr. Smith' },
    { date: '2026-06-15', type: 'Lab Review', provider: 'Dr. Patel' },
    { date: '2026-05-20', type: 'Annual Physical', provider: 'Dr. Smith' },
  ],
  medications: [
    { name: 'Lisinopril', dosage: '10mg', frequency: 'Once daily', prescriber: 'Dr. Smith', startDate: '2025-01-10' },
    { name: 'Metformin', dosage: '500mg', frequency: 'Twice daily', prescriber: 'Dr. Patel', startDate: '2025-06-01' },
    { name: 'Atorvastatin', dosage: '20mg', frequency: 'Once daily at bedtime', prescriber: 'Dr. Smith', startDate: '2024-11-15' },
    { name: 'Omeprazole', dosage: '20mg', frequency: 'Once daily before breakfast', prescriber: 'Dr. Garcia', startDate: '2026-03-01' },
  ],
  allergies: [
    { allergen: 'Penicillin', severity: 'Severe', reaction: 'Anaphylaxis', status: 'Active' },
    { allergen: 'Sulfa drugs', severity: 'Moderate', reaction: 'Rash, hives', status: 'Active' },
    { allergen: 'Latex', severity: 'Mild', reaction: 'Contact dermatitis', status: 'Active' },
  ],
  labs: [
    { test: 'Hemoglobin A1c', result: '7.2%', referenceRange: '< 7.0%', date: '2026-06-15', flag: 'high' },
    { test: 'Fasting Glucose', result: '142 mg/dL', referenceRange: '70-100 mg/dL', date: '2026-06-15', flag: 'high' },
    { test: 'Total Cholesterol', result: '198 mg/dL', referenceRange: '< 200 mg/dL', date: '2026-06-15', flag: 'normal' },
    { test: 'LDL Cholesterol', result: '118 mg/dL', referenceRange: '< 100 mg/dL', date: '2026-06-15', flag: 'high' },
    { test: 'HDL Cholesterol', result: '52 mg/dL', referenceRange: '> 40 mg/dL', date: '2026-06-15', flag: 'normal' },
    { test: 'Creatinine', result: '0.9 mg/dL', referenceRange: '0.6-1.2 mg/dL', date: '2026-06-15', flag: 'normal' },
    { test: 'TSH', result: '2.1 mIU/L', referenceRange: '0.4-4.0 mIU/L', date: '2026-05-20', flag: 'normal' },
    { test: 'WBC', result: '4.8 K/uL', referenceRange: '4.5-11.0 K/uL', date: '2026-05-20', flag: 'normal' },
  ],
  conditions: [
    { name: 'Type 2 Diabetes Mellitus', onsetDate: '2023-08-15', status: 'Active', clinicalStatus: 'Uncontrolled' },
    { name: 'Essential Hypertension', onsetDate: '2022-03-10', status: 'Active', clinicalStatus: 'Controlled' },
    { name: 'Hyperlipidemia', onsetDate: '2024-11-01', status: 'Active', clinicalStatus: 'Controlled' },
    { name: 'Gastroesophageal Reflux', onsetDate: '2026-02-20', status: 'Active', clinicalStatus: 'Improved' },
  ],
};

const statusColors: Record<string, string> = {
  Active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  Inactive: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  Discharged: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
};

const flagColors: Record<string, string> = {
  normal: 'text-green-600 dark:text-green-400',
  high: 'text-red-600 dark:text-red-400',
  low: 'text-amber-600 dark:text-amber-400',
};

const flagBadge: Record<string, string> = {
  normal: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  high: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  low: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
};

const severityColors: Record<string, string> = {
  Severe: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  Moderate: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  Mild: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
};

export default function PatientChart() {
  useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const patient = mockPatient;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Patient Header */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="h-14 w-14 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-400 text-xl font-bold shrink-0">
            {patient.name.split(' ').map((n) => n[0]).join('')}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">{patient.name}</h2>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium w-fit ${statusColors[patient.status]}`}>
                {patient.status}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" aria-hidden="true" />
                DOB: {new Date(patient.dob).toLocaleDateString()}
              </span>
              <span className="flex items-center gap-1">
                <Hash className="h-4 w-4" aria-hidden="true" />
                {patient.mrn}
              </span>
              <span className="flex items-center gap-1">
                <User className="h-4 w-4" aria-hidden="true" />
                {patient.gender}
              </span>
            </div>
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400 space-y-1">
            <p>Insurance: {patient.insurance}</p>
            <p>Phone: {patient.phone}</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
        <nav className="flex gap-0 min-w-max" role="tablist" aria-label="Patient chart sections">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              aria-controls={`panel-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors min-h-[44px] whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <tab.icon className="h-4 w-4" aria-hidden="true" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Panels */}
      <div id={`panel-${activeTab}`} role="tabpanel" aria-labelledby={activeTab}>
        {activeTab === 'overview' && <OverviewTab patient={patient} />}
        {activeTab === 'medications' && <MedicationsTab patient={patient} />}
        {activeTab === 'allergies' && <AllergiesTab patient={patient} />}
        {activeTab === 'labs' && <LabsTab patient={patient} />}
        {activeTab === 'conditions' && <ConditionsTab patient={patient} />}
      </div>
    </div>
  );
}

function OverviewTab({ patient }: { patient: MockPatient }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Vitals */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-4 flex items-center gap-2">
          <Heart className="h-4 w-4" aria-hidden="true" />
          Vitals
        </h3>
        <div className="space-y-3">
          {patient.vitals.map((vital) => (
            <div key={vital.label} className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">{vital.label}</span>
              <span className={`text-sm font-semibold ${flagColors[vital.status]}`}>
                {vital.value}{vital.unit ? ` ${vital.unit}` : ''}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Encounters */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-4 flex items-center gap-2">
          <Clock className="h-4 w-4" aria-hidden="true" />
          Recent Encounters
        </h3>
        <div className="space-y-3">
          {patient.encounters.map((enc, i) => (
            <div key={i} className="border-l-2 border-blue-200 dark:border-blue-800 pl-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">{enc.type}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {enc.provider} &middot; {new Date(enc.date).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Active Medications Count */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-4 flex items-center gap-2">
          <Pill className="h-4 w-4" aria-hidden="true" />
          Active Medications
        </h3>
        <div className="text-center py-4">
          <span className="text-4xl font-bold text-blue-600 dark:text-blue-400">
            {patient.medications.length}
          </span>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">medications active</p>
        </div>
        <div className="space-y-2 mt-4">
          {patient.medications.slice(0, 3).map((med) => (
            <div key={med.name} className="text-sm text-gray-600 dark:text-gray-400">
              {med.name} <span className="text-gray-400 dark:text-gray-500">&middot;</span> {med.dosage}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function MedicationsTab({ patient }: { patient: MockPatient }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Medication</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Dosage</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Frequency</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Prescriber</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Start Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {patient.medications.map((med) => (
              <tr key={med.name} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{med.name}</td>
                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{med.dosage}</td>
                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{med.frequency}</td>
                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{med.prescriber}</td>
                <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  {new Date(med.startDate).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AllergiesTab({ patient }: { patient: MockPatient }) {
  return (
    <div className="space-y-4">
      {patient.allergies.map((allergy) => (
        <div
          key={allergy.allergen}
          className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5"
        >
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold text-gray-900 dark:text-white">{allergy.allergen}</h3>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${severityColors[allergy.severity] || ''}`}>
                  {allergy.severity}
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Reaction: {allergy.reaction}</p>
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400">{allergy.status}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function LabsTab({ patient }: { patient: MockPatient }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Test</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Result</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Reference Range</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Date</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Flag</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {patient.labs.map((lab) => (
              <tr key={lab.test} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{lab.test}</td>
                <td className={`px-4 py-3 text-sm font-semibold ${flagColors[lab.flag]}`}>{lab.result}</td>
                <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{lab.referenceRange}</td>
                <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  {new Date(lab.date).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${flagBadge[lab.flag]}`}>
                    {lab.flag === 'normal' ? 'Normal' : lab.flag === 'high' ? 'High' : 'Low'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ConditionsTab({ patient }: { patient: MockPatient }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Condition</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Onset Date</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Clinical Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {patient.conditions.map((cond) => (
              <tr key={cond.name} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{cond.name}</td>
                <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  {new Date(cond.onsetDate).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${statusColors[cond.status] || ''}`}>
                    {cond.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{cond.clinicalStatus}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
