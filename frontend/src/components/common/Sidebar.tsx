import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Inbox,
  CheckCircle2,
  History,
  BarChart3,
  Cpu,
  Settings,
  HelpCircle,
  LogOut,
  X
} from 'lucide-react';

interface SidebarProps {
  highCount?: number;
  mediumCount?: number;
  lowCount?: number;
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  highCount = 4,
  mediumCount = 8,
  lowCount = 17,
  isOpen = false,
  onClose
}) => {
  const navItems = [
    { to: '/doctor/dashboard', label: 'Overview', icon: LayoutDashboard },
    { to: '/doctor/reviews', label: 'Review Queue', icon: Inbox, badge: highCount + mediumCount + lowCount },
    { to: '/doctor/verified', label: 'Verified', icon: CheckCircle2 },
    { to: '/doctor/history', label: 'Review History', icon: History },
    { to: '/doctor/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/doctor/models', label: 'Model Registry', icon: Cpu },
  ];

  return (
    <>
      {/* Backdrop overlay for mobile */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40 md:hidden"
        />
      )}

      <aside
        className={`fixed md:sticky top-0 left-0 z-50 h-screen w-64 bg-slate-900 text-slate-300 flex flex-col transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Sidebar Header */}
        <div className="h-16 px-5 flex items-center justify-between border-b border-slate-800">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Navigation</span>
          <button onClick={onClose} className="md:hidden text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Priority Quick Counters */}
        <div className="p-4 mx-3 my-3 bg-slate-800/80 rounded-xl border border-slate-700/60">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">Priority Queue</div>
          <div className="space-y-1.5 text-xs font-medium">
            <div className="flex items-center justify-between text-rose-300">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-500"/> HIGH</span>
              <span className="font-bold px-1.5 py-0.5 rounded bg-rose-500/20">{highCount}</span>
            </div>
            <div className="flex items-center justify-between text-amber-300">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-500"/> MEDIUM</span>
              <span className="font-bold px-1.5 py-0.5 rounded bg-amber-500/20">{mediumCount}</span>
            </div>
            <div className="flex items-center justify-between text-emerald-300">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500"/> LOW</span>
              <span className="font-bold px-1.5 py-0.5 rounded bg-emerald-500/20">{lowCount}</span>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-medical-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                  }`
                }
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-bold border border-slate-700">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer actions */}
        <div className="p-3 border-t border-slate-800 space-y-1 text-xs font-medium">
          <NavLink to="/doctor/profile" className="flex items-center gap-3 px-3.5 py-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800">
            <Settings className="w-4 h-4" />
            <span>Profile & Settings</span>
          </NavLink>
          <a href="#help" className="flex items-center gap-3 px-3.5 py-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800">
            <HelpCircle className="w-4 h-4" />
            <span>Documentation</span>
          </a>
          <button className="w-full flex items-center gap-3 px-3.5 py-2 rounded-lg text-rose-400 hover:bg-rose-500/10 transition-colors">
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
};
