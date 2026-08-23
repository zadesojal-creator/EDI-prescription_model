import { apiClient, USE_MOCK_API } from './api';
import { FeedbackPayload } from '../types';
import { CURRENT_DOCTOR } from '../constants';

export const feedbackApi = {
  async submitDoctorFeedback(payload: FeedbackPayload): Promise<any> {
    if (USE_MOCK_API) {
      return {
        status: "SUCCESS",
        message: "Doctor feedback recorded successfully in mock mode.",
        audit_record: {
          token: payload.token,
          action: payload.doctor_action,
          label: payload.doctor_verified_label,
          doctor: CURRENT_DOCTOR.doctor_name,
          timestamp: new Date().toISOString()
        }
      };
    }
    const res = await apiClient.post('/api/doctor/feedback', payload);
    return res.data;
  }
};
