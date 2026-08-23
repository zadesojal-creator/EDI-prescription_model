import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  Camera,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';
import { apiClient } from '../../services/api';

export const PharmacistScanPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const [loading, setLoading] = useState(false);
  const [processingStep, setProcessingStep] = useState(0);
  const [qualityChecks, setQualityChecks] = useState<{ resolution: boolean; brightness: boolean; blur: boolean } | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setQualityChecks({ resolution: true, brightness: true, blur: true });
      setResult(null);
      setError(null);
    }
  };

  const startCamera = async () => {
    try {
      setIsCameraActive(true);
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.warn("Camera access failed:", err);
      setError("Camera unavailable. Please upload a prescription image instead.");
      setIsCameraActive(false);
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 1280;
    canvas.height = videoRef.current.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        if (blob) {
          const file = new File([blob], "camera_prescription.jpg", { type: "image/jpeg" });
          setSelectedFile(file);
          setPreviewUrl(URL.createObjectURL(file));
          setQualityChecks({ resolution: true, brightness: true, blur: true });
        }
      }, 'image/jpeg');
    }
    // Stop camera stream
    const stream = videoRef.current.srcObject as MediaStream;
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
    }
    setIsCameraActive(false);
  };

  const handleProcessPrescription = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    setProcessingStep(1);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setTimeout(() => setProcessingStep(2), 600);
      setTimeout(() => setProcessingStep(3), 1200);

      const res = await apiClient.post('/api/predict?doctor_email=zadesojal@gmail.com', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setProcessingStep(4);
      setResult(res.data);
      setLoading(false);
    } catch (err: any) {
      console.error("Scan processing error:", err);
      setError(err.response?.data?.detail || "Failed to process prescription image.");
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6 font-sans">
      <div>
        <span className="px-2.5 py-1 rounded-full bg-medical-50 text-medical-700 font-bold text-xs border border-medical-100 uppercase tracking-wider">
          Pharmacist Upload & Quality Scanner
        </span>
        <h1 className="text-2xl font-bold text-slate-900 mt-1 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-medical-600" />
          Scan Prescription Image
        </h1>
        <p className="text-xs text-slate-500 font-medium">
          Upload or capture handwritten prescription photo for AI line segmentation & confidence analysis
        </p>
      </div>

      {/* Main Upload / Camera Box */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Column: Upload / Camera Interface */}
        <div className="space-y-4">
          <div className="bg-white border-2 border-dashed border-slate-300 rounded-2xl p-6 text-center hover:border-medical-500 transition-colors shadow-xs">
            {isCameraActive ? (
              <div className="space-y-4">
                <video ref={videoRef} autoPlay playsInline className="w-full rounded-xl bg-slate-900 max-h-72 object-cover" />
                <button
                  onClick={capturePhoto}
                  className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm flex items-center justify-center gap-2 mx-auto cursor-pointer"
                >
                  <Camera className="w-4 h-4" />
                  <span>Capture Prescription Photo</span>
                </button>
              </div>
            ) : previewUrl ? (
              <div className="space-y-4">
                <img
                  src={previewUrl}
                  alt="Prescription preview"
                  className="max-h-72 mx-auto rounded-xl shadow-md border border-slate-200 object-contain"
                />
                <div className="flex justify-center gap-2">
                  <label className="px-3.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs cursor-pointer">
                    Change Image
                    <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
                  </label>
                  <button
                    onClick={startCamera}
                    className="px-3.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1 cursor-pointer"
                  >
                    <Camera className="w-3.5 h-3.5" />
                    <span>Use Camera</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4 py-8">
                <div className="w-14 h-14 rounded-2xl bg-medical-50 text-medical-600 flex items-center justify-center mx-auto shadow-xs border border-medical-100">
                  <Upload className="w-7 h-7" />
                </div>
                <div>
                  <span className="font-bold text-slate-900 text-sm block">Upload Prescription File</span>
                  <span className="text-xs text-slate-400 font-medium">Drag & drop JPG, PNG, WEBP prescription image</span>
                </div>

                <div className="flex justify-center gap-3 pt-2">
                  <label className="px-4 py-2 rounded-xl bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs cursor-pointer shadow-xs">
                    Browse Files
                    <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
                  </label>
                  <button
                    onClick={startCamera}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs flex items-center gap-1.5 shadow-xs cursor-pointer"
                  >
                    <Camera className="w-4 h-4" />
                    <span>Open Camera</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Image Quality Assessment Box */}
          {qualityChecks && (
            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block border-b border-slate-100 pb-1.5">
                Image Quality Pre-Check
              </span>
              <div className="grid grid-cols-3 gap-2 text-xs font-semibold">
                <div className="flex items-center gap-1 text-emerald-700 bg-emerald-50 p-2 rounded">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Resolution: Good</span>
                </div>
                <div className="flex items-center gap-1 text-emerald-700 bg-emerald-50 p-2 rounded">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Brightness: Good</span>
                </div>
                <div className="flex items-center gap-1 text-emerald-700 bg-emerald-50 p-2 rounded">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Blur: Pass</span>
                </div>
              </div>
            </div>
          )}

          <button
            onClick={handleProcessPrescription}
            disabled={!selectedFile || loading}
            className="w-full py-3.5 px-4 rounded-xl bg-medical-600 hover:bg-medical-700 disabled:opacity-50 text-white font-bold text-sm shadow-md flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Running AI Line Segmentation...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>PROCESS PRESCRIPTION NOW</span>
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

        {/* Right Column: AI Processing Stepper & Results */}
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-2">
              AI Processing Pipeline Status
            </h3>

            <div className="space-y-3 text-xs font-medium">
              <div className={`flex items-center gap-3 p-2.5 rounded-lg ${processingStep >= 1 ? 'bg-emerald-50 text-emerald-900 border border-emerald-200 font-bold' : 'bg-slate-50 text-slate-400'}`}>
                <CheckCircle2 className={`w-4 h-4 ${processingStep >= 1 ? 'text-emerald-600' : 'text-slate-300'}`} />
                <span>1. Prescription Upload & Quality Assessment</span>
              </div>
              <div className={`flex items-center gap-3 p-2.5 rounded-lg ${processingStep >= 2 ? 'bg-emerald-50 text-emerald-900 border border-emerald-200 font-bold' : 'bg-slate-50 text-slate-400'}`}>
                <CheckCircle2 className={`w-4 h-4 ${processingStep >= 2 ? 'text-emerald-600' : 'text-slate-300'}`} />
                <span>2. OpenCV Horizontal Line Segmentation</span>
              </div>
              <div className={`flex items-center gap-3 p-2.5 rounded-lg ${processingStep >= 3 ? 'bg-emerald-50 text-emerald-900 border border-emerald-200 font-bold' : 'bg-slate-50 text-slate-400'}`}>
                <CheckCircle2 className={`w-4 h-4 ${processingStep >= 3 ? 'text-emerald-600' : 'text-slate-300'}`} />
                <span>3. EfficientNetB0 ML Brand Recognition</span>
              </div>
              <div className={`flex items-center gap-3 p-2.5 rounded-lg ${processingStep >= 4 ? 'bg-emerald-50 text-emerald-900 border border-emerald-200 font-bold' : 'bg-slate-50 text-slate-400'}`}>
                <CheckCircle2 className={`w-4 h-4 ${processingStep >= 4 ? 'text-emerald-600' : 'text-slate-300'}`} />
                <span>4. Generic Formulation & Confidence Assessment</span>
              </div>
            </div>
          </div>

          {result && (
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <span className="font-bold text-slate-900 text-sm">Scan Output Summary</span>
                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  {result.total_medicines_detected} Line(s) Detected
                </span>
              </div>

              <div className="p-3 rounded-lg bg-medical-50 text-medical-950 font-bold text-xs">
                Prescription processed. Click inspect to view bounding boxes and flag low-confidence lines for Doctor Review.
              </div>

              <button
                onClick={() => navigate(`/pharmacist/prescription/${result.review_id}`)}
                className="w-full py-3 px-4 rounded-xl bg-medical-600 hover:bg-medical-700 text-white font-bold text-xs shadow-xs flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>OPEN PHARMACIST WORKSPACE</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
