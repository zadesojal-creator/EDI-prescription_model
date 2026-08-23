import React from 'react';
import { BarChart3, TrendingUp, PieChart as PieIcon, CheckCircle2 } from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';

export const AnalyticsPage: React.FC = () => {
  const pieData = [
    { name: 'AI Confirmed (74%)', value: 74, color: '#38a169' },
    { name: 'Doctor Corrected (19%)', value: 19, color: '#3182ce' },
    { name: 'OOD Medicines (7%)', value: 7, color: '#dd6b20' },
  ];

  const barData = [
    { priority: 'HIGH Priority', confirmed: 12, corrected: 18, ood: 5 },
    { priority: 'MEDIUM Priority', confirmed: 45, corrected: 8, ood: 2 },
    { priority: 'LOW Priority', confirmed: 88, corrected: 4, ood: 1 },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-medical-600" />
          Doctor Feedback & AI Accuracy Analytics
        </h1>
        <p className="text-xs text-slate-500 font-medium mt-0.5">
          Empirical verification metrics and clinical decision-support performance
        </p>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">AI Confirmation Rate</span>
          <div className="text-3xl font-extrabold text-emerald-600 mt-2">74.2%</div>
          <p className="text-xs text-slate-500 mt-1 font-medium">Doctor approved AI predictions without edit</p>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Doctor Correction Rate</span>
          <div className="text-3xl font-extrabold text-medical-600 mt-2">18.8%</div>
          <p className="text-xs text-slate-500 mt-1 font-medium">Brand corrected from 78 registered classes</p>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">OOD Medicines Identified</span>
          <div className="text-3xl font-extrabold text-amber-600 mt-2">7.0%</div>
          <p className="text-xs text-slate-500 mt-1 font-medium">New unregistered medicines submitted</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
            <PieIcon className="w-4 h-4 text-medical-600" />
            Verification Decision Distribution
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bar Chart */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-medical-600" />
            Doctor Actions by Clinical Priority Level
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <XAxis dataKey="priority" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="confirmed" fill="#38a169" name="Confirmed" />
                <Bar dataKey="corrected" fill="#3182ce" name="Corrected" />
                <Bar dataKey="ood" fill="#dd6b20" name="OOD" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
