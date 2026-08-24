import React, { useState } from 'react';
import {
  Check,
  Edit3,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  FileSpreadsheet
} from 'lucide-react';
import { MedicineLine } from '../../types';
import { PriorityBadge } from '../common/PriorityBadge';
import { MedicineInfoPanel } from './MedicineInfoPanel';

interface MedicineLineCardProps {
  line: MedicineLine;
  index: number;
  isSelected?: boolean;
  onSelect?: () => void;
  onConfirm: (line: MedicineLine) => void;
  onOpenCorrectModal: (line: MedicineLine) => void;
  onOpenOODModal: (line: MedicineLine) => void;
}

export const MedicineLineCard: React.FC<MedicineLineCardProps> = ({
  line,
  index,
  isSelected = false,
  onSelect,
  onConfirm,
  onOpenCorrectModal,
  onOpenOODModal
}) => {
  const [showCandidates, setShowCandidates] = useState(false);
  const pred = line.prediction;
  const confPct = Math.round(pred.top_confidence * 100);

  const isConfirmed = line.status === 'CONFIRMED';
  const isCorrected = line.status === 'CORRECTED';
  const isOOD = line.status === 'OOD';
  const isVerified = isConfirmed || isCorrected || isOOD;

  // Segment image crop URL conversion
  const segImgUrl = line.segment_filename
    ? `/api/image/segments/${line.segment_filename}`
    : '/data/sample_prescription_multiline.png';

  return (
    <div
      id={`line-card-${index}`}
      onClick={onSelect}
      className={`p-5 rounded-xl border transition-all bg-white shadow-xs ${
        isSelected
          ? 'ring-2 ring-medical-500 border-medical-400 shadow-md'
          : isVerified
          ? 'border-emerald-200 bg-gradient-to-b from-emerald-50/20 to-white'
          : 'border-slate-200 hover:border-slate-300'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <span className="w-7 h-7 rounded-lg bg-medical-50 text-medical-700 font-bold text-xs flex items-center justify-center border border-medical-100">
            #{line.line_number}
          </span>
          <h3 className="font-bold text-slate-900 text-sm">Medicine Line #{line.line_number}</h3>
          {isVerified && (
            <span className="flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Verified by Doctor
            </span>
          )}
        </div>

        <PriorityBadge priority={pred.review_priority || 'HIGH'} size="sm" />
      </div>

      {/* Grid Content */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left: Cropped Handwriting Segment Image */}
        <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800 flex flex-col items-center justify-center min-h-[110px]">
          <span className="text-[10px] font-medium text-slate-400 mb-1">Cropped Handwriting Segment</span>
          <img
            src={segImgUrl}
            alt={`Line #${line.line_number} crop`}
            className="max-h-24 object-contain rounded border border-slate-800"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '/data/sample_prescription_multiline.png';
            }}
          />
        </div>

        {/* Right: AI Prediction Summary */}
        <div className="space-y-2 text-xs font-medium text-slate-700">
          <div>
            <span className="text-slate-400 uppercase tracking-wider text-[10px] font-bold block">Top AI Predicted Brand</span>
            <span className="text-base font-bold text-medical-700">{pred.top_brand}</span>
          </div>

          <div>
            <span className="text-slate-400 uppercase tracking-wider text-[10px] font-bold block">Generic Chemical Formulation</span>
            <span className="text-slate-800 font-semibold">{pred.generic_name || 'N/A (UNVERIFIED)'}</span>
          </div>

          {/* AI Confidence Meter */}
          <div>
            <div className="flex justify-between items-center text-[11px] font-bold text-slate-600 mb-1">
              <span>AI Confidence</span>
              <span className={confPct >= 90 ? 'text-emerald-600' : confPct >= 70 ? 'text-amber-600' : 'text-rose-600'}>
                {confPct}% ({pred.status})
              </span>
            </div>
            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
              <div
                className={`h-full rounded-full transition-all ${
                  confPct >= 90 ? 'bg-emerald-500' : confPct >= 70 ? 'bg-amber-500' : 'bg-rose-500'
                }`}
                style={{ width: `${confPct}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Doctor Verification Status (if already verified) */}
      {isVerified && (
        <div className="mt-4 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 font-medium flex items-center justify-between">
          <div>
            <span className="font-bold">Verified Label: </span>
            <span className="font-semibold text-emerald-950">{line.doctor_verified_label || pred.top_brand}</span>
            <span className="ml-2 text-[11px] text-emerald-700">({line.status})</span>
          </div>
          <span className="text-[11px] text-emerald-600 font-semibold">✓ Original AI data preserved</span>
        </div>
      )}

      {/* Expandable Top-3 Candidates Table */}
      <div className="mt-4 pt-3 border-t border-slate-100">
        <button
          onClick={() => setShowCandidates(!showCandidates)}
          className="w-full flex items-center justify-between text-xs font-bold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <span className="flex items-center gap-1.5">
            <FileSpreadsheet className="w-3.5 h-3.5 text-medical-600" />
            Top-3 AI Candidates Table
          </span>
          {showCandidates ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showCandidates && (
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
                  <th className="py-1.5 px-2">Rank</th>
                  <th className="py-1.5 px-2">Brand Candidate</th>
                  <th className="py-1.5 px-2">Generic Formulation</th>
                  <th className="py-1.5 px-2">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pred.top_candidates?.map((c, i) => (
                  <tr key={i} className="hover:bg-slate-50/50">
                    <td className="py-1.5 px-2 font-bold text-slate-400">#{i + 1}</td>
                    <td className="py-1.5 px-2 font-bold text-slate-800">{c.brand_name}</td>
                    <td className="py-1.5 px-2 text-slate-600">{c.generic_name}</td>
                    <td className="py-1.5 px-2 font-semibold text-slate-700">{(c.confidence * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Free Medicine Information Panel (RxNorm + openFDA) */}
      <MedicineInfoPanel info={pred.medicine_info} brandName={pred.top_brand} />

      {/* Action Buttons */}
      <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-3 gap-2">
        <button
          onClick={() => onConfirm(line)}
          className={`px-3 py-2 rounded-lg font-bold text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer ${
            isConfirmed
              ? 'bg-emerald-600 text-white shadow-xs'
              : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
          }`}
        >
          <Check className="w-3.5 h-3.5" />
          <span>✓ Confirm ({pred.top_brand})</span>
        </button>

        <button
          onClick={() => onOpenCorrectModal(line)}
          className={`px-3 py-2 rounded-lg font-bold text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer ${
            isCorrected
              ? 'bg-medical-600 text-white shadow-xs'
              : 'bg-medical-50 text-medical-700 hover:bg-medical-100 border border-medical-200'
          }`}
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>✎ Correct Brand</span>
        </button>

        <button
          onClick={() => onOpenOODModal(line)}
          className={`px-3 py-2 rounded-lg font-bold text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer ${
            isOOD
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>⚠ OOD Medicine</span>
        </button>
      </div>
    </div>
  );
};
