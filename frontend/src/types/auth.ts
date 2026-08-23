export type UserRole = 'PHARMACIST' | 'DOCTOR' | 'ADMIN';

export interface AuthUser {
  user_id: string;
  name: string;
  email: string;
  role: UserRole;
  access_token: string;
  pharmacy?: string;
  specialty?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  role?: UserRole;
}
