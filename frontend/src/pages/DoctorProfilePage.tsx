import React from 'react';
import { User, ShieldCheck, Mail, Building, Key } from 'lucide-react';
import { CURRENT_DOCTOR } from '../constants';

export const DoctorProfilePage: React.FC = () => {
  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <User className="w-6 h-6 text-medical-600" />
          Doctor Account & Session Profile
        </h1>
        <p className="text-xs text-slate-500 font-medium mt-0.5">
          Medical practitioner credentials and clinical verification signature
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-6">
        <div className="flex items-center gap-4 pb-6 border-b border-slate-100">
          <div className="w-16 h-16 rounded-2xl bg-medical-600 text-white font-bold text-2xl flex items-center justify-center shadow-md">
            SZ
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">{CURRENT_DOCTOR.doctor_name}</h2>
            <p className="text-xs text-slate-500 font-medium">{CURRENT_DOCTOR.specialty}</p>
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 mt-2">
              <ShieldCheck className="w-3.5 h-3.5" /> Verified Medical Professional
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs font-medium">
          <div className="space-y-1">
            <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1">
              <Key className="w-3.5 h-3.5" /> Doctor ID
            </span>
            <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 font-mono font-bold text-slate-800">
              {CURRENT_DOCTOR.doctor_id}
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1">
              <Mail className="w-3.5 h-3.5" /> Registered Email Address
            </span>
            <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 font-bold text-slate-800">
              {CURRENT_DOCTOR.doctor_email}
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1">
              <Building className="w-3.5 h-3.5" /> Medical Board License / Reg. No.
            </span>
            <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 font-mono font-bold text-slate-800">
              BMDC-REG-2093/2623
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">Session Security Status</span>
            <div className="p-2.5 bg-emerald-50 rounded-lg border border-emerald-200 text-emerald-900 font-bold flex items-center justify-between">
              <span>HTTPS Encrypted Session</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
