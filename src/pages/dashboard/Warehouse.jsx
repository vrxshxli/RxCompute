import React, { useEffect, useState } from 'react';
import DashboardHeader from '../../components/DashboardHeader';

const API_BASE = 'http://127.0.0.1:8000';

export default function WarehouseDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('app_token');
    if (!token) {
      window.location.href = '/login';
      return;
    }
    fetch(`${API_BASE}/dashboard/warehouse`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (r) => {
        if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message || 'Failed to load dashboard'));
  }, []);

  const role = data?.role || 'warehouse';

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50">
      <DashboardHeader title="Warehouse Dashboard" role={role} />
      <main className="max-w-6xl mx-auto p-6">
        {error && <div className="mb-4 px-4 py-3 bg-red-100 text-red-700 rounded">{error}</div>}
        <div className="grid md:grid-cols-3 gap-6">
          <div className="col-span-2 bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-2">Stock Overview</h2>
            <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">{JSON.stringify(data, null, 2)}</pre>
          </div>
          <div className="bg-white rounded-xl shadow border border-gray-100 p-6">
            <h3 className="text-md font-semibold mb-2">Actions</h3>
            <ul className="space-y-2 text-sm text-emerald-700">
              <li>- Receive shipment</li>
              <li>- Update inventory</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
