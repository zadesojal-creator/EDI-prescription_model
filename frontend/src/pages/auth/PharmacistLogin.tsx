import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Pill, Lock, Mail, ShieldCheck, ArrowRight } from 'lucide-react';
import { authApi } from '../../services/authApi';

export const PharmacistLogin: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('pharmacist@clinic.org');
  const [password, setPassword] = useState('pharmacist123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await authApi.login({ email, password, role: 'PHARMACIST' });
      setLoading(false);
      navigate('/pharmacist/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid pharmacist credentials.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6 text-slate-100 font-sans">
      <div className="max-w-md w-full bg-slate-800 border border-slate-700/80 rounded-2xl p-8 shadow-2xl space-y-6">
        {/* Header Logo */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-medical-700 to-medical-500 flex items-center justify-center text-white font-bold text-2xl mx-auto shadow-lg">
            M
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">MediVerify AI</h1>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-medical-500/20 text-medical-300 border border-medical-500/30 text-xs font-bold uppercase tracking-wider">
            <Pill className="w-3.5 h-3.5" />
            Pharmacist Verification Portal
          </div>
          <p className="text-xs text-slate-400 font-medium">
            AI-assisted handwritten prescription processing & pharmacy dispensing
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs font-medium">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Pharmacist Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-medical-500"
                placeholder="pharmacist@clinic.org"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-medical-500"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-medical-600 hover:bg-medical-700 font-bold text-sm text-white shadow-lg flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
          >
            <span>{loading ? "Signing In..." : "Sign In to Pharmacist Portal"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Footer & Switch Role Link */}
        <div className="pt-4 border-t border-slate-700/60 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Secure Session
          </span>
          <button
            onClick={() => navigate('/doctor/login')}
            className="text-medical-400 hover:text-medical-300 font-bold"
          >
            Switch to Doctor Login →
          </button>
        </div>
      </div>
    </div>
  );
};
