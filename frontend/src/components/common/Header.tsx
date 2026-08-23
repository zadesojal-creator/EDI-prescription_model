import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, LogOut, User, Pill, Stethoscope } from 'lucide-react';
import { authApi } from '../../services/authApi';

interface HeaderProps {
  onToggleSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const navigate = useNavigate();
  const currentUser = authApi.getCurrentUser();

  const handleLogout = () => {
    const isDoc = currentUser?.role === 'DOCTOR';
    authApi.logout();
    navigate(isDoc ? '/doctor/login' : '/pharmacist/login');
  };

  return (
    <header className="h-16 bg-slate-900 border-b border-slate-800 text-white flex items-center justify-between px-4 sm:px-6 sticky top-0 z-30 shadow-md font-sans">
      {/* Brand Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white cursor-pointer"
        >
          ☰
        </button>
        <div
          onClick={() => navigate(currentUser?.role === 'DOCTOR' ? '/doctor/dashboard' : '/pharmacist/dashboard')}
          className="flex items-center gap-2 cursor-pointer"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-medical-600 to-medical-400 flex items-center justify-center font-bold text-lg text-white shadow-xs">
            M
          </div>
          <div>
            <span className="font-bold text-sm tracking-tight text-white block">MediVerify AI</span>
            <span className="text-[10px] text-medical-300 font-semibold uppercase tracking-wider block">
              {currentUser?.role === 'DOCTOR' ? 'Doctor Review Portal' : 'Pharmacist Dispensing Portal'}
            </span>
          </div>
        </div>
      </div>

      {/* Role & Session Status */}
      <div className="flex items-center gap-4 text-xs">
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Encrypted Session</span>
        </div>

        {currentUser && (
          <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
            <div className="text-right hidden sm:block">
              <span className="font-bold text-slate-100 block text-xs">{currentUser.name}</span>
              <span className="text-[10px] text-slate-400 font-medium block flex items-center gap-1 justify-end">
                {currentUser.role === 'DOCTOR' ? (
                  <><Stethoscope className="w-3 h-3 text-emerald-400" /> Doctor</>
                ) : (
                  <><Pill className="w-3 h-3 text-medical-400" /> Pharmacist</>
                )}
              </span>
            </div>

            <button
              onClick={handleLogout}
              title="Logout"
              className="p-2 rounded-xl bg-slate-800 hover:bg-rose-600/20 text-slate-300 hover:text-rose-400 border border-slate-700 transition-colors cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
