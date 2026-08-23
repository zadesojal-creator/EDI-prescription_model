import React, { useEffect, useState } from 'react';
import { Bell, CheckCircle2, Send, FileText } from 'lucide-react';
import { pharmacistApi } from '../../services/pharmacistApi';

export const PharmacistNotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<any[]>([]);

  useEffect(() => {
    pharmacistApi.getNotifications().then(res => setNotifications(res.notifications || []));
  }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 font-sans">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Bell className="w-6 h-6 text-medical-600" />
          Pharmacist Notification Center
        </h1>
        <p className="text-xs text-slate-500 font-medium">
          Real-time notifications for doctor review completions and prescription scans
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl divide-y divide-slate-100 shadow-xs">
        {notifications.map((n) => (
          <div key={n.id} className="p-4 flex items-start gap-3">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
              n.type === 'DOCTOR_VERIFIED' ? 'bg-emerald-50 text-emerald-600' : 'bg-medical-50 text-medical-600'
            }`}>
              {n.type === 'DOCTOR_VERIFIED' ? <CheckCircle2 className="w-5 h-5" /> : <Send className="w-5 h-5" />}
            </div>

            <div className="flex-1 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 text-sm">{n.title}</span>
                <span className="text-[10px] text-slate-400 font-medium">{n.timestamp}</span>
              </div>
              <p className="text-xs text-slate-600 font-medium">{n.message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
