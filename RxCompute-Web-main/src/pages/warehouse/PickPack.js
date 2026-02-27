import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { Btn, PageHeader } from '../../components/shared';
import { CheckCircle, Map } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function WarehousePickPack() {
  const { token, apiBase } = useAuth();
  const [orders, setOrders] = useState([]);
  const [savingOrderId, setSavingOrderId] = useState(null);

  const load = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${apiBase}/orders/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setOrders(Array.isArray(data) ? data : []);
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

  const items = useMemo(
    () =>
      orders
        .filter((o) => ["verified", "confirmed", "picking", "packed"].includes(o.status))
        .flatMap((o) =>
          (o.items || []).map((it) => ({
            ...it,
            orderId: o.id,
            oid: o.order_uid,
            orderStatus: o.status,
            rack: `Rack ${String.fromCharCode(65 + ((it.medicine_id || 0) % 6))}`,
            shelf: `Shelf ${((it.medicine_id || 0) % 4) + 1}`,
          })),
        )
        .slice(0, 24),
    [orders],
  );

  return (
    <div>
      <PageHeader title="Pick & Pack" subtitle="Grouped by rack from live warehouse queue" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(280px,1fr))", gap: 12 }}>
        {items.map((x, i) => {
          const done = x.orderStatus === "packed" || x.orderStatus === "dispatched";
          const isPicking = x.orderStatus === "picking";
          const canStartPick = x.orderStatus === "verified" || x.orderStatus === "confirmed";
          return (
            <div key={`${x.orderId}-${i}`} style={{ background: T.white, border: `1px solid ${done ? T.green : T.gray200}`, borderRadius: 10, padding: 16, opacity: done ? 0.75 : 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontFamily: "monospace", fontSize: 11, color: T.gray500 }}>{x.oid}</span>
                {done && <CheckCircle size={16} color={T.green} />}
              </div>
              <div style={{ fontWeight: 500, color: T.gray900, marginBottom: 4 }}>{x.name}</div>
              <div style={{ fontSize: 12, color: T.gray500, marginBottom: 8 }}>Qty: {x.quantity}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: `${T.blue}08`, borderRadius: 8, fontSize: 12 }}>
                <Map size={14} color={T.blue} />
                <span style={{ color: T.blue, fontWeight: 600 }}>{x.rack}, {x.shelf}</span>
              </div>
              {canStartPick && <Btn variant="primary" size="sm" style={{ marginTop: 10, width: "100%" }} disabled={savingOrderId === x.orderId} onClick={() => updateOrderStatus(x.orderId, "picking")}><CheckCircle size={12} />Pick</Btn>}
              {isPicking && <Btn variant="success" size="sm" style={{ marginTop: 10, width: "100%" }} disabled={savingOrderId === x.orderId} onClick={() => updateOrderStatus(x.orderId, "packed")}><CheckCircle size={12} />Pack</Btn>}
            </div>
          );
        })}
      </div>
    </div>
  );
}