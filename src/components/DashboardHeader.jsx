import React from 'react';
import { useNavigate } from 'react-router-dom';
import { auth } from '../lib/firebaseClient';
import { signOut } from 'firebase/auth';

export default function DashboardHeader({ title, role }) {
  const navigate = useNavigate();

  const onLogout = async () => {
    try {
      localStorage.removeItem('app_token');
      await signOut(auth);
    } catch (_) {}
    navigate('/');
  };

  return (
    <header className="w-full bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600" />
        <div>
          <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
          {role && (
            <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 uppercase tracking-wide">
              {role}
            </span>
          )}
        </div>
      </div>
      <button
        onClick={onLogout}
        className="px-4 py-2 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50"
      >
        Logout
      </button>
    </header>
  );
}
