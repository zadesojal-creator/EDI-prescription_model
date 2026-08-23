import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  AlertTriangle,
  ArrowLeft,
  Cpu
} from 'lucide-react';
import { reviewApi } from '../services/reviewApi';
import { feedbackApi } from '../services/feedbackApi';
import { ReviewTask, MedicineLine } from '../types';
import { PrescriptionViewer } from '../components/review/PrescriptionViewer';
import { MedicineLineCard } from '../components/review/MedicineLineCard';
import { MedicineSearchModal } from '../components/review/MedicineSearchModal';
import { OODModal } from '../components/review/OODModal';
import { AuditTrail } from '../components/review/AuditTrail';
import { FocusModeModal } from '../components/review/FocusModeModal';
import { ReviewProgress } from '../components/review/ReviewProgress';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { CURRENT_DOCTOR } from '../constants';

export const ReviewWorkspacePage: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const [task, setTask] = useState<ReviewTask | null>(null);
  const [lines, setLines] = useState<MedicineLine[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedIndex, setSelectedIndex] = useState<number | null>(0);
  const [correctModalLine, setCorrectModalLine] = useState<MedicineLine | null>(null);
  const [oodModalLine, setOodModalLine] = useState<MedicineLine | null>(null);
  const [isFocusModeOpen, setIsFocusModeOpen] = useState(false);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);

    reviewApi.getReviewByToken(token)
      .then(data => {
        setTask(data);
        if (data.all_medicines && data.all_medicines.length > 0) {
          setLines(data.all_medicines);
        } else {
          // Fallback single line construction if single word
          setLines([{
            line_number: 1,
            bounding_box: { x: 44, y: 115, width: 716, height: 70 },
            prediction: {
              top_brand: data.original_prediction || 'Unknown',
              generic_name: null,
              mapping_status: 'UNVERIFIED',
              top_confidence: data.original_confidence || 0.0,
              status: data.prediction_status || 'high_confidence',
              doctor_feedback_required: true,
              doctor_verification_required: true,
              review_priority: data.priority || 'HIGH',
              user_message: 'Single prescription line prediction.',
              is_definitive_display: true,
              top_candidates: data.top_3_predictions || []
            }
          }]);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Token resolution error:", err);
        setError("Invalid, expired, or completed review token. Please check your link.");
        setLoading(false);
      });
  }, [token]);

  // Handler: Confirm single line
  const handleConfirmLine = async (line: MedicineLine) => {
    setLines(prev => prev.map(l => l.line_number === line.line_number ? {
      ...l,
      status: 'CONFIRMED',
      doctor_verified_label: l.prediction.top_brand
    } : l));

    try {
      await feedbackApi.submitDoctorFeedback({
        token: token || 'demo',
        doctor_action: 'CONFIRM',
        doctor_verified_label: line.prediction.top_brand,
        doctor_id: CURRENT_DOCTOR.doctor_id,
        doctor_email: CURRENT_DOCTOR.doctor_email,
        line_number: line.line_number
      });
    } catch (err) {
      console.warn("Feedback submission error:", err);
    }
  };

  // Handler: Correct brand via 78-class modal
  const handleSelectCorrectBrand = async (line: MedicineLine, brand: string) => {
    setLines(prev => prev.map(l => l.line_number === line.line_number ? {
      ...l,
      status: 'CORRECTED',
      doctor_verified_label: brand
    } : l));

    try {
      await feedbackApi.submitDoctorFeedback({
        token: token || 'demo',
        doctor_action: 'CORRECT',
        doctor_verified_label: brand,
        doctor_id: CURRENT_DOCTOR.doctor_id,
        doctor_email: CURRENT_DOCTOR.doctor_email,
        line_number: line.line_number
      });
    } catch (err) {
      console.warn("Feedback submission error:", err);
    }
  };

  // Handler: Submit OOD brand
  const handleSubmitOOD = async (line: MedicineLine, brandName: string, genericName?: string, notes?: string) => {
    setLines(prev => prev.map(l => l.line_number === line.line_number ? {
      ...l,
      status: 'OOD',
      doctor_verified_label: brandName
    } : l));

    try {
      await feedbackApi.submitDoctorFeedback({
        token: token || 'demo',
        doctor_action: 'CORRECT',
        doctor_verified_label: brandName,
        doctor_id: CURRENT_DOCTOR.doctor_id,
        doctor_email: CURRENT_DOCTOR.doctor_email,
        line_number: line.line_number,
        notes: notes
      });
    } catch (err) {
      console.warn("Feedback submission error:", err);
    }
  };

  // Handler: Confirm all lines
  const handleConfirmAll = () => {
    lines.forEach(l => handleConfirmLine(l));
  };

  // Handler: Complete Full Review
  const handleSubmitFullReview = () => {
    alert("✓ Doctor verification for full prescription complete! Verified records appended.");
    navigate('/doctor/reviews');
  };

  const reviewedCount = lines.filter(l => l.status !== undefined).length;

  if (loading) return <div className="p-6"><LoadingSkeleton /></div>;

  if (error || !task) {
    return (
      <div className="p-12 text-center max-w-lg mx-auto space-y-4">
        <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto" />
        <h2 className="text-xl font-bold text-slate-900">Review Token Unavailable</h2>
        <p className="text-xs text-slate-500">{error || "This review token is invalid or expired."}</p>
        <button
          onClick={() => navigate('/doctor/reviews')}
          className="px-4 py-2 rounded-lg bg-medical-600 text-white font-bold text-xs"
        >
          Return to Review Queue
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#f8fafc]">
      {/* Top Action Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between sticky top-16 z-20 shadow-2xs">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/doctor/reviews')}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 flex items-center gap-1 text-xs font-bold"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Queue</span>
          </button>
          <div>
            <h1 className="font-bold text-slate-900 text-base leading-tight flex items-center gap-2">
              Prescription Review Workspace
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                {task.prescription_id}
              </span>
            </h1>
            <p className="text-xs text-slate-500 font-medium">
              Total Medicines Detected: <strong className="text-slate-800">{lines.length}</strong>
            </p>
          </div>
        </div>

        <PriorityBadge priority={task.priority} size="md" />
      </div>

      {/* Main Split-Screen Content Workspace */}
      <div className="flex-1 p-6 max-w-7xl w-full mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Prescription Viewer (5 Cols) */}
        <div className="lg:col-span-5 h-[calc(100vh-180px)] sticky top-36">
          <PrescriptionViewer
            imageReference={task.image_reference}
            lines={lines}
            selectedLineIndex={selectedIndex}
            onSelectLine={(idx) => {
              setSelectedIndex(idx);
              const el = document.getElementById(`line-card-${idx}`);
              if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }}
          />
        </div>

        {/* Right Column: AI Analysis & Line Cards (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* AI Intelligence Summary Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-medical-600" />
                Prescription AI Intelligence Summary
              </span>
              <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                EfficientNetB0 Model (v1.0)
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-slate-400 block text-[10px]">Prescription ID</span>
                <span className="font-bold text-slate-900 font-mono">{task.prescription_id}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Medicines Detected</span>
                <span className="font-bold text-slate-900">{lines.length} lines</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Review Priority</span>
                <PriorityBadge priority={task.priority} size="sm" />
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Primary AI Confidence</span>
                <span className="font-bold text-medical-700">{(task.original_confidence * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Immutable Audit Information */}
          <AuditTrail task={task} />

          {/* Individual Medicine Line Cards Header */}
          <div className="flex items-center justify-between pt-2">
            <h2 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <span>Individual Medicine Line Predictions</span>
              <span className="text-xs font-semibold text-slate-500">({lines.length} items)</span>
            </h2>

            <button
              onClick={() => setIsFocusModeOpen(true)}
              className="text-xs font-bold text-medical-600 hover:text-medical-700 underline"
            >
              Launch Focus Mode →
            </button>
          </div>

          {/* Medicine Line Cards List */}
          <div className="space-y-4">
            {lines.map((line, idx) => (
              <MedicineLineCard
                key={line.line_number || idx}
                line={line}
                index={idx}
                isSelected={selectedIndex === idx}
                onSelect={() => setSelectedIndex(idx)}
                onConfirm={handleConfirmLine}
                onOpenCorrectModal={(l) => setCorrectModalLine(l)}
                onOpenOODModal={(l) => setOodModalLine(l)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Sticky Bottom Progress Bar */}
      <ReviewProgress
        totalLines={lines.length}
        reviewedCount={reviewedCount}
        onOpenFocusMode={() => setIsFocusModeOpen(true)}
        onConfirmAll={handleConfirmAll}
        onSubmitFullReview={handleSubmitFullReview}
      />

      {/* Modals */}
      <MedicineSearchModal
        isOpen={Boolean(correctModalLine)}
        line={correctModalLine}
        onClose={() => setCorrectModalLine(null)}
        onSelectBrand={handleSelectCorrectBrand}
      />

      <OODModal
        isOpen={Boolean(oodModalLine)}
        line={oodModalLine}
        onClose={() => setOodModalLine(null)}
        onSubmitOOD={handleSubmitOOD}
      />

      <FocusModeModal
        isOpen={isFocusModeOpen}
        lines={lines}
        onClose={() => setIsFocusModeOpen(false)}
        onConfirm={handleConfirmLine}
        onOpenCorrectModal={(l) => setCorrectModalLine(l)}
        onOpenOODModal={(l) => setOodModalLine(l)}
      />
    </div>
  );
};
