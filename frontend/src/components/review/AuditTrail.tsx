import React, { useState } from 'react';
import { ShieldCheck, ChevronDown, ChevronUp, Lock } from 'lucide-react';
import { ReviewTask } from '../../types';
import { CURRENT_DOCTOR } from '../../constants';

interface AuditTrailProps {
  task: ReviewTask;
}

export const AuditTrail: React.FC<AuditTrailProps> = ({ task }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between font-bold text-xs text-slate-700 hover:text-slate-900 transition-colors"
      >
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>IMMUTABLE CLINICAL AUDIT INFORMATION</span>
          <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono">
            {task.review_id}
          </span>
        </div>
        {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {isOpen && (
        <div className="mt-4 pt-4 border-t border-slate-100 grid grid-cols-1 md:grid-cols-2 gap-6 text-xs font-medium">
          {/* Left: Original AI Data */}
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between text-slate-500 font-bold border-b border-slate-200 pb-1.5 uppercase text-[10px]">
              <span>Original AI Inference Data</span>
              <Lock className="w-3 h-3 text-slate-400" />
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Top AI Predicted Brand:</span>
              <span className="font-bold text-slate-800 text-sm">{task.original_prediction}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Original Confidence Score:</span>
              <span className="font-semibold text-slate-700">{(task.original_confidence * 100).toFixed(2)}%</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">AI Model Architecture & Version:</span>
              <span className="font-mono text-slate-700">EfficientNetB0 ({task.model_version || 'v1.0'})</span>
            </div>
            <div className="pt-1 text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
              <span>✓ Original AI data preserved without mutation</span>
            </div>
          </div>

          {/* Right: Doctor Verification Data */}
          <div className="p-3.5 rounded-lg bg-emerald-50/60 border border-emerald-200 space-y-2">
            <div className="flex items-center justify-between text-emerald-800 font-bold border-b border-emerald-200 pb-1.5 uppercase text-[10px]">
              <span>Doctor Verification & Audit Log</span>
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Reviewing Medical Professional:</span>
              <span className="font-bold text-slate-900">{CURRENT_DOCTOR.doctor_name} ({CURRENT_DOCTOR.doctor_email})</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Clinical Review Priority:</span>
              <span className="font-bold text-slate-800">{task.priority} PRIORITY</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Task Verification Status:</span>
              <span className="font-bold text-emerald-700">{task.status || 'PENDING'}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Verification Timestamp:</span>
              <span className="font-mono text-slate-700">{task.created_at || new Date().toISOString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
