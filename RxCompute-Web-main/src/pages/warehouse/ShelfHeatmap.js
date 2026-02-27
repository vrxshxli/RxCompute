import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { PageHeader } from '../../components/shared';
import { Zap } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function WarehouseShelfHeatmap() {
  const { token, apiBase } = useAuth();
  const [medicines, setMedicines] = useState([]);

  const load = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${apiBase}/medicines/?limit=500`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setMedicines(Array.isArray(data) ? data : []);
    } catch (_) {}
  };

  useEffect(() => {
    load();
  }, [token, apiBase]);

  const reorder = useMemo(() => medicines.filter((m) => (m.stock || 0) < 25).slice(0, 5), [medicines]);
  return (
    <div>
      <PageHeader title="Shelf Heatmap" />
      <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
        {[["Healthy", T.green], ["Low", T.yellow], ["Critical", T.red], ["Out", T.gray900]].map(([l, c]) => <div key={l} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: T.gray600 }}><span style={{ width: 16, height: 16, borderRadius: 4, background: c }} />{l}</div>)}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 16 }}>
        <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 24 }}><div style={{ display: "grid", gridTemplateColumns: "repeat(8,1fr)", gap: 8 }}>{medicines.map((m) => { const stock = m.stock || 0; const c = stock > 50 ? T.green : stock > 20 ? T.yellow : stock > 0 ? T.red : T.gray900; return <div key={m.id} title={m.name} style={{ height: 60, borderRadius: 8, background: c, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", cursor: "pointer", transition: "transform .15s", color: T.white, fontWeight: 700 }} onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.1)"; }} onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; }}><span style={{ fontSize: 15 }}>{stock}</span><span style={{ fontSize: 8, opacity: 0.8 }}>{m.name.split(" ")[0]}</span></div>; })}</div></div>
        <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 20 }}><div style={{ fontWeight: 600, fontSize: 14, color: T.gray900, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}><Zap size={16} color={T.orange} />Auto-Reorder</div>{reorder.map((m) => <div key={m.id} style={{ padding: "10px 0", borderBottom: `1px solid ${T.gray100}` }}><div style={{ fontWeight: 500, fontSize: 13, color: T.gray800 }}>{m.name}</div><div style={{ fontSize: 11, color: T.gray500, marginTop: 2 }}>Stock: {m.stock || 0}</div><div style={{ fontSize: 11, color: T.orange, marginTop: 2 }}>Suggest: {Math.max(30, 80 - (m.stock || 0))} units</div></div>)}</div>
      </div>
    </div>
  );
}