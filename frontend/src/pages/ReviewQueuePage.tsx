import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, Filter, ArrowRight, Inbox } from 'lucide-react';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { reviewApi } from '../services/reviewApi';
import { ReviewTask } from '../types';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';

export const ReviewQueuePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialPriority = searchParams.get('priority') || 'ALL';

  const [reviews, setReviews] = useState<ReviewTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [priorityFilter, setPriorityFilter] = useState(initialPriority);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    setLoading(true);
    reviewApi.getPendingReviews(priorityFilter === 'ALL' ? undefined : priorityFilter)
      .then(data => {
        setReviews(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load queue:", err);
        setLoading(false);
      });
  }, [priorityFilter]);

  const filteredReviews = reviews.filter(r =>
    r.prescription_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.original_prediction.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Inbox className="w-6 h-6 text-medical-600" />
            Doctor Review Queue
          </h1>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Select a prescription to open the interactive AI Review Workspace
          </p>
        </div>

        {/* Priority Filter Pills */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-bold">
          {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((p) => (
            <button
              key={p}
              onClick={() => setPriorityFilter(p)}
              className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
                priorityFilter === p
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
        <input
          type="text"
          placeholder="Search queue by Prescription ID or AI Predicted Brand Name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-medical-500 text-sm font-medium shadow-2xs"
        />
      </div>

      {/* Reviews Grid */}
      {loading ? (
        <LoadingSkeleton />
      ) : filteredReviews.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredReviews.map((r) => (
            <div
              key={r.review_id}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                  <span className="font-mono font-bold text-xs text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                    {r.prescription_id}
                  </span>
                  <PriorityBadge priority={r.priority} size="sm" />
                </div>

                <div className="space-y-2 text-xs font-medium text-slate-700">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Total Medicines:</span>
                    <span className="font-bold text-slate-900">{r.total_medicines_detected} line(s)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Top AI Prediction:</span>
                    <span className="font-bold text-medical-700">{r.original_prediction}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Top AI Confidence:</span>
                    <span className="font-bold text-slate-800">{(r.original_confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400 font-medium">
                  {new Date(r.created_at).toLocaleDateString()}
                </span>
                <button
                  onClick={() => navigate(`/review/${r.review_id}`)}
                  className="px-4 py-2 rounded-lg bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs shadow-2xs flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  <span>OPEN REVIEW</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-500">
          <Inbox className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h3 className="font-bold text-slate-800 text-sm">No Pending Prescription Reviews</h3>
          <p className="text-xs text-slate-500 mt-1">All prescription reviews matching your filter have been completed.</p>
        </div>
      )}
    </div>
  );
};
