import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Clock,
  AlertTriangle,
  Send,
  CheckCircle2,
  ArrowRight,
  FileText
} from 'lucide-react';
import { StatCard } from '../../components/common/StatCard';
import { pharmacistApi } from '../../services/pharmacistApi';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';

export const PharmacistDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    pharmacistApi.getDashboard()
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6"><LoadingSkeleton /></div>;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 font-sans">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-medical-900 text-white rounded-2xl p-6 shadow-md flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="px-2.5 py-1 rounded-full bg-medical-500/30 text-medical-200 text-xs font-bold border border-medical-400/30 uppercase tracking-wider">
            Pharmacist Dispensing Console
          </span>
          <h1 className="text-2xl font-bold mt-2">Good evening, Alex Smith, R.Ph.</h1>
          <p className="text-slate-300 text-xs font-medium mt-1">
            AI-assisted prescription scanning, line extraction, and doctor escalation workspace.
          </p>
        </div>

        <button
          onClick={() => navigate('/pharmacist/scan')}
          className="px-5 py-2.5 rounded-xl bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs shadow-md flex items-center gap-2 self-start md:self-auto cursor-pointer"
        >
          <Sparkles className="w-4 h-4" />
          <span>Scan New Prescription</span>
        </button>
      </div>

      {/* 5 Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="SCANNED TODAY"
          value={data?.scanned_today || 42}
          subtitle="Prescriptions uploaded"
          icon={FileText}
          variant="info"
        />
        <StatCard
          title="PROCESSING"
          value={data?.processing || 3}
          subtitle="AI Segmentation in progress"
          icon={Clock}
          variant="default"
        />
        <StatCard
          title="NEEDS REVIEW"
          value={data?.needs_review || 7}
          subtitle="Uncertain line items"
          icon={AlertTriangle}
          variant="warning"
          actionText="Inspect"
          onAction={() => navigate('/pharmacist/prescriptions')}
        />
        <StatCard
          title="DOCTOR REVIEW"
          value={data?.doctor_review_count || 4}
          subtitle="Escalated to Doctor"
          icon={Send}
          variant="danger"
          actionText="Track Status"
          onAction={() => navigate('/pharmacist/prescriptions?status=DOCTOR_REVIEW')}
        />
        <StatCard
          title="VERIFIED"
          value={data?.verified_count || 28}
          subtitle="Ready for dispensing"
          icon={CheckCircle2}
          variant="success"
          actionText="View Catalog"
          onAction={() => navigate('/pharmacist/prescriptions?status=VERIFIED')}
        />
      </div>

      {/* Recent Scans Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-slate-900 text-base">Recent Prescription Scans</h2>
            <p className="text-xs text-slate-500 font-medium">
              Monitor AI recognition progress and doctor escalation status
            </p>
          </div>
          <button
            onClick={() => navigate('/pharmacist/prescriptions')}
            className="text-xs font-bold text-medical-600 hover:text-medical-700"
          >
            View All Scans →
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200 uppercase tracking-wider">
                <th className="py-3 px-4">Prescription ID</th>
                <th className="py-3 px-4">Lines Detected</th>
                <th className="py-3 px-4">Lowest Confidence</th>
                <th className="py-3 px-4">Current Status</th>
                <th className="py-3 px-4">Scanned Time</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {data?.recent_scans?.map((s: any) => (
                <tr key={s.prescription_id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-bold font-mono text-slate-900">
                    {s.prescription_id}
                  </td>
                  <td className="py-3 px-4 font-semibold text-slate-700">
                    {s.lines} lines
                  </td>
                  <td className="py-3 px-4 font-bold text-slate-800">
                    {(s.confidence * 100).toFixed(1)}%
                  </td>
                  <td className="py-3 px-4 font-bold">
                    <span className={`px-2.5 py-0.5 rounded text-[10px] ${
                      s.status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800' :
                      s.status === 'DOCTOR_REVIEW' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {s.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-500">{s.created_at}</td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => navigate(`/pharmacist/prescription/${s.prescription_id}`)}
                      className="px-3 py-1.5 rounded-lg bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs shadow-2xs transition-colors cursor-pointer flex items-center gap-1 ml-auto"
                    >
                      <span>INSPECT</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
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
