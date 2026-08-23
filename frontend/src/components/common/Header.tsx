import React from 'react';
import { Bell, ShieldCheck, User, Menu } from 'lucide-react';
import { CURRENT_DOCTOR } from '../../constants';

interface HeaderProps {
  onToggleSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-4 md:px-6 flex items-center justify-between sticky top-0 z-30 shadow-sm">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
          aria-label="Toggle Sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-medical-700 to-medical-500 flex items-center justify-center text-white font-bold text-lg shadow-sm">
            M
          </div>
          <div>
            <h1 className="font-bold text-slate-900 leading-tight text-base flex items-center gap-2">
              MediVerify <span className="text-xs font-semibold px-2 py-0.5 rounded bg-medical-50 text-medical-700 border border-medical-100">AI Console</span>
            </h1>
            <p className="text-xs text-slate-500 font-medium">Doctor Decision-Support Workspace</p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Secure Session</span>
        </div>

        <button className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
        </button>

        <div className="h-6 w-px bg-slate-200" />

        <div className="flex items-center gap-2.5 cursor-pointer p-1 rounded-lg hover:bg-slate-50 transition-colors">
          <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 font-semibold text-sm">
            SZ
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-bold text-slate-900">{CURRENT_DOCTOR.doctor_name}</div>
            <div className="text-[11px] text-slate-500 font-medium">{CURRENT_DOCTOR.specialty}</div>
          </div>
        </div>
      </div>
    </header>
  );
};
