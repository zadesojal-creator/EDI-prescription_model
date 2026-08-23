import React, { useState } from 'react';
import { Search, X, Pill, Check } from 'lucide-react';
import { REGISTERED_BRANDS_78 } from '../../constants';
import { MedicineLine } from '../../types';

interface MedicineSearchModalProps {
  isOpen: boolean;
  line: MedicineLine | null;
  onClose: () => void;
  onSelectBrand: (line: MedicineLine, selectedBrand: string) => void;
}

export const MedicineSearchModal: React.FC<MedicineSearchModalProps> = ({
  isOpen,
  line,
  onClose,
  onSelectBrand
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  if (!isOpen || !line) return null;

  const filteredBrands = REGISTERED_BRANDS_78.filter(
    (item) =>
      item.brand.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.generic.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[85vh] animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <Pill className="w-5 h-5 text-medical-600" />
              Correct Brand for Line #{line.line_number}
            </h3>
            <p className="text-xs text-slate-500 font-medium">
              Select correct medicine from the 78 registered brand classes
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Live Search Input */}
        <div className="p-4 border-b border-slate-100 bg-white">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              autoFocus
              placeholder="Search by brand name or generic chemical (e.g., Napa, Esomeprazole)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-medical-500 focus:border-medical-500 text-sm font-medium"
            />
          </div>
        </div>

        {/* Brand List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-1 divide-y divide-slate-100">
          {filteredBrands.length > 0 ? (
            filteredBrands.map((item, idx) => (
              <button
                key={idx}
                onClick={() => {
                  onSelectBrand(line, item.brand);
                  onClose();
                }}
                className="w-full pt-2.5 pb-2 px-3 rounded-lg text-left hover:bg-medical-50/60 transition-colors group flex items-center justify-between cursor-pointer"
              >
                <div>
                  <div className="font-bold text-sm text-slate-900 group-hover:text-medical-700">
                    {item.brand}
                  </div>
                  <div className="text-xs text-slate-500 font-medium">
                    Generic: <span className="text-slate-700">{item.generic}</span>
                  </div>
                </div>
                <div className="opacity-0 group-hover:opacity-100 text-xs font-bold text-medical-600 flex items-center gap-1">
                  <span>Select</span>
                  <Check className="w-4 h-4" />
                </div>
              </button>
            ))
          ) : (
            <div className="py-8 text-center text-slate-500 text-xs font-medium">
              No registered brands matching "{searchQuery}".
              <div className="mt-2">
                <span className="text-slate-400">Is this a new unregistered medicine?</span>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-between items-center text-xs">
          <span className="text-slate-500 font-medium">Showing {filteredBrands.length} of 78 brands</span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg font-bold text-slate-600 hover:bg-slate-200 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
