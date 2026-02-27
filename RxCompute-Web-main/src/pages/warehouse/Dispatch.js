import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { StatusPill, Btn, PageHeader } from '../../components/shared';
import { Truck, Package } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function WarehouseDispatch() {
  const { token, apiBase } = useAuth();
  const [transfers, setTransfers] = useState([]);
  const [savingTransferId, setSavingTransferId] = useState(null);

  const load = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${apiBase}/warehouse/transfers?direction=warehouse_to_pharmacy`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setTransfers(Array.isArray(data) ? data : []);
    } catch (_) {}
  };

  useEffect(() => {
    load();
  }, [token, apiBase]);

  const packed = useMemo(
    () =>
      transfers
        .filter((o) => o.status === "packed" || o.status === "dispatched")
        .map((o) => ({ ...o, tracking: o.status === "dispatched" ? `TRK-${String(o.id).padStart(6, "0")}` : null })),
    [transfers],
  );

  const dispatchTransfer = async (transferId) => {
    if (!token) return;
    setSavingTransferId(transferId);
    try {
      await fetch(`${apiBase}/warehouse/transfers/${transferId}/status`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: "dispatched" }),
      });
      await load();
    } catch (_) {
    } finally {
      setSavingTransferId(null);
    }
  };

  const batchDispatch = async () => {
    const toDispatch = packed.filter((o) => o.status !== "dispatched");
    for (const tx of toDispatch) {
      // Keep requests sequential for predictable status updates.
      // eslint-disable-next-line no-await-in-loop
      await dispatchTransfer(tx.id);
    }
  };

  return (
    <div>
      <PageHeader title="Dispatch" actions={<Btn variant="primary" size="sm" onClick={batchDispatch}><Truck size={14} />Batch Send</Btn>} />
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {packed.map((o) => (
          <div key={o.id} style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 4 }}>
                <span style={{ fontFamily: "monospace", fontSize: 12, fontWeight: 600 }}>TRF-{String(o.id).padStart(5, "0")}</span>
                <StatusPill status={o.status} />
              </div>
              <div style={{ fontSize: 12, color: T.gray500 }}>{o.medicine_name} · Qty {o.quantity} · {o.pharmacy_store_name || "-"}</div>
              {o.tracking && <div style={{ fontSize: 11, fontFamily: "monospace", color: T.blue, marginTop: 4 }}>{o.tracking}</div>}
            </div>
            {o.status !== "dispatched" ? <Btn variant="success" size="sm" disabled={savingTransferId === o.id} onClick={() => dispatchTransfer(o.id)}><Truck size={12} />Send to Pharmacy</Btn> : <span style={{ fontSize: 12, color: T.green, fontWeight: 600 }}>Dispatched</span>}
          </div>
        ))}
        {packed.length === 0 && <div style={{ textAlign: "center", padding: 60, color: T.gray400 }}><Package size={48} strokeWidth={1} /><div style={{ marginTop: 16, fontWeight: 600 }}>No packed orders</div></div>}
      </div>
    </div>
  );
}