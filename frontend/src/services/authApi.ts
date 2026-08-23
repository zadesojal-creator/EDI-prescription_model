import { apiClient, USE_MOCK_API } from './api';
import { AuthUser, LoginCredentials } from '../types/auth';

const AUTH_USER_KEY = 'mediverify_auth_user';

export const authApi = {
  async login(credentials: LoginCredentials): Promise<AuthUser> {
    if (USE_MOCK_API) {
      const isDoc = credentials.email.includes('doctor') || credentials.email.includes('sojal') || credentials.role === 'DOCTOR';
      const user: AuthUser = isDoc
        ? {
            user_id: 'doc_001',
            name: 'Dr. Sojal Zade, M.D.',
            email: 'zadesojal@gmail.com',
            role: 'DOCTOR',
            specialty: 'Pediatrician / General Physician',
            access_token: 'mock_doc_token_123'
          }
        : {
            user_id: 'pharm_001',
            name: 'Alex Smith, R.Ph.',
            email: credentials.email || 'pharmacist@clinic.org',
            role: 'PHARMACIST',
            pharmacy: 'MediVerify Central Pharmacy',
            access_token: 'mock_pharm_token_123'
          };
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
      return user;
    }

    const res = await apiClient.post('/api/auth/login', credentials);
    const user: AuthUser = res.data;
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
    return user;
  },

  logout() {
    localStorage.removeItem(AUTH_USER_KEY);
  },

  getCurrentUser(): AuthUser | null {
    const raw = localStorage.getItem(AUTH_USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },

  isAuthenticated(): boolean {
    return Boolean(this.getCurrentUser());
  },

  hasRole(role: string): boolean {
    const user = this.getCurrentUser();
    return user ? user.role === role : false;
  }
};
