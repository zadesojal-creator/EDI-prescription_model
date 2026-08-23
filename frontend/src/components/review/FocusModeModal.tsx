import React, { useState } from 'react';
import { X, ChevronLeft, ChevronRight, Check, Edit3, AlertTriangle } from 'lucide-react';
import { MedicineLine } from '../../types';

interface FocusModeModalProps {
  isOpen: boolean;
  lines: MedicineLine[];
  onClose: () => void;
  onConfirm: (line: MedicineLine) => void;
  onOpenCorrectModal: (line: MedicineLine) => void;
  onOpenOODModal: (line: MedicineLine) => void;
}

export const FocusModeModal: React.FC<FocusModeModalProps> = ({
  isOpen,
  lines,
  onClose,
  onConfirm,
  onOpenCorrectModal,
  onOpenOODModal
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (!isOpen || !lines || lines.length === 0) return null;

  const currentLine = lines[currentIndex];
  const pred = currentLine.prediction;
  const confPct = Math.round(pred.top_confidence * 100);

  const segImgUrl = currentLine.segment_filename
    ? `/api/image/segments/${currentLine.segment_filename}`
    : '/data/sample_prescription_multiline.png';

  const handleNext = () => {
    if (currentIndex < lines.length - 1) setCurrentIndex(prev => prev + 1);
  };

  const handlePrev = () => {
    if (currentIndex > 0) setCurrentIndex(prev => prev - 1);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 text-slate-100 rounded-2xl max-w-2xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 rounded-md bg-medical-600 text-white font-bold text-xs">
              FOCUS MODE
            </span>
            <span className="font-bold text-sm text-slate-200">
              Line #{currentLine.line_number} of {lines.length}
            </span>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-center">
          {/* Large Cropped Handwriting Image */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex items-center justify-center min-h-[160px]">
            <img
              src={segImgUrl}
              alt={`Focus Line #${currentLine.line_number}`}
              className="max-h-36 object-contain rounded"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/data/sample_prescription_multiline.png';
              }}
            />
          </div>

          {/* AI Prediction & Confidence */}
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">Top Predicted Brand</span>
            <h2 className="text-3xl font-extrabold text-medical-400">{pred.top_brand}</h2>
            <div className="mt-2 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 text-xs font-semibold text-slate-300">
              <span>Generic Formulation: {pred.generic_name || 'N/A'}</span>
              <span>•</span>
              <span className={confPct >= 90 ? 'text-emerald-400' : 'text-rose-400'}>{confPct}% Confidence</span>
            </div>
          </div>

          {/* Verification Action Buttons */}
          <div className="grid grid-cols-3 gap-3 pt-2">
            <button
              onClick={() => onConfirm(currentLine)}
              className="py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm flex items-center justify-center gap-2 shadow-sm cursor-pointer"
            >
              <Check className="w-4 h-4" />
              <span>✓ Confirm</span>
            </button>
            <button
              onClick={() => onOpenCorrectModal(currentLine)}
              className="py-3 px-4 rounded-xl bg-medical-600 hover:bg-medical-700 text-white font-bold text-sm flex items-center justify-center gap-2 shadow-sm cursor-pointer"
            >
              <Edit3 className="w-4 h-4" />
              <span>✎ Correct</span>
            </button>
            <button
              onClick={() => onOpenOODModal(currentLine)}
              className="py-3 px-4 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-sm flex items-center justify-center gap-2 shadow-sm cursor-pointer"
            >
              <AlertTriangle className="w-4 h-4" />
              <span>⚠ OOD</span>
            </button>
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/90 flex items-center justify-between">
          <button
            onClick={handlePrev}
            disabled={currentIndex === 0}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-xs font-bold flex items-center gap-1 cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous Line</span>
          </button>

          <span className="text-xs text-slate-400 font-medium">
            {currentIndex + 1} / {lines.length}
          </span>

          <button
            onClick={handleNext}
            disabled={currentIndex === lines.length - 1}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-xs font-bold flex items-center gap-1 cursor-pointer"
          >
            <span>Next Line</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
