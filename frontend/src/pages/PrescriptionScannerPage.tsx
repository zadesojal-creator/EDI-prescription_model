import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  RefreshCw,
  Send
} from 'lucide-react';
import { apiClient } from '../services/api';
import { PriorityBadge } from '../components/common/PriorityBadge';

export const PrescriptionScannerPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  };

  const handleScanPrescription = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await apiClient.post('/api/predict?doctor_email=zadesojal@gmail.com', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(res.data);
      setLoading(false);
    } catch (err: any) {
      console.error("Scan error:", err);
      setError(err.response?.data?.detail || "Failed to analyze prescription image. Ensure FastAPI server is running.");
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="px-2.5 py-1 rounded-full bg-medical-50 text-medical-700 font-bold text-xs border border-medical-100 uppercase tracking-wider">
            Patient / Pharmacist Scanner Portal
          </span>
          <h1 className="text-2xl font-bold text-slate-900 mt-1 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-medical-600" />
            Scan Handwritten Prescription Page
          </h1>
          <p className="text-xs text-slate-500 font-medium">
            Upload any handwritten prescription image to detect medicine lines, predict brand names, and map generic formulations.
          </p>
        </div>

        <button
          onClick={() => navigate('/doctor/dashboard')}
          className="px-4 py-2 rounded-xl bg-slate-900 text-white hover:bg-slate-800 font-bold text-xs shadow-xs cursor-pointer"
        >
          Switch to Doctor Console →
        </button>
      </div>

      {/* Main Upload & Results Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Image Upload Area (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white border-2 border-dashed border-slate-300 rounded-2xl p-6 text-center hover:border-medical-500 transition-colors bg-gradient-to-b from-slate-50/50 to-white shadow-xs">
            {previewUrl ? (
              <div className="space-y-4">
                <img
                  src={previewUrl}
                  alt="Prescription Preview"
                  className="max-h-80 mx-auto rounded-xl shadow-md border border-slate-200 object-contain"
                />
                <div className="flex justify-center gap-2">
                  <label className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs cursor-pointer">
                    Change Image
                    <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
                  </label>
                </div>
              </div>
            ) : (
              <label className="cursor-pointer block py-8 space-y-3">
                <div className="w-14 h-14 rounded-2xl bg-medical-50 text-medical-600 flex items-center justify-center mx-auto shadow-xs border border-medical-100">
                  <Upload className="w-7 h-7" />
                </div>
                <div>
                  <span className="font-bold text-slate-900 text-sm block">Click or Drag Prescription Image</span>
                  <span className="text-xs text-slate-400 font-medium">Supports JPG, PNG, WEBP prescription photos</span>
                </div>
                <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
              </label>
            )}
          </div>

          <button
            onClick={handleScanPrescription}
            disabled={!selectedFile || loading}
            className="w-full py-3.5 px-4 rounded-xl bg-medical-600 hover:bg-medical-700 disabled:opacity-50 text-white font-bold text-sm shadow-sm flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Segmenting & Analyzing Prescription...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>ANALYZE PRESCRIPTION NOW</span>
              </>
            )}
          </button>

          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Right Column: Scan Results Output (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          {result ? (
            <div className="space-y-4">
              {/* Summary Banner */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 text-sm flex items-center gap-2">
                    <FileText className="w-4 h-4 text-medical-600" />
                    Prescription Analysis Output
                  </span>
                  <PriorityBadge priority={result.review_priority || 'HIGH'} size="sm" />
                </div>

                <div className="p-3 rounded-lg bg-medical-50 border border-medical-100 text-xs text-medical-900 font-medium">
                  📋 Total Prescribed Medicines Line(s) Detected: <strong className="text-medical-950 font-bold">{result.total_medicines_detected}</strong>
                </div>

                {result.email_notification?.email_status === 'SENT' && (
                  <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 font-medium flex items-center gap-2">
                    <Send className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>
                      Doctor verification review request automatically dispatched to <strong>zadesojal@gmail.com</strong>!
                    </span>
                  </div>
                )}
              </div>

              {/* Per-Medicine Cards List */}
              <div className="space-y-3">
                <h3 className="font-bold text-slate-900 text-sm">Detected Medicine Lines ({result.all_medicines?.length || 1})</h3>

                {result.all_medicines?.map((m: any, idx: number) => {
                  const pred = m.prediction;
                  const conf = Math.round(pred.top_confidence * 100);

                  return (
                    <div key={idx} className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                        <span className="font-bold text-xs text-slate-800">Medicine Line #{m.line_number}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          conf >= 90 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                        }`}>
                          {conf}% CONFIDENCE
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div>
                          <span className="text-slate-400 block text-[10px] uppercase font-bold">Top AI Brand</span>
                          <span className="font-bold text-medical-700 text-sm">{pred.top_brand}</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px] uppercase font-bold">Generic Chemical Formulation</span>
                          <span className="font-semibold text-slate-800">{pred.generic_name || 'UNVERIFIED'}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Link to Doctor Portal Review */}
              {result.doctor_review_url && (
                <div className="p-4 rounded-xl bg-slate-900 text-white flex items-center justify-between">
                  <div>
                    <span className="font-bold text-xs block">Doctor Review Portal Link Generated</span>
                    <span className="text-[11px] text-slate-400 font-mono">{result.doctor_review_url}</span>
                  </div>
                  <button
                    onClick={() => navigate(result.doctor_review_url)}
                    className="px-3.5 py-1.5 rounded-lg bg-medical-500 hover:bg-medical-600 text-white font-bold text-xs cursor-pointer"
                  >
                    Open Review →
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-500 shadow-xs space-y-3">
              <FileText className="w-12 h-12 text-slate-300 mx-auto" />
              <h3 className="font-bold text-slate-800 text-sm">Ready to Scan Prescription</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Upload a prescription photo on the left and click <strong>Analyze Prescription Now</strong> to view instant AI medicine line segmentation & predictions.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
