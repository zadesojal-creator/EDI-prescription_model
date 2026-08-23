import React from 'react';
import { CheckCircle2, ShieldCheck, Eye } from 'lucide-react';

interface ReviewProgressProps {
  totalLines: number;
  reviewedCount: number;
  onOpenFocusMode?: () => void;
  onConfirmAll?: () => void;
  onSubmitFullReview?: () => void;
}

export const ReviewProgress: React.FC<ReviewProgressProps> = ({
  totalLines,
  reviewedCount,
  onOpenFocusMode,
  onConfirmAll,
  onSubmitFullReview
}) => {
  const pct = totalLines > 0 ? Math.round((reviewedCount / totalLines) * 100) : 0;
  const isComplete = reviewedCount >= totalLines && totalLines > 0;

  return (
    <div className="sticky bottom-0 z-30 bg-white/95 backdrop-blur-md border-t border-slate-200 px-4 py-3 shadow-lg">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Left: Progress Bar */}
        <div className="w-full sm:w-1/2 space-y-1">
          <div className="flex items-center justify-between text-xs font-bold text-slate-700">
            <span>
              {reviewedCount} of {totalLines} Medicines Verified
            </span>
            <span className={isComplete ? 'text-emerald-600' : 'text-medical-600'}>{pct}%</span>
          </div>
          <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                isComplete ? 'bg-emerald-500' : 'bg-medical-500'
              }`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
          {onOpenFocusMode && (
            <button
              onClick={onOpenFocusMode}
              className="px-3.5 py-2 rounded-lg font-bold text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Eye className="w-3.5 h-3.5 text-slate-500" />
              <span>Focus Mode</span>
            </button>
          )}

          {onConfirmAll && (
            <button
              onClick={onConfirmAll}
              className="px-3.5 py-2 rounded-lg font-bold text-xs bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Confirm All ({totalLines})</span>
            </button>
          )}

          {onSubmitFullReview && (
            <button
              onClick={onSubmitFullReview}
              className={`px-4 py-2 rounded-lg font-bold text-xs text-white shadow-xs flex items-center gap-1.5 transition-colors cursor-pointer ${
                isComplete ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-medical-600 hover:bg-medical-700'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Complete Verification</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
