import React, { useState } from 'react';
import {
  Pill,
  ShieldAlert,
  Info,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  AlertTriangle,
  FileText,
  Activity,
  Zap,
  CheckCircle2
} from 'lucide-react';
import { MedicineInfo } from '../../types';

interface MedicineInfoPanelProps {
  info?: MedicineInfo;
  brandName: string;
}

export const MedicineInfoPanel: React.FC<MedicineInfoPanelProps> = ({ info, brandName }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<'indications' | 'warnings' | 'reactions' | 'interactions'>('indications');

  if (!info) {
    return null;
  }

  const confidencePercent = Math.round((info.match_confidence || 0) * 100);
  const isHighConf = confidencePercent >= 90;
  const isMedConf = confidencePercent >= 75 && confidencePercent < 90;

  return (
    <div className="mt-3 border border-slate-200 rounded-xl bg-slate-50/70 overflow-hidden text-xs">
      {/* Header Bar */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-2.5 bg-gradient-to-r from-slate-100 to-slate-50 hover:bg-slate-100 flex items-center justify-between transition-colors text-left cursor-pointer"
      >
        <div className="flex items-center gap-2">
          <Pill className="w-4 h-4 text-medical-600 shrink-0" />
          <div>
            <span className="font-bold text-slate-900 text-xs">
              Clinical Drug Information & Safety Labeling
            </span>
            <span className="text-[10px] text-slate-500 font-medium block">
              Powered by RxNorm & openFDA Free APIs
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
            isHighConf ? 'bg-emerald-100 text-emerald-800' :
            isMedConf ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'
          }`}>
            {isHighConf ? 'HIGH MATCH' : isMedConf ? 'MEDIUM MATCH' : 'LOW MATCH'} ({confidencePercent}%)
          </span>

          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-3 space-y-3 bg-white border-t border-slate-200">
          {/* Metadata Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200/80 text-[11px]">
            <div>
              <span className="text-slate-400 block text-[9px] uppercase font-bold">Standardized Name</span>
              <span className="font-bold text-slate-900">{info.normalized_name || brandName}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[9px] uppercase font-bold">Active Generic</span>
              <span className="font-bold text-medical-700">{info.generic_name || 'UNVERIFIED'}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[9px] uppercase font-bold">RxCUI Identifier</span>
              <span className="font-mono font-bold text-slate-800">{info.rxcui || 'N/A'}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[9px] uppercase font-bold">Strength / Form</span>
              <span className="font-bold text-slate-800">
                {info.strength || ''} {info.dosage_form || 'Form Unspecified'}
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-200 gap-1 text-[11px]">
            <button
              type="button"
              onClick={() => setActiveTab('indications')}
              className={`px-3 py-1.5 font-bold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'indications'
                  ? 'border-medical-600 text-medical-700 bg-medical-50/50'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              📋 Indications ({info.indications.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('warnings')}
              className={`px-3 py-1.5 font-bold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'warnings'
                  ? 'border-amber-600 text-amber-700 bg-amber-50/50'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              ⚠️ Warnings ({info.warnings.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('reactions')}
              className={`px-3 py-1.5 font-bold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'reactions'
                  ? 'border-rose-600 text-rose-700 bg-rose-50/50'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              ⚡ Side Effects ({info.adverse_reactions.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('interactions')}
              className={`px-3 py-1.5 font-bold border-b-2 transition-colors cursor-pointer ${
                activeTab === 'interactions'
                  ? 'border-purple-600 text-purple-700 bg-purple-50/50'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              🔄 Interactions ({info.drug_interactions.length})
            </button>
          </div>

          {/* Tab Content Display */}
          <div className="p-2.5 rounded-lg bg-slate-50/50 border border-slate-100 max-h-48 overflow-y-auto space-y-2 text-[11px] text-slate-700 leading-relaxed">
            {activeTab === 'indications' && (
              <div>
                <span className="font-bold text-slate-900 block mb-1 text-[11px]">
                  Medicine Labelled Indications & Uses:
                </span>
                {info.indications.length > 0 ? (
                  <ul className="list-disc list-inside space-y-1">
                    {info.indications.map((ind, idx) => (
                      <li key={idx} className="text-slate-800">{ind}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-slate-400 italic">No specific openFDA indication label records available for this compound.</p>
                )}
              </div>
            )}

            {activeTab === 'warnings' && (
              <div>
                <span className="font-bold text-amber-900 block mb-1 text-[11px]">
                  Warnings, Precautions & Boxed Warnings:
                </span>
                {info.warnings.length > 0 ? (
                  <ul className="list-disc list-inside space-y-1 text-amber-900 font-medium">
                    {info.warnings.map((warn, idx) => (
                      <li key={idx}>{warn}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-slate-400 italic">No specific openFDA warnings records available for this compound.</p>
                )}
              </div>
            )}

            {activeTab === 'reactions' && (
              <div>
                <span className="font-bold text-rose-900 block mb-1 text-[11px]">
                  Adverse Reactions & Side Effects:
                </span>
                {info.adverse_reactions.length > 0 ? (
                  <ul className="list-disc list-inside space-y-1 text-rose-900">
                    {info.adverse_reactions.map((react, idx) => (
                      <li key={idx}>{react}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-slate-400 italic">No specific adverse reactions records available for this compound.</p>
                )}
              </div>
            )}

            {activeTab === 'interactions' && (
              <div>
                <span className="font-bold text-purple-900 block mb-1 text-[11px]">
                  Known Drug-Drug Interactions:
                </span>
                {info.drug_interactions.length > 0 ? (
                  <ul className="list-disc list-inside space-y-1 text-purple-900">
                    {info.drug_interactions.map((inter, idx) => (
                      <li key={idx}>{inter}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-slate-400 italic">No specific drug interaction records available for this compound.</p>
                )}
              </div>
            )}
          </div>

          {/* Sources & Clinical Safety Notice */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2 border-t border-slate-100 text-[10px] text-slate-500">
            <div className="flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>Data Sources: <strong>{info.source?.normalization || 'RxNorm'}</strong> + <strong>{info.source?.clinical_label || 'openFDA'}</strong></span>
            </div>

            <div className="text-[9px] text-slate-400 italic">
              ⚖ Decision-support data from public NLM & FDA datasets. Does NOT constitute a patient diagnosis.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
