import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import PatientChart from './pages/PatientChart';

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/patients" element={<PatientListPage />} />
            <Route path="/patients/:id" element={<PatientChart />} />
            <Route path="/claims" element={<ClaimsPage />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}

function PatientListPage() {
  return (
    <div className="max-w-6xl mx-auto">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Patients</h2>
      <p className="text-gray-500 dark:text-gray-400">Patient list coming soon. Use /patients/:id to view a patient chart.</p>
    </div>
  );
}

function ClaimsPage() {
  return (
    <div className="max-w-6xl mx-auto">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Claims</h2>
      <p className="text-gray-500 dark:text-gray-400">Claims management coming soon.</p>
    </div>
  );
}

function AuditPage() {
  return (
    <div className="max-w-6xl mx-auto">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Audit Log</h2>
      <p className="text-gray-500 dark:text-gray-400">Audit log coming soon.</p>
    </div>
  );
}

function SettingsPage() {
  return (
    <div className="max-w-6xl mx-auto">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Settings</h2>
      <p className="text-gray-500 dark:text-gray-400">Settings coming soon.</p>
    </div>
  );
}
