import axios from 'axios';

const env = (import.meta as any).env || {};
const API_BASE_URL = env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
export const USE_MOCK_API = env.VITE_USE_MOCK_API === 'true';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 15000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
