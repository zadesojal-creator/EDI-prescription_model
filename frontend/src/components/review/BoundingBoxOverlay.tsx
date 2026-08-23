import React from 'react';
import { MedicineLine } from '../../types';

interface BoundingBoxOverlayProps {
  lines: MedicineLine[];
  selectedIndex?: number | null;
  onSelect?: (index: number) => void;
}

export const BoundingBoxOverlay: React.FC<BoundingBoxOverlayProps> = ({
  lines,
  selectedIndex = null,
  onSelect
}) => {
  if (!lines || lines.length === 0) return null;

  // Assume baseline dimensions of sample prescription sheet (641 x 895) for scaling % calculations
  const BASE_H = 641;
  const BASE_W = 895;

  return (
    <div className="absolute inset-0 pointer-events-none">
      {lines.map((line, idx) => {
        const box = line.bounding_box;
        if (!box) return null;

        const isSelected = selectedIndex === idx;
        const topPct = (box.y / BASE_H) * 100;
        const leftPct = (box.x / BASE_W) * 100;
        const widthPct = (box.width / BASE_W) * 100;
        const heightPct = (box.height / BASE_H) * 100;

        const isVerified = line.status === 'CONFIRMED' || line.status === 'CORRECTED';

        return (
          <div
            key={line.line_number || idx}
            onClick={(e) => {
              e.stopPropagation();
              if (onSelect) onSelect(idx);
            }}
            style={{
              top: `${topPct}%`,
              left: `${leftPct}%`,
              width: `${widthPct}%`,
              height: `${heightPct}%`,
            }}
            className={`absolute pointer-events-auto border-2 rounded transition-all cursor-pointer group flex items-start justify-between p-1 ${
              isSelected
                ? 'border-medical-500 bg-medical-500/20 ring-2 ring-medical-400 z-20 shadow-lg'
                : isVerified
                ? 'border-emerald-500/80 bg-emerald-500/10 hover:bg-emerald-500/20'
                : 'border-amber-400/80 bg-amber-400/10 hover:bg-amber-400/25'
            }`}
          >
            <span
              className={`text-[10px] font-bold px-1.5 py-0.5 rounded text-white shadow-xs ${
                isSelected
                  ? 'bg-medical-600'
                  : isVerified
                  ? 'bg-emerald-600'
                  : 'bg-amber-600'
              }`}
            >
              #{line.line_number}
            </span>

            <span className="hidden group-hover:inline-block text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-900/90 text-slate-100 shadow-md">
              {line.prediction.top_brand}
            </span>
          </div>
        );
      })}
    </div>
  );
};
