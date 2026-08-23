import { apiClient, USE_MOCK_API } from './api';
import { ReviewTask } from '../types';
import { MOCK_REVIEWS } from '../constants';

export const reviewApi = {
  async getPendingReviews(priorityFilter?: string): Promise<ReviewTask[]> {
    if (USE_MOCK_API) {
      if (priorityFilter) {
        return MOCK_REVIEWS.filter(r => r.priority === priorityFilter);
      }
      return MOCK_REVIEWS;
    }
    const url = priorityFilter ? `/api/doctor/reviews?priority=${priorityFilter}` : '/api/doctor/reviews';
    const res = await apiClient.get(url);
    return res.data.pending_reviews || [];
  },

  async getReviewByToken(token: string): Promise<ReviewTask> {
    if (USE_MOCK_API || token.startsWith('demo')) {
      const found = MOCK_REVIEWS.find(r => r.review_id === token) || MOCK_REVIEWS[0];
      return found;
    }
    const res = await apiClient.get(`/review/${token}`, {
      headers: { Accept: 'application/json' }
    });
    return res.data.review_task || res.data;
  }
};
