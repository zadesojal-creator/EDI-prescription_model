import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Clock, CheckCircle2, Inbox, ArrowRight } from 'lucide-react';
import { StatCard } from '../components/common/StatCard';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { reviewApi } from '../services/reviewApi';
import { ReviewTask } from '../types';
import { CURRENT_DOCTOR } from '../constants';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [reviews, setReviews] = useState<ReviewTask[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    reviewApi.getPendingReviews()
      .then(data => {
        setReviews(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load queue:", err);
        setLoading(false);
      });
  }, []);

  const highCount = reviews.filter(r => r.priority === 'HIGH').length;
  const mediumCount = reviews.filter(r => r.priority === 'MEDIUM').length;
  const lowCount = reviews.filter(r => r.priority === 'LOW').length;

  if (loading) {
    return <div className="p-6"><LoadingSkeleton /></div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-medical-900 to-medical-800 text-white rounded-2xl p-6 shadow-md flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="px-2.5 py-1 rounded-full bg-medical-500/30 text-medical-200 text-xs font-bold border border-medical-400/30 uppercase tracking-wider">
            Clinical AI Decision-Support
          </span>
          <h1 className="text-2xl font-bold mt-2">Good evening, {CURRENT_DOCTOR.doctor_name}</h1>
          <p className="text-slate-300 text-xs font-medium mt-1">
            AI-assisted handwritten prescription recognition & verification console.
          </p>
        </div>

        <button
          onClick={() => navigate('/doctor/reviews')}
          className="px-5 py-2.5 rounded-xl bg-white text-slate-900 hover:bg-slate-100 font-bold text-xs shadow-sm flex items-center gap-2 self-start md:self-auto cursor-pointer"
        >
          <span>Open Review Queue</span>
          <ArrowRight className="w-4 h-4 text-medical-600" />
        </button>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="HIGH PRIORITY"
          value={highCount}
          subtitle="Urgent doctor verification required"
          icon={AlertCircle}
          variant="danger"
          actionText="Review Now"
          onAction={() => navigate('/doctor/reviews?priority=HIGH')}
        />
        <StatCard
          title="MEDIUM PRIORITY"
          value={mediumCount}
          subtitle="Verification recommended"
          icon={Clock}
          variant="warning"
          actionText="Needs Review"
          onAction={() => navigate('/doctor/reviews?priority=MEDIUM')}
        />
        <StatCard
          title="LOW PRIORITY"
          value={lowCount}
          subtitle="Routine high-confidence predictions"
          icon={Inbox}
          variant="info"
          actionText="View Routine"
          onAction={() => navigate('/doctor/reviews?priority=LOW')}
        />
        <StatCard
          title="VERIFIED TODAY"
          value={26}
          subtitle="Doctor confirmed/corrected"
          icon={CheckCircle2}
          variant="success"
          actionText="View Log"
          onAction={() => navigate('/doctor/verified')}
        />
      </div>

      {/* Priority Review Queue Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-slate-900 text-base">Priority Review Queue</h2>
            <p className="text-xs text-slate-500 font-medium">
              Prescriptions ordered by clinical review priority (HIGH → MEDIUM → LOW)
            </p>
          </div>
          <button
            onClick={() => navigate('/doctor/reviews')}
            className="text-xs font-bold text-medical-600 hover:text-medical-700"
          >
            View All Pending ({reviews.length}) →
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200 uppercase tracking-wider">
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Prescription ID</th>
                <th className="py-3 px-4">Medicines Detected</th>
                <th className="py-3 px-4">Top AI Prediction</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Created At</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {reviews.length > 0 ? (
                reviews.map((r) => (
                  <tr key={r.review_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4">
                      <PriorityBadge priority={r.priority} size="sm" />
                    </td>
                    <td className="py-3 px-4 font-bold text-slate-900 font-mono">
                      {r.prescription_id}
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-700">
                      {r.total_medicines_detected} line(s)
                    </td>
                    <td className="py-3 px-4 font-bold text-medical-700">
                      {r.original_prediction}
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-700">
                      {(r.original_confidence * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-slate-500 font-medium">
                      {new Date(r.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => navigate(`/review/${r.review_id}`)}
                        className="px-3 py-1.5 rounded-lg bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs shadow-2xs transition-colors cursor-pointer"
                      >
                        REVIEW →
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-medium">
                    No pending reviews in queue. All prescriptions are verified!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
