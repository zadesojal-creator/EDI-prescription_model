import { apiClient, USE_MOCK_API } from './api';

export const adminApi = {
  async getAdminDashboard(): Promise<any> {
    if (USE_MOCK_API) {
      return {
        metrics: {
          total_doctor_reviews: 142,
          confirmed_count: 105,
          corrected_count: 27,
          ood_count: 10,
          verified_samples_collected: 142,
          retraining_threshold: 500
        }
      };
    }
    const res = await apiClient.get('/api/admin/dashboard');
    return res.data;
  },

  async getModelRegistry(): Promise<any> {
    if (USE_MOCK_API) {
      return {
        active_production_version: "v1.0",
        versions: [
          { version: "v1.0", status: "LIVE", accuracy: 83.91, deployed: true, created_at: "2026-08-20" },
          { version: "v0.9", status: "ARCHIVED", accuracy: 81.40, deployed: false, created_at: "2026-08-15" }
        ]
      };
    }
    const res = await apiClient.get('/api/admin/model-registry');
    return res.data;
  }
};
