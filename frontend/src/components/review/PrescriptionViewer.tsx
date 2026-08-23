import React, { useState } from 'react';
import {
  ZoomIn,
  ZoomOut,
  Maximize,
  RotateCw,
  RefreshCw,
  Eye
} from 'lucide-react';
import { BoundingBoxOverlay } from './BoundingBoxOverlay';
import { MedicineLine } from '../../types';

interface PrescriptionViewerProps {
  imageReference: string;
  lines?: MedicineLine[];
  selectedLineIndex?: number | null;
  onSelectLine?: (index: number) => void;
}

export const PrescriptionViewer: React.FC<PrescriptionViewerProps> = ({
  imageReference,
  lines = [],
  selectedLineIndex = null,
  onSelectLine
}) => {
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Convert raw filesystem path (e.g. D:\ediprjcursor\data\uploads\img.jpg) to browser endpoint URL
  const getImageSrc = (ref: string) => {
    if (!ref) return '/data/sample_prescription_multiline.png';
    if (ref.startsWith('http') || ref.startsWith('/')) return ref;
    const filename = ref.split(/[/\\]/).pop();
    return `/api/image/${filename}`;
  };

  const imgSrc = getImageSrc(imageReference);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5));
  const handleReset = () => {
    setZoom(1);
    setRotation(0);
  };
  const handleRotate = () => setRotation(prev => (prev + 90) % 360);

  return (
    <div className={`flex flex-col bg-slate-900 rounded-xl overflow-hidden border border-slate-800 shadow-md ${isFullscreen ? 'fixed inset-4 z-50 bg-slate-950' : 'h-full min-h-[480px]'}`}>
      {/* Toolbar */}
      <div className="bg-slate-800/90 px-4 py-2.5 flex items-center justify-between border-b border-slate-700/80 text-slate-300 text-xs font-medium">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-medical-500" />
          <span className="font-semibold text-slate-200">Prescription Page Viewer</span>
          <span className="text-slate-500">({Math.round(zoom * 100)}%)</span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleZoomIn}
            className="p-1.5 hover:bg-slate-700 rounded text-slate-300 hover:text-white transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1.5 hover:bg-slate-700 rounded text-slate-300 hover:text-white transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleRotate}
            className="p-1.5 hover:bg-slate-700 rounded text-slate-300 hover:text-white transition-colors"
            title="Rotate 90°"
          >
            <RotateCw className="w-4 h-4" />
          </button>
          <button
            onClick={handleReset}
            className="p-1.5 hover:bg-slate-700 rounded text-slate-300 hover:text-white transition-colors"
            title="Reset Zoom & Rotation"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <div className="w-px h-4 bg-slate-700 mx-1" />
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 hover:bg-slate-700 rounded text-slate-300 hover:text-white transition-colors"
            title="Toggle Fullscreen"
          >
            <Maximize className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Image Canvas Container */}
      <div className="flex-1 overflow-auto p-4 flex items-center justify-center relative bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px]">
        <div
          className="relative transition-transform duration-200 ease-out max-w-full"
          style={{
            transform: `scale(${zoom}) rotate(${rotation}deg)`,
            transformOrigin: 'center center'
          }}
        >
          <img
            src={imgSrc}
            alt="Prescription Document"
            className="rounded shadow-xl max-h-[600px] object-contain border border-slate-800"
            onError={(e) => {
              // Fallback to sample image if image not found
              (e.target as HTMLImageElement).src = '/data/sample_prescription_multiline.png';
            }}
          />

          {/* Interactive Bounding Box Overlay */}
          <BoundingBoxOverlay
            lines={lines}
            selectedIndex={selectedLineIndex}
            onSelect={onSelectLine}
          />
        </div>
      </div>
    </div>
  );
};
