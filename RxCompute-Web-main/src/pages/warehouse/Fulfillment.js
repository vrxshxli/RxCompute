import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { Btn, PageHeader } from '../../components/shared';
import { Play, CheckCircle, PackageCheck, PlusCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function WarehouseFulfillment() {
  const { token, apiBase } = useAuth();
  const [orders, setOrders] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [savingOrderId, setSavingOrderId] = useState(null);
  const [showStockAdd, setShowStockAdd] = useState(false);
  const [stockForm, setStockForm] = useState({ medicineId: "", units: "10" });
  const [stockMsg, setStockMsg] = useState("");

  const load = async () => {
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const [ordersRes, medsRes] = await Promise.all([
        fetch(`${apiBase}/orders/`, { headers }),
        fetch(`${apiBase}/medicines/?limit=500`, { headers }),
      ]);
      if (ordersRes.ok) {
        const data = await ordersRes.json();
        setOrders(Array.isArray(data) ? data : []);
      }
      if (medsRes.ok) {
        const data = await medsRes.json();
        setMedicines(Array.isArray(data) ? data : []);
      }
    } catch (_) {}
  };

  useEffect(() => {
    load();
  }, [token, apiBase]);

  const updateOrderStatus = async (orderId, status) => {
    if (!token) return;
    setSavingOrderId(orderId);
    try {
      await fetch(`${apiBase}/orders/${orderId}/status`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
      });
      await load();
    } catch (_) {
    } finally {
      setSavingOrderId(null);
    }
  };

  const addStock = async () => {
    if (!token || !stockForm.medicineId || Number(stockForm.units) <= 0) {
      setStockMsg("Choose medicine and valid units");
      return;
    }
    setStockMsg("");
    try {
      const res = await fetch(`${apiBase}/medicines/${stockForm.medicineId}/add-stock?units=${Number(stockForm.units)}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setStockMsg(data?.detail || "Unable to add stock");
        return;
      }
      setStockMsg("Stock updated");
      await load();
    } catch (_) {
      setStockMsg("Network error while adding stock");
    }
  };

  const tasks = useMemo(
    () =>
      orders
        .filter((o) => ["verified", "confirmed", "picking", "packed", "dispatched"].includes(o.status))
        .map((o) => {
          let stage = "dispatched";
          if (o.status === "verified" || o.status === "confirmed") stage = "ready_to_pick";
          if (o.status === "picking") stage = "picking";
          if (o.status === "packed") stage = "ready_to_pack";
          return {
            ...o,
            ts: stage,
            rack: `Rack ${String.fromCharCode(65 + (o.id % 6))}${Math.floor((o.id || 1) / 6) + 1}`,
          };
        }),
    [orders],
  );

  const sc = { ready_to_pick: T.blue, picking: T.yellow, ready_to_pack: T.green, dispatched: T.gray400 };
  const sl = { ready_to_pick: "Ready to Pick", picking: "Picking", ready_to_pack: "Ready to Send", dispatched: "Dispatched" };

  return (
    <div>
      <PageHeader
        title="Fulfillment Queue"
        badge={String(tasks.length)}
        actions={<Btn variant="secondary" size="sm" onClick={() => setShowStockAdd((v) => !v)}><PlusCircle size={12} />{showStockAdd ? "Close Intake" : "Add Warehouse Stock"}</Btn>}
      />
      {showStockAdd ? (
        <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14, marginBottom: 12 }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr auto", gap: 8 }}>
            <select value={stockForm.medicineId} onChange={(e) => setStockForm({ ...stockForm, medicineId: e.target.value })} style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }}>
              <option value="">Select medicine</option>
              {medicines.map((m) => <option key={m.id} value={m.id}>{m.name} (stock: {m.stock || 0})</option>)}
            </select>
            <input value={stockForm.units} onChange={(e) => setStockForm({ ...stockForm, units: e.target.value })} placeholder="Units" type="number" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
            <Btn variant="primary" size="sm" onClick={addStock}>Add</Btn>
          </div>
          {stockMsg ? <div style={{ marginTop: 8, fontSize: 12, color: stockMsg === "Stock updated" ? T.green : T.red }}>{stockMsg}</div> : null}
        </div>
      ) : null}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {tasks.map((t) => (
          <div key={t.id} style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 16, borderLeft: `4px solid ${sc[t.ts] || T.gray400}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ fontFamily: "monospace", fontSize: 12, fontWeight: 600 }}>{t.order_uid}</span>
                <span style={{ background: `${sc[t.ts] || T.gray400}15`, color: sc[t.ts], padding: "3px 10px", borderRadius: 6, fontSize: 10, fontWeight: 700, textTransform: "uppercase" }}>{sl[t.ts]}</span>
              </div>
              <span style={{ fontSize: 12, color: T.gray400 }}>to {t.pharmacy || "-"}</span>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
              {(t.items || []).map((x, i) => (
                <div key={i} style={{ padding: "8px 14px", background: T.gray50, borderRadius: 8, fontSize: 12, display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ fontWeight: 500, color: T.gray800 }}>{(x.name || "").split(" ").slice(0, 3).join(" ")}</span>
                  <span style={{ color: T.blue, fontWeight: 700 }}>x{x.quantity}</span>
                  <span style={{ color: T.gray400, fontSize: 10 }}>{t.rack}</span>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              {t.ts === "ready_to_pick" && <Btn variant="primary" size="sm" disabled={savingOrderId === t.id} onClick={() => updateOrderStatus(t.id, "picking")}><Play size={12} />Start Pick</Btn>}
              {t.ts === "picking" && <Btn variant="success" size="sm" disabled={savingOrderId === t.id} onClick={() => updateOrderStatus(t.id, "packed")}><PackageCheck size={12} />Mark Packed</Btn>}
              {t.ts === "ready_to_pack" && <Btn variant="primary" size="sm" disabled={savingOrderId === t.id} onClick={() => updateOrderStatus(t.id, "dispatched")}><CheckCircle size={12} />Send to Pharmacy</Btn>}
              {t.ts === "dispatched" && <span style={{ fontSize: 12, color: T.green, fontWeight: 600 }}>Done</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}