import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  variant?: 'danger' | 'warning' | 'success' | 'info' | 'default';
  actionText?: string;
  onAction?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'default',
  actionText,
  onAction
}) => {
  let borderBorder = 'border-slate-200';
  let iconBg = 'bg-slate-100 text-slate-700';

  if (variant === 'danger') {
    borderBorder = 'border-rose-200 bg-gradient-to-b from-rose-50/40 to-white';
    iconBg = 'bg-rose-100 text-rose-700';
  } else if (variant === 'warning') {
    borderBorder = 'border-amber-200 bg-gradient-to-b from-amber-50/40 to-white';
    iconBg = 'bg-amber-100 text-amber-700';
  } else if (variant === 'success') {
    borderBorder = 'border-emerald-200 bg-gradient-to-b from-emerald-50/40 to-white';
    iconBg = 'bg-emerald-100 text-emerald-700';
  } else if (variant === 'info') {
    borderBorder = 'border-medical-200 bg-gradient-to-b from-medical-50/40 to-white';
    iconBg = 'bg-medical-100 text-medical-700';
  }

  return (
    <div className={`p-5 rounded-xl border bg-white shadow-xs flex flex-col justify-between ${borderBorder}`}>
      <div>
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{title}</span>
          {Icon && (
            <div className={`p-2 rounded-lg ${iconBg}`}>
              <Icon className="w-4 h-4" />
            </div>
          )}
        </div>
        <div className="text-3xl font-extrabold text-slate-900 mt-2">{value}</div>
        {subtitle && <div className="text-xs text-slate-500 mt-1 font-medium">{subtitle}</div>}
      </div>

      {actionText && (
        <button
          onClick={onAction}
          className="mt-4 pt-3 border-t border-slate-100 text-xs font-bold text-medical-600 hover:text-medical-700 flex items-center justify-between group cursor-pointer"
        >
          <span>{actionText}</span>
          <span className="group-hover:translate-x-1 transition-transform">→</span>
        </button>
      )}
    </div>
  );
};
