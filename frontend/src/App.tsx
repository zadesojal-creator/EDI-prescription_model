import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './layouts/AppShell';
import { DashboardPage } from './pages/DashboardPage';
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
        <Route path="/" element={<AppShell />}>
          <Route index element={<Navigate to="/doctor/dashboard" replace />} />
          <Route path="doctor/dashboard" element={<DashboardPage />} />
          <Route path="doctor/reviews" element={<ReviewQueuePage />} />
          <Route path="doctor/verified" element={<VerifiedHistoryPage />} />
          <Route path="doctor/history" element={<VerifiedHistoryPage />} />
          <Route path="doctor/analytics" element={<AnalyticsPage />} />
          <Route path="doctor/models" element={<ModelRegistryPage />} />
          <Route path="doctor/profile" element={<DoctorProfilePage />} />
        </Route>
        {/* Direct Token Review Workspace Route */}
        <Route path="review/:token" element={<ReviewWorkspacePage />} />
        <Route path="*" element={<Navigate to="/doctor/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
