/** Settings — app configuration and preferences */

import { useState } from 'react';
import {
  Settings,
  Moon,
  Sun,
  Bell,
  Shield,
  Database,
  Globe,
  Save,
  CheckCircle,
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

export default function SettingsPage() {
  const { theme, toggleTheme } = useTheme();
  const [saved, setSaved] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [compactMode, setCompactMode] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Settings className="h-6 w-6 text-gray-400" aria-hidden="true" />
          Settings
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Configure your dashboard preferences
        </p>
      </div>

      {/* Appearance */}
      <Section
        icon={<Moon className="h-5 w-5 text-indigo-500" />}
        title="Appearance"
        description="Customize how the dashboard looks"
      >
        <SettingRow
          label="Theme"
          description="Switch between light and dark mode"
        >
          <button
            onClick={toggleTheme}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            {theme === 'dark' ? (
              <>
                <Moon className="h-4 w-4" aria-hidden="true" /> Dark
              </>
            ) : (
              <>
                <Sun className="h-4 w-4" aria-hidden="true" /> Light
              </>
            )}
          </button>
        </SettingRow>

        <SettingRow
          label="Compact Mode"
          description="Reduce spacing and padding throughout the UI"
        >
          <Toggle
            checked={compactMode}
            onChange={setCompactMode}
            label="Compact mode"
          />
        </SettingRow>
      </Section>

      {/* Notifications */}
      <Section
        icon={<Bell className="h-5 w-5 text-amber-500" />}
        title="Notifications"
        description="Control alert and notification preferences"
      >
        <SettingRow
          label="Clinical Alerts"
          description="Show CDS hook alerts and drug interaction warnings"
        >
          <Toggle
            checked={notifications}
            onChange={setNotifications}
            label="Clinical alerts"
          />
        </SettingRow>

        <SettingRow
          label="Audit Events"
          description="Notify when new audit events are recorded"
        >
          <Toggle checked={false} onChange={() => {}} label="Audit events" />
        </SettingRow>
      </Section>

      {/* Data */}
      <Section
        icon={<Database className="h-5 w-5 text-green-500" />}
        title="Data"
        description="Data refresh and storage settings"
      >
        <SettingRow
          label="Auto-Refresh"
          description="Automatically refresh dashboard data every 30 seconds"
        >
          <Toggle
            checked={autoRefresh}
            onChange={setAutoRefresh}
            label="Auto refresh"
          />
        </SettingRow>

        <SettingRow
          label="FHIR Server"
          description="Base URL for the FHIR R4 backend"
        >
          <span className="text-sm font-mono text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-3 py-1.5 rounded-lg">
            /fhir
          </span>
        </SettingRow>
      </Section>

      {/* Security */}
      <Section
        icon={<Shield className="h-5 w-5 text-red-500" />}
        title="Security"
        description="Authentication and access control"
      >
        <SettingRow
          label="Audit Chain"
          description="Immutable audit trail integrity verification"
        >
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-sm font-medium">
            <CheckCircle className="h-4 w-4" aria-hidden="true" />
            Enabled
          </span>
        </SettingRow>

        <SettingRow
          label="HIPAA Compliance"
          description="Data encryption at rest and in transit"
        >
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-sm font-medium">
            <CheckCircle className="h-4 w-4" aria-hidden="true" />
            Active
          </span>
        </SettingRow>
      </Section>

      {/* About */}
      <Section
        icon={<Globe className="h-5 w-5 text-blue-500" />}
        title="About"
        description="System information"
      >
        <div className="space-y-3">
          <InfoRow label="Version" value="0.1.0" />
          <InfoRow label="Platform" value="Crisis-Cost Orchestrator" />
          <InfoRow label="FHIR Version" value="R4 (4.0.1)" />
          <InfoRow label="CDS Hooks" value="v2.0" />
        </div>
      </Section>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className={`inline-flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
            saved
              ? 'bg-green-600 text-white'
              : 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800'
          }`}
        >
          {saved ? (
            <>
              <CheckCircle className="h-4 w-4" aria-hidden="true" />
              Saved
            </>
          ) : (
            <>
              <Save className="h-4 w-4" aria-hidden="true" />
              Save Preferences
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function Section({
  icon,
  title,
  description,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          {icon}
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {title}
          </h2>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {description}
        </p>
      </div>
      <div className="divide-y divide-gray-200 dark:divide-gray-700">{children}</div>
    </div>
  );
}

function SettingRow({
  label,
  description,
  children,
}: {
  label: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="px-6 py-4 flex items-center justify-between gap-4">
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white">{label}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
          {description}
        </p>
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
      <span className="text-sm font-mono text-gray-900 dark:text-white">{value}</span>
    </div>
  );
}

function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 ${
        checked ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
          checked ? 'translate-x-5' : 'translate-x-0'
        }`}
      />
    </button>
  );
}
