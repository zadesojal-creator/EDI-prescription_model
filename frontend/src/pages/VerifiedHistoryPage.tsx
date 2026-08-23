import React, { useState } from 'react';
import { CheckCircle2, Search, Lock } from 'lucide-react';
import { CURRENT_DOCTOR } from '../constants';

export const VerifiedHistoryPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'ALL' | 'CONFIRMED' | 'CORRECTED' | 'OOD'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const mockHistory = [
    {
      id: "ver_001",
      prescription_id: "rx_81088bcc",
      line_no: 4,
      ai_prediction: "Napa Extend",
      verified_label: "Napa Extend",
      action: "CONFIRMED",
      doctor: CURRENT_DOCTOR.doctor_name,
      timestamp: "2026-08-23 23:51",
      model: "EfficientNetB0 (v1.0)"
    },
    {
      id: "ver_002",
      prescription_id: "rx_81088bcc",
      line_no: 1,
      ai_prediction: "Unknown",
      verified_label: "Cold er",
      action: "CORRECTED",
      doctor: CURRENT_DOCTOR.doctor_name,
      timestamp: "2026-08-23 23:52",
      model: "EfficientNetB0 (v1.0)"
    },
    {
      id: "ver_003",
      prescription_id: "rx_90214a",
      line_no: 2,
      ai_prediction: "Unknown",
      verified_label: "Augmentin 625",
      action: "OOD",
      doctor: CURRENT_DOCTOR.doctor_name,
      timestamp: "2026-08-23 22:20",
      model: "EfficientNetB0 (v1.0)"
    }
  ];

  const filtered = mockHistory.filter(item => {
    if (activeTab !== 'ALL' && item.action !== activeTab) return false;
    return (
      item.prescription_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.verified_label.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <CheckCircle2 className="w-6 h-6 text-emerald-600" />
            Doctor Verified Dataset Log
          </h1>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Immutable log of doctor-confirmed and corrected prescription samples
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-bold">
          {['ALL', 'CONFIRMED', 'CORRECTED', 'OOD'].map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t as any)}
              className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
                activeTab === t ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
        <input
          type="text"
          placeholder="Search verified catalog by Prescription ID or Verified Brand..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm font-medium"
        />
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200 uppercase tracking-wider">
                <th className="py-3 px-4">Verification ID</th>
                <th className="py-3 px-4">Prescription</th>
                <th className="py-3 px-4">Original AI Prediction</th>
                <th className="py-3 px-4">Doctor Verified Label</th>
                <th className="py-3 px-4">Doctor Action</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Audit Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map(item => (
                <tr key={item.id} className="hover:bg-slate-50/60">
                  <td className="py-3 px-4 font-mono font-bold text-slate-700">{item.id}</td>
                  <td className="py-3 px-4 font-mono text-slate-900">{item.prescription_id} (Line #{item.line_no})</td>
                  <td className="py-3 px-4 text-slate-500 font-semibold">{item.ai_prediction}</td>
                  <td className="py-3 px-4 font-bold text-emerald-800 text-sm">{item.verified_label}</td>
                  <td className="py-3 px-4 font-bold">
                    <span className={`px-2 py-0.5 rounded text-[10px] ${
                      item.action === 'CONFIRMED' ? 'bg-emerald-100 text-emerald-800' :
                      item.action === 'CORRECTED' ? 'bg-medical-100 text-medical-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {item.action}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-500">{item.timestamp}</td>
                  <td className="py-3 px-4 text-emerald-600 font-semibold flex items-center gap-1">
                    <Lock className="w-3 h-3" />
                    <span>Preserved</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
