import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './layouts/AppShell';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

// Auth Pages
import { PharmacistLogin } from './pages/auth/PharmacistLogin';
import { DoctorLogin } from './pages/auth/DoctorLogin';

// Pharmacist Pages
import { PharmacistDashboard } from './pages/pharmacist/PharmacistDashboard';
import { PharmacistScanPage } from './pages/pharmacist/PharmacistScanPage';
import { PharmacistPrescriptionDetail } from './pages/pharmacist/PharmacistPrescriptionDetail';
import { PharmacistNotificationsPage } from './pages/pharmacist/PharmacistNotificationsPage';

// Doctor Pages
import { DashboardPage } from './pages/DashboardPage';
import { PrescriptionScannerPage } from './pages/PrescriptionScannerPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { ReviewWorkspacePage } from './pages/ReviewWorkspacePage';
import { VerifiedHistoryPage } from './pages/VerifiedHistoryPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ModelRegistryPage } from './pages/ModelRegistryPage';
import { DoctorProfilePage } from './pages/DoctorProfilePage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Authentication Routes */}
        <Route path="/pharmacist/login" element={<PharmacistLogin />} />
        <Route path="/doctor/login" element={<DoctorLogin />} />

        {/* Pharmacist Protected Routes */}
        <Route
          path="/pharmacist"
          element={
            <ProtectedRoute requiredRole="PHARMACIST">
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/pharmacist/dashboard" replace />} />
          <Route path="dashboard" element={<PharmacistDashboard />} />
          <Route path="scan" element={<PharmacistScanPage />} />
          <Route path="prescriptions" element={<PharmacistDashboard />} />
          <Route path="prescription/:id" element={<PharmacistPrescriptionDetail />} />
          <Route path="notifications" element={<PharmacistNotificationsPage />} />
          <Route path="medicines" element={<PrescriptionScannerPage />} />
          <Route path="history" element={<VerifiedHistoryPage />} />
          <Route path="profile" element={<DoctorProfilePage />} />
        </Route>

        {/* Doctor Protected Routes */}
        <Route
          path="/doctor"
          element={
            <ProtectedRoute requiredRole="DOCTOR">
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/doctor/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="reviews" element={<ReviewQueuePage />} />
          <Route path="verified" element={<VerifiedHistoryPage />} />
          <Route path="history" element={<VerifiedHistoryPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="models" element={<ModelRegistryPage />} />
          <Route path="profile" element={<DoctorProfilePage />} />
        </Route>

        {/* Universal Direct Review Workspace & Scanner */}
        <Route path="/scan" element={<AppShell />}>
          <Route index element={<PrescriptionScannerPage />} />
        </Route>
        <Route path="/review/:token" element={<ReviewWorkspacePage />} />

        {/* Root Redirect to Pharmacist Login */}
        <Route path="/" element={<Navigate to="/pharmacist/login" replace />} />
        <Route path="*" element={<Navigate to="/pharmacist/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
