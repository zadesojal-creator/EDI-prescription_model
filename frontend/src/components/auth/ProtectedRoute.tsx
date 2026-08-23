import React from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { authApi } from '../../services/authApi';
import { UserRole } from '../../types/auth';

interface ProtectedRouteProps {
  requiredRole: UserRole;
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ requiredRole, children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const currentUser = authApi.getCurrentUser();

  if (!currentUser) {
    const loginTarget = requiredRole === 'DOCTOR' ? '/doctor/login' : '/pharmacist/login';
    return <Navigate to={loginTarget} state={{ from: location }} replace />;
  }

  if (currentUser.role !== requiredRole && currentUser.role !== 'ADMIN') {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-slate-800 border border-slate-700 rounded-2xl p-8 text-center space-y-5 shadow-2xl animate-in fade-in zoom-in-95">
          <div className="w-16 h-16 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center mx-auto border border-rose-500/30">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div>
            <span className="px-2.5 py-1 rounded bg-rose-500/20 text-rose-300 font-bold text-xs uppercase tracking-wider">
              403 Access Restricted
            </span>
            <h2 className="text-2xl font-bold mt-2 text-white">Role Permission Denied</h2>
            <p className="text-slate-400 text-xs font-medium mt-2 leading-relaxed">
              {requiredRole === 'DOCTOR'
                ? "Doctor privileges are required to access this clinical verification workspace. Pharmacists cannot approve doctor reviews."
                : "Pharmacist credentials are required to access the dispensing scanner workspace."}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/60 text-left text-xs space-y-1 text-slate-300">
            <div><span className="text-slate-500 font-bold">Signed in as:</span> {currentUser.name} ({currentUser.email})</div>
            <div><span className="text-slate-500 font-bold">Assigned Role:</span> <span className="font-bold text-amber-400">{currentUser.role}</span></div>
            <div><span className="text-slate-500 font-bold">Required Role:</span> <span className="font-bold text-emerald-400">{requiredRole}</span></div>
          </div>

          <button
            onClick={() => {
              if (currentUser.role === 'PHARMACIST') navigate('/pharmacist/dashboard');
              else if (currentUser.role === 'DOCTOR') navigate('/doctor/dashboard');
              else navigate('/');
            }}
            className="w-full py-3 px-4 rounded-xl bg-medical-600 hover:bg-medical-700 font-bold text-xs text-white shadow-md flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to {currentUser.role === 'PHARMACIST' ? 'Pharmacist Dashboard' : 'Doctor Console'}</span>
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
