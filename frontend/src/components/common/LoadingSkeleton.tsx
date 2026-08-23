import React from 'react';

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-slate-200 rounded-lg w-1/3" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="h-28 bg-slate-200 rounded-xl" />
        <div className="h-28 bg-slate-200 rounded-xl" />
        <div className="h-28 bg-slate-200 rounded-xl" />
      </div>
      <div className="h-64 bg-slate-200 rounded-xl" />
    </div>
  );
};
