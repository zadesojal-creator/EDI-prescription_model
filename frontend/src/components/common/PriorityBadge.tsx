import React from 'react';

interface PriorityBadgeProps {
  priority: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  size?: 'sm' | 'md' | 'lg';
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, size = 'md' }) => {
  const normalized = priority.toUpperCase();

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';
  if (normalized === 'HIGH') {
    colorClasses = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (normalized === 'MEDIUM') {
    colorClasses = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (normalized === 'LOW') {
    colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  }

  const sizeClasses =
    size === 'sm'
      ? 'px-2 py-0.5 text-[10px]'
      : size === 'lg'
      ? 'px-3.5 py-1 text-xs tracking-wider'
      : 'px-2.5 py-0.5 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-bold uppercase rounded-full border ${colorClasses} ${sizeClasses}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          normalized === 'HIGH'
            ? 'bg-rose-500'
            : normalized === 'MEDIUM'
            ? 'bg-amber-500'
            : 'bg-emerald-500'
        }`}
      />
      {normalized} PRIORITY
    </span>
  );
};
