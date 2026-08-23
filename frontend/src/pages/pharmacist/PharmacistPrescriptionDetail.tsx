import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileText,
  AlertTriangle,
  Send,
  CheckCircle2,
  X,
  Search,
  Sparkles,
  Info
} from 'lucide-react';
import { PrescriptionViewer } from '../../components/review/PrescriptionViewer';
import { BoundingBoxOverlay } from '../../components/review/BoundingBoxOverlay';
import { PriorityBadge } from '../../components/common/PriorityBadge';
import { pharmacistApi } from '../../services/pharmacistApi';

export const PharmacistPrescriptionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [selectedLine, setSelectedLine] = useState<number | null>(1);

  const [flagModalOpen, setFlagModalOpen] = useState(false);
  const [flagReason, setFlagReason] = useState('LOW_CONFIDENCE');
  const [pharmacistNote, setPharmacistNote] = useState('');
  const [flagLoading, setFlagLoading] = useState(false);
  const [flagSuccess, setFlagSuccess] = useState<any | null>(null);

  // Sample multi-line dataset
  const lines = [
    {
      line_number: 1,
      bounding_box: { x: 44, y: 115, width: 716, height: 70 },
      top_brand: "Napa Extend",
      generic_name: "Paracetamol",
      confidence: 0.938,
      status: "high_confidence",
      top_candidates: [
        { class_index: 55, brand_name: "Napa Extend", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.938 },
        { class_index: 54, brand_name: "Napa", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.042 },
        { class_index: 0, brand_name: "Ace", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.012 }
      ]
    },
    {
      line_number: 2,
      bounding_box: { x: 66, y: 180, width: 455, height: 67 },
      top_brand: "Unknown",
      generic_name: "UNVERIFIED",
      confidence: 0.362,
      status: "doctor_verification_required",
      top_candidates: [
        { class_index: 15, brand_name: "Teyp", generic_name: "Paracetamol Syrup", mapping_status: "UNVERIFIED", confidence: 0.362 },
        { class_index: 0, brand_name: "Ace", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.284 },
        { class_index: 55, brand_name: "Napa Extend", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.155 }
      ]
    },
    {
      line_number: 3,
      bounding_box: { x: 66, y: 243, width: 152, height: 54 },
      top_brand: "Ehli PD",
      generic_name: "Amoxicillin",
      confidence: 0.385,
      status: "doctor_verification_required",
      top_candidates: [
        { class_index: 18, brand_name: "Ehli PD", generic_name: "Amoxicillin", mapping_status: "UNVERIFIED", confidence: 0.385 },
        { class_index: 7, brand_name: "Azithrocin", generic_name: "Azithromycin", mapping_status: "VERIFIED", confidence: 0.301 },
        { class_index: 41, brand_name: "Zimax", generic_name: "Azithromycin", mapping_status: "VERIFIED", confidence: 0.142 }
      ]
    }
  ];

  const handleSendToDoctor = async () => {
    if (!selectedLine) return;
    setFlagLoading(true);
    try {
      const res = await pharmacistApi.flagForDoctor(id || "rx_81088bcc", selectedLine, flagReason, pharmacistNote);
      setFlagSuccess(res);
      setFlagLoading(false);
    } catch (err) {
      console.error(err);
      setFlagLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 font-sans">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 border border-slate-200 rounded-xl shadow-xs">
        <div>
          <span className="px-2 py-0.5 rounded bg-medical-50 text-medical-700 font-bold text-[10px] uppercase border border-medical-100">
            Pharmacist Inspection Workspace
          </span>
          <h1 className="text-xl font-bold text-slate-900 mt-1 flex items-center gap-2">
            <FileText className="w-5 h-5 text-medical-600" />
            Prescription #{id || 'RX-81088BCC'}
          </h1>
          <p className="text-xs text-slate-500 font-medium">
            Review medicine line predictions, top-3 candidates, and escalate low-confidence lines for Doctor Review.
          </p>
        </div>

        <button
          onClick={() => setFlagModalOpen(true)}
          className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-xs flex items-center gap-2 cursor-pointer"
        >
          <AlertTriangle className="w-4 h-4" />
          <span>SEND TO DOCTOR FOR REVIEW</span>
        </button>
      </div>

      {/* Two-Panel Grid Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Image Viewer (6 Cols) */}
        <div className="lg:col-span-6 space-y-3">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-md min-h-[500px] relative">
            <PrescriptionViewer
              imageReference="/data/sample_prescription_multiline.png"
              lines={lines.map(l => ({
                line_number: l.line_number,
                bounding_box: l.bounding_box,
                prediction: {
                  top_brand: l.top_brand,
                  generic_name: l.generic_name,
                  mapping_status: "VERIFIED",
                  top_confidence: l.confidence,
                  status: l.status,
                  doctor_feedback_required: false,
                  doctor_verification_required: false,
                  review_priority: "LOW",
                  user_message: "",
                  is_definitive_display: true,
                  top_candidates: l.top_candidates
                }
              }))}
              selectedLineIndex={selectedLine}
              onSelectLine={(lineNum: number) => setSelectedLine(lineNum)}
            />
          </div>
        </div>

        {/* Right Column: Medicine Line Analysis & Candidates (6 Cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3">
            <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-2">
              Detected Medicine Lines ({lines.length})
            </h3>

            <div className="space-y-3">
              {lines.map((m) => {
                const isSelected = selectedLine === m.line_number;
                const confPercent = Math.round(m.confidence * 100);

                return (
                  <div
                    key={m.line_number}
                    onClick={() => setSelectedLine(m.line_number)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer space-y-3 ${
                      isSelected
                        ? 'bg-medical-50/50 border-medical-500 ring-2 ring-medical-500/20 shadow-xs'
                        : 'bg-white border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-slate-800">Medicine Line #{m.line_number}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                        confPercent >= 90 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                      }`}>
                        {confPercent}% CONFIDENCE
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold">Predicted Brand</span>
                        <span className="font-bold text-medical-700 text-sm">{m.top_brand}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold">Generic Chemical</span>
                        <span className="font-semibold text-slate-800">{m.generic_name}</span>
                      </div>
                    </div>

                    {/* Top-3 Candidates Table */}
                    <div className="pt-2 border-t border-slate-100 space-y-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Top-3 AI Candidates</span>
                      {m.top_candidates.map((c, idx) => (
                        <div key={idx} className="flex items-center justify-between text-[11px] text-slate-600 font-medium">
                          <span>{idx+1}. {c.brand_name} ({c.generic_name})</span>
                          <span className="font-bold text-slate-900">{Math.round(c.confidence*100)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Flag / Send to Doctor Review Modal */}
      {flagModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-rose-600" />
                Escalate Line #{selectedLine} for Doctor Review
              </h3>
              <button onClick={() => setFlagModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            {flagSuccess ? (
              <div className="space-y-4 text-center py-4">
                <CheckCircle2 className="w-12 h-12 text-emerald-600 mx-auto" />
                <h4 className="font-bold text-slate-900 text-base">Escalated to Doctor Successfully</h4>
                <p className="text-xs text-slate-600">
                  Review task created and email notification dispatched to <strong>zadesojal@gmail.com</strong> with a secure 24-hour token.
                </p>
                <button
                  onClick={() => { setFlagModalOpen(false); setFlagSuccess(null); }}
                  className="px-4 py-2 rounded-xl bg-slate-900 text-white font-bold text-xs cursor-pointer"
                >
                  Close Modal
                </button>
              </div>
            ) : (
              <div className="space-y-4 text-xs font-medium">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">Reason for Doctor Escalation</label>
                  <select
                    value={flagReason}
                    onChange={(e) => setFlagReason(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-slate-300 font-semibold bg-white text-slate-900"
                  >
                    <option value="LOW_CONFIDENCE">Low AI Confidence (&lt; 70%)</option>
                    <option value="UNREADABLE">Unreadable Handwriting</option>
                    <option value="OOD">Out-of-Distribution Medicine</option>
                    <option value="OCR_ERROR">Possible Character Error</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">Pharmacist Note (Optional)</label>
                  <textarea
                    rows={3}
                    value={pharmacistNote}
                    onChange={(e) => setPharmacistNote(e.target.value)}
                    placeholder="Enter clinical notes for Dr. Sojal Zade..."
                    className="w-full p-2.5 rounded-xl border border-slate-300 bg-white text-slate-900"
                  />
                </div>

                <div className="pt-2 flex justify-end gap-2">
                  <button
                    onClick={() => setFlagModalOpen(false)}
                    className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSendToDoctor}
                    disabled={flagLoading}
                    className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold cursor-pointer flex items-center gap-1.5"
                  >
                    <Send className="w-4 h-4" />
                    <span>{flagLoading ? "Escalating..." : "Confirm & Send to Doctor"}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
