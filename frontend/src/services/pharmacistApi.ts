import { apiClient, USE_MOCK_API } from './api';

export const pharmacistApi = {
  async getDashboard(): Promise<any> {
    if (USE_MOCK_API) {
      return {
        scanned_today: 42,
        processing: 3,
        needs_review: 7,
        doctor_review_count: 4,
        verified_count: 28,
        recent_scans: [
          { prescription_id: "rx_81088bcc", lines: 5, confidence: 0.362, status: "DOCTOR_REVIEW", created_at: "12:30" },
          { prescription_id: "rx_1234abcd", lines: 4, confidence: 0.938, status: "VERIFIED", created_at: "12:15" },
          { prescription_id: "rx_90214a", lines: 3, confidence: 0.784, status: "NEEDS_REVIEW", created_at: "11:45" }
        ]
      };
    }
    const res = await apiClient.get('/api/pharmacist/dashboard');
    return res.data;
  },

  async flagForDoctor(prescriptionId: string, lineNumber: number, reason: string, note?: string): Promise<any> {
    if (USE_MOCK_API) {
      return {
        status: "SUCCESS",
        message: `Prescription ${prescriptionId} Line #${lineNumber} flagged for Doctor Review. Email dispatched to zadesojal@gmail.com.`,
        review_id: "rev_mock_flag_123",
        doctor_review_url: "/review/demo_token"
      };
    }
    const res = await apiClient.post('/api/pharmacist/flag', {
      prescription_id: prescriptionId,
      line_number: lineNumber,
      reason: reason,
      note: note,
      doctor_email: "zadesojal@gmail.com"
    });
    return res.data;
  },

  async getNotifications(): Promise<any> {
    if (USE_MOCK_API) {
      return {
        notifications: [
          { id: "notif_1", type: "DOCTOR_VERIFIED", title: "Doctor Verification Complete", message: "Dr. Sojal Zade verified Prescription rx_81088bcc Line #2 as 'Napa'.", timestamp: "10 mins ago", read: false },
          { id: "notif_2", type: "DOCTOR_REVIEW_SENT", title: "Doctor Review Escalated", message: "Prescription rx_90214a sent to Dr. Sojal Zade via email.", timestamp: "30 mins ago", read: true },
          { id: "notif_3", type: "ANALYSIS_COMPLETE", title: "Prescription Scanned", message: "Prescription rx_1234abcd scanned: 4 lines detected.", timestamp: "1 hour ago", read: true }
        ]
      };
    }
    const res = await apiClient.get('/api/pharmacist/notifications');
    return res.data;
  }
};
