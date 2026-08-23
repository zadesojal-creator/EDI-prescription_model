import React, { useState } from 'react';
import { AlertTriangle, X, Send } from 'lucide-react';
import { MedicineLine } from '../../types';

interface OODModalProps {
  isOpen: boolean;
  line: MedicineLine | null;
  onClose: () => void;
  onSubmitOOD: (line: MedicineLine, brandName: string, genericName?: string, notes?: string) => void;
}

export const OODModal: React.FC<OODModalProps> = ({
  isOpen,
  line,
  onClose,
  onSubmitOOD
}) => {
  const [brandName, setBrandName] = useState('');
  const [genericName, setGenericName] = useState('');
  const [notes, setNotes] = useState('');

  if (!isOpen || !line) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!brandName.trim()) return;
    onSubmitOOD(line, brandName.trim(), genericName.trim(), notes.trim());
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-amber-100 bg-amber-50/60 flex items-center justify-between">
          <div className="flex items-center gap-2 text-amber-900">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h3 className="font-bold text-base">Unregistered Medicine (OOD)</h3>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-amber-700 hover:bg-amber-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600 font-medium">
            This medicine is outside the 78 registered classes. Entering details will submit it as an
            <span className="font-bold text-slate-800"> Out-of-Distribution (OOD)</span> sample for doctor-verified dataset retraining.
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              New Medicine Brand Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              autoFocus
              placeholder="e.g., Augmentin 625..."
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-sm font-medium"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Generic Formulation (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g., Amoxicillin + Clavulanic Acid..."
              value={genericName}
              onChange={(e) => setGenericName(e.target.value)}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 text-sm font-medium"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Doctor Note / Clinical Observations (Optional)
            </label>
            <textarea
              rows={2}
              placeholder="Add notes about dosage, handwriting clarity, or formulation..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 text-sm font-medium"
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg font-bold text-xs text-slate-600 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!brandName.trim()}
              className="px-4 py-2 rounded-lg font-bold text-xs bg-amber-600 hover:bg-amber-700 text-white shadow-xs flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Submit OOD Verification</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
