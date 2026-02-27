import React, { useEffect, useState } from 'react';
import T from '../../utils/tokens';
import { Btn, PageHeader, StatCard } from '../../components/shared';
import { Activity, Bell, Mail, Users, Warehouse } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function AdminSystemHealth() {
  const { token, apiBase } = useAuth();
  const [health, setHealth] = useState(null);
  const [stockBreakdown, setStockBreakdown] = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = async () => {
    if (!token) return;
    setLoading(true);
    setMsg("");
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [healthRes, stockRes] = await Promise.all([
        fetch(`${apiBase}/notifications/delivery-health`, { headers }),
        fetch(`${apiBase}/warehouse/stock-breakdown`, { headers }),
      ]);
      if (healthRes.ok) {
        const data = await healthRes.json();
        setHealth(data);
      }
      if (stockRes.ok) {
        const data = await stockRes.json();
        setStockBreakdown(Array.isArray(data) ? data : []);
      }
      if (!healthRes.ok && !stockRes.ok) {
        setMsg("Unable to load debug health");
      }
    } catch (_) {
      setMsg("Network error while loading debug health");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [token, apiBase]);

  const smtpOk = (health?.smtp?.reachability || []).some((x) => !!x.ok);

  return (
    <div>
      <PageHeader title="System Health" subtitle="Delivery debug + stock breakdown" actions={<Btn variant="secondary" size="sm" onClick={load}>{loading ? "Refreshing..." : "Refresh"}</Btn>} />
      {msg ? <div style={{ marginBottom: 10, color: T.red, fontSize: 12 }}>{msg}</div> : null}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 12, marginBottom: 14 }}>
        <StatCard icon={Mail} label="SMTP Reachability" value={smtpOk ? "OK" : "FAIL"} color={smtpOk ? T.green : T.red} subtitle={health?.smtp?.host || "-"} />
        <StatCard icon={Bell} label="Notifications 24h" value={String(health?.events_24h?.notifications_created || 0)} color={T.blue} />
        <StatCard icon={Users} label="Users With Push Token" value={String(health?.push?.users_with_push_token || 0)} color={T.orange} />
        <StatCard icon={Warehouse} label="Warehouse Pending Outbound" value={String(health?.warehouse?.outbound_transfers_pending || 0)} color={T.blue} />
      </div>
      <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14, marginBottom: 14 }}>
        <div style={{ fontWeight: 700, color: T.gray900, marginBottom: 8, display: "flex", alignItems: "center", gap: 8 }}><Activity size={14} />SMTP Port Reachability</div>
        {(health?.smtp?.reachability || []).map((r, idx) => (
          <div key={idx} style={{ fontSize: 12, color: r.ok ? T.green : T.red, padding: "4px 0" }}>
            {r.host}:{r.port} - {r.ok ? `OK (${r.ip || "resolved"})` : r.error || "failed"}
          </div>
        ))}
      </div>
      <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14 }}>
        <div style={{ fontWeight: 700, color: T.gray900, marginBottom: 8 }}>Medicine Stock Breakdown (Admin vs Warehouse vs Pharmacy)</div>
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 8, fontSize: 11, color: T.gray500, marginBottom: 8 }}>
          <div>Medicine</div><div>Admin</div><div>Warehouse</div><div>Pharmacy</div>
        </div>
        {stockBreakdown.slice(0, 80).map((m) => (
          <div key={m.medicine_id} style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 8, fontSize: 12, padding: "6px 0", borderBottom: `1px solid ${T.gray100}` }}>
            <div>{m.name}</div><div>{m.admin_stock}</div><div>{m.warehouse_stock}</div><div>{m.pharmacy_stock_dispatched}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
