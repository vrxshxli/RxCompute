import React, { useEffect, useState } from 'react';
import DashboardHeader from '../../components/DashboardHeader';

const API_BASE = 'http://127.0.0.1:8000';

export default function UserDashboard() {
  const [overview, setOverview] = useState(null);
  const [orders, setOrders] = useState([]);
  const [orderDetail, setOrderDetail] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [locker, setLocker] = useState(null);
  const [reminders, setReminders] = useState(null);
  const [docs, setDocs] = useState(null);
  const [profiles, setProfiles] = useState(null);
  const [addresses, setAddresses] = useState(null);
  const [payments, setPayments] = useState(null);
  const [tickets, setTickets] = useState(null);
  const [settings, setSettings] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('app_token');
    if (!token) {
      window.location.href = '/login';
      return;
    }
    const headers = { Authorization: `Bearer ${token}` };
    const fetchJson = async (path) => {
      const r = await fetch(`${API_BASE}${path}`, { headers });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
      return r.json();
    };
    (async () => {
      try {
        setLoading(true);
        const [ov, ord, sug, loc, rem, d, prof, addr, pay, tkt, setg] = await Promise.all([
          fetchJson('/user/overview'),
          fetchJson('/user/orders'),
          fetchJson('/user/refill/suggestions'),
          fetchJson('/user/locker'),
          fetchJson('/user/reminders'),
          fetchJson('/user/docs'),
          fetchJson('/user/profiles'),
          fetchJson('/user/account/addresses'),
          fetchJson('/user/account/payments'),
          fetchJson('/user/support/tickets'),
          fetchJson('/user/settings'),
        ]);
        setOverview(ov);
        setOrders(ord.items || []);
        setSuggestions(sug);
        setLocker(loc);
        setReminders(rem);
        setDocs(d);
        setProfiles(prof);
        setAddresses(addr);
        setPayments(pay);
        setTickets(tkt);
        setSettings(setg);
      } catch (e) {
        setError(e.message || 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const role = 'user';

  const token = typeof window !== 'undefined' ? localStorage.getItem('app_token') : null;
  const authorizedFetch = (path, options = {}) => {
    return fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
        ...(options.headers || {}),
      },
    });
  };

  const handleRefill = async (orderId) => {
    try {
      const r = await authorizedFetch(`/user/orders/${orderId}/refill`, { method: 'POST' });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
      const res = await r.json();
      alert(`Refill placed. New Order: ${res.new_order_id}`);
    } catch (e) {
      alert(e.message || 'Refill failed');
    }
  };

  const viewOrder = async (orderId) => {
    try {
      const r = await authorizedFetch(`/user/orders/${orderId}`);
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
      setOrderDetail(await r.json());
    } catch (e) {
      alert(e.message || 'Failed to load order');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50">
      <DashboardHeader title="User Dashboard" role={role} />
      <main className="max-w-7xl mx-auto p-6">
        {error && <div className="mb-4 px-4 py-3 bg-red-100 text-red-700 rounded">{error}</div>}
        {loading && <div className="mb-4 px-4 py-3 bg-emerald-100 text-emerald-800 rounded">Loading dashboard</div>}

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Smart Overview */}
          <section className="lg:col-span-2 bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4">Smart Overview</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-semibold mb-2">Active Medicines</h3>
                <ul className="space-y-2 text-sm">
                  {(overview?.active_medicines || []).map((m, i) => (
                    <li key={i} className="flex justify-between border rounded p-2">
                      <span>{m.name}  {m.dose}</span>
                      <span className="text-gray-500">{m.purpose}  {m.doctor}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Todays Schedule</h3>
                <ul className="space-y-2 text-sm">
                  {(overview?.today_schedule || []).map((s, i) => (
                    <li key={i} className="flex justify-between border rounded p-2">
                      <span>{s.text}</span>
                      <span className="text-gray-500">{s.time}</span>
                    </li>
                  ))}
                </ul>
                <h3 className="font-semibold mt-4 mb-2">Refill Alerts</h3>
                <ul className="space-y-2 text-sm">
                  {(overview?.refill_alerts || []).map((r, i) => (
                    <li key={i} className="flex justify-between items-center border rounded p-2">
                      <span>{r.text}</span>
                      <button onClick={() => alert('Reorder flow')} className="px-3 py-1 text-sm rounded bg-emerald-600 text-white">Reorder</button>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>

          {/* Orders & Refills */}
          <section className="bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4">Orders & Refills</h2>
            <ul className="space-y-3 text-sm">
              {orders.map((o) => (
                <li key={o.id} className="border rounded p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{o.id}</div>
                      <div className="text-gray-500">{o.date}  ₹{o.total}</div>
                    </div>
                    <span className="px-2 py-1 rounded text-xs bg-gray-100">{o.status}</span>
                  </div>
                  <div className="mt-2 flex gap-2">
                    <button onClick={() => handleRefill(o.id)} className="px-3 py-1 rounded bg-emerald-600 text-white text-xs">One-tap Refill</button>
                    <button onClick={() => viewOrder(o.id)} className="px-3 py-1 rounded border text-xs">Details</button>
                  </div>
                </li>
              ))}
            </ul>
            {orderDetail && (
              <div className="mt-4 bg-gray-50 p-3 rounded text-xs">
                <div className="font-semibold mb-1">Order {orderDetail.id}</div>
                <div>Status: {orderDetail.status}</div>
                <div className="mt-1">Payment: {orderDetail.payment_method}  Address: {orderDetail.address}</div>
                <div className="mt-1">Items:</div>
                <ul className="list-disc ml-5">
                  {orderDetail.items?.map((it, idx) => (
                    <li key={idx}>{it.name}  {it.qty} — ₹{it.price}</li>
                  ))}
                </ul>
                <div className="mt-2 flex gap-2">
                  <a href={orderDetail.invoice_url} target="_blank" rel="noreferrer" className="text-emerald-700 underline">Invoice</a>
                  <a href={orderDetail.qr_url} target="_blank" rel="noreferrer" className="text-emerald-700 underline">QR Bill</a>
                </div>
              </div>
            )}
          </section>
        </div>

        {/* Smart Refill Suggestions (AI) */}
        <section className="mt-6 grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4">Smart Refill Suggestions</h2>
            <div className="text-sm">
              <div className="font-semibold mb-2">Recommended</div>
              <ul className="list-disc ml-5 mb-3">
                {(suggestions?.recommended || []).map((x, i) => (
                  <li key={i}>{x.name} — {x.reason}</li>
                ))}
              </ul>
              <div className="font-semibold mb-2">Missed</div>
              <ul className="list-disc ml-5">
                {(suggestions?.missed || []).map((x, i) => (
                  <li key={i}>{x.name} — {x.note}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow border border-gray-100 p-6">
            <h3 className="font-semibold mb-2">Auto-remind</h3>
            <div className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={!!suggestions?.auto_remind} readOnly />
              <span>Auto-remind me before medicine finishes</span>
            </div>
          </div>
        </section>

        {/* Medicine Locker */}
        <section className="mt-6 bg-white rounded-xl shadow border border-gray-100 p-6">
          <h2 className="text-lg font-semibold mb-4">Medicine Locker</h2>
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            {(locker?.medicines || []).map((m, i) => (
              <div key={i} className="border rounded p-3">
                <div className="font-medium">{m.name}</div>
                <div className="text-gray-600">{m.dosage}  {m.frequency}</div>
                <div className="text-gray-500">{(m.times||[]).join(', ')}</div>
                <div className="mt-2 flex gap-2 flex-wrap">
                  {(m.tags || []).map((t, j) => (
                    <span key={j} className="px-2 py-0.5 text-xs rounded bg-emerald-100 text-emerald-800">{t}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Reminders & Notifications */}
        <section className="mt-6 grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4">Reminders</h2>
            <ul className="space-y-2 text-sm">
              {(reminders?.schedule || []).map((r, i) => (
                <li key={i} className="flex justify-between border rounded p-2">
                  <span>{r.medicine} — {(r.times||[]).join(', ')}</span>
                  <span className="text-gray-500">{r.enabled ? 'On' : 'Off'}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-white rounded-xl shadow border border-gray-100 p-6">
            <h3 className="font-semibold mb-2">Notifications</h3>
            <ul className="space-y-2 text-sm max-h-60 overflow-auto">
              {(reminders?.notifications || []).map((n, i) => (
                <li key={i} className="border rounded p-2">
                  <div className="font-medium capitalize">{n.type}</div>
                  <div className="text-gray-600">{n.text}</div>
                  <div className="text-gray-400 text-xs">{n.ts}</div>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Prescription & Documents Vault */}
        <section className="mt-6 grid lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4">Prescriptions</h2>
            <ul className="space-y-2 text-sm">
              {(docs?.prescriptions || []).map((p) => (
                <li key={p.id} className="flex items-center justify-between border rounded p-2">
                  <div>
                    <div className="font-medium">{p.id}</div>
                    <div className="text-gray-500">Rx required: {p.rx_required ? 'Yes' : 'No'}  Expires {p.expires}</div>
                  </div>
                  <a href={p.file} target="_blank" rel="noreferrer" className="text-emerald-700 underline">Open</a>
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4">Invoices</h2>
            <ul className="space-y-2 text-sm">
              {(docs?.invoices || []).map((inv) => (
                <li key={inv.order_id} className="flex items-center justify-between border rounded p-2">
                  <div className="font-medium">{inv.order_id}</div>
                  <a href={inv.file} target="_blank" rel="noreferrer" className="text-emerald-700 underline">Download</a>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Family Profiles */}
        <section className="mt-6 bg-white rounded-xl shadow border border-gray-100 p-6">
          <h2 className="text-lg font-semibold mb-4">Family Profiles</h2>
          <div className="flex items-center gap-3">
            {(profiles?.list || []).map((p) => (
              <span key={p.id} className={`px-3 py-1 rounded text-sm ${profiles?.active === p.id ? 'bg-emerald-600 text-white' : 'bg-gray-100'}`}>{p.name}</span>
            ))}
          </div>
          <div className="mt-3 text-sm text-gray-600">Active: {profiles?.active}</div>
        </section>

        {/* Safety & Doctor Help */}
        <section className="mt-6 grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4">Safety Warnings</h2>
            <ul className="space-y-2 text-sm">
              <li className="text-gray-500">No active warnings</li>
            </ul>
          </div>
          <div className="bg-white rounded-xl shadow border border-gray-100 p-6">
            <h3 className="font-semibold mb-2">Ask AI Pharmacist</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              const q = e.target.q.value;
              e.target.reset();
              try {
                const r = await authorizedFetch('/user/ai/ask', { method: 'POST', body: JSON.stringify({ q }) });
                const res = await r.json();
                alert(res.answer);
              } catch (_) { alert('Failed to ask AI'); }
            }} className="space-y-2 text-sm">
              <input name="q" placeholder="Can I take this with food?" className="w-full border rounded px-3 py-2" />
              <button className="px-3 py-2 rounded bg-emerald-600 text-white text-sm">Ask</button>
            </form>
          </div>
        </section>

        {/* Address & Payment Management */}
        <section className="mt-6 grid lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4">Addresses</h2>
            <ul className="space-y-2 text-sm">
              {(addresses?.items || []).map((a) => (
                <li key={a.id} className="border rounded p-2 flex justify-between">
                  <span>{a.label} — {a.line}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4">Payments</h2>
            <ul className="space-y-2 text-sm">
              {(payments?.items || []).map((p) => (
                <li key={p.id} className="border rounded p-2 flex justify-between">
                  <span className="capitalize">{p.type}</span>
                  <span className="text-gray-500">{p.masked}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Support & Settings */}
        <section className="mt-6 grid lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4">Support Tickets</h2>
            <ul className="space-y-2 text-sm">
              {(tickets?.items || []).map((t) => (
                <li key={t.id} className="border rounded p-2 flex justify-between">
                  <span>{t.subject}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-gray-100">{t.status}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="lg:col-span-2 bg-white rounded-xl shadow border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4">Settings & Privacy</h2>
            <div className="text-sm grid md:grid-cols-2 gap-4">
              <div>
                <div className="font-medium mb-1">Language</div>
                <div className="text-gray-600">{settings?.language?.toUpperCase() || 'EN'}</div>
              </div>
              <div>
                <div className="font-medium mb-1">AI Recommendations</div>
                <div className="text-gray-600">{settings?.ai_recommendations ? 'Enabled' : 'Disabled'}</div>
              </div>
              <div>
                <div className="font-medium mb-1">Data Download</div>
                <div className="text-gray-600">{settings?.gdpr?.download_available ? 'Available' : 'Not available'}</div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}