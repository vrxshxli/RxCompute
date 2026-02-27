import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { Btn, PageHeader } from '../../components/shared';
import { Play, PlusCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function WarehouseFulfillment() {
  const { token, apiBase } = useAuth();
  const [stock, setStock] = useState([]);
  const [inboundTransfers, setInboundTransfers] = useState([]);
  const [outboundTransfers, setOutboundTransfers] = useState([]);
  const [pharmacies, setPharmacies] = useState([]);
  const [savingTransferId, setSavingTransferId] = useState(null);
  const [showSendPharmacy, setShowSendPharmacy] = useState(false);
  const [sendMsg, setSendMsg] = useState("");
  const [sendForm, setSendForm] = useState({
    medicine_id: "",
    quantity: "10",
    pharmacy_store_id: "",
    note: "",
  });

  const load = async () => {
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const [stockRes, inboundRes, outboundRes, storesRes] = await Promise.all([
        fetch(`${apiBase}/warehouse/stock`, { headers }),
        fetch(`${apiBase}/warehouse/transfers?direction=admin_to_warehouse`, { headers }),
        fetch(`${apiBase}/warehouse/transfers?direction=warehouse_to_pharmacy`, { headers }),
        fetch(`${apiBase}/pharmacy-stores/`, { headers }),
      ]);
      if (stockRes.ok) {
        const data = await stockRes.json();
        setStock(Array.isArray(data) ? data : []);
      }
      if (inboundRes.ok) {
        const data = await inboundRes.json();
        setInboundTransfers(Array.isArray(data) ? data : []);
      }
      if (outboundRes.ok) {
        const data = await outboundRes.json();
        setOutboundTransfers(Array.isArray(data) ? data : []);
      }
      if (storesRes.ok) {
        const data = await storesRes.json();
        setPharmacies(Array.isArray(data) ? data : []);
      }
    } catch (_) {}
  };

  useEffect(() => {
    load();
  }, [token, apiBase]);

  const updateTransferStatus = async (transferId, status) => {
    if (!token) return;
    setSavingTransferId(transferId);
    try {
      await fetch(`${apiBase}/warehouse/transfers/${transferId}/status`, {
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
      setSavingTransferId(null);
    }
  };

  const sendToPharmacy = async () => {
    if (!token || !sendForm.medicine_id || !sendForm.pharmacy_store_id || Number(sendForm.quantity) <= 0) {
      setSendMsg("Choose medicine, pharmacy and valid quantity");
      return;
    }
    setSendMsg("");
    try {
      const res = await fetch(`${apiBase}/warehouse/transfers/warehouse-to-pharmacy`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          medicine_id: Number(sendForm.medicine_id),
          quantity: Number(sendForm.quantity),
          pharmacy_store_id: Number(sendForm.pharmacy_store_id),
          note: sendForm.note.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setSendMsg(data?.detail || "Unable to create pharmacy transfer");
        return;
      }
      setSendMsg("Transfer created");
      setSendForm({ medicine_id: "", quantity: "10", pharmacy_store_id: "", note: "" });
      await load();
    } catch (_) {
      setSendMsg("Network error while creating transfer");
    }
  };

  const queuedOutbound = useMemo(
    () => outboundTransfers.filter((x) => ["requested", "picking", "packed"].includes(x.status)),
    [outboundTransfers],
  );
  const sc = { requested: T.blue, picking: T.yellow, packed: T.green, dispatched: T.gray400, received: T.green };

  return (
    <div>
      <PageHeader
        title="Warehouse Fulfillment"
        badge={`Stock SKUs: ${stock.length}`}
        actions={<Btn variant="secondary" size="sm" onClick={() => setShowSendPharmacy((v) => !v)}><PlusCircle size={12} />{showSendPharmacy ? "Close" : "Send Medicine to Pharmacy"}</Btn>}
      />
      {showSendPharmacy ? (
        <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14, marginBottom: 12 }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 2fr 2fr", gap: 8 }}>
            <select value={sendForm.medicine_id} onChange={(e) => setSendForm({ ...sendForm, medicine_id: e.target.value })} style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }}>
              <option value="">Select medicine</option>
              {stock.map((m) => <option key={m.medicine_id} value={m.medicine_id}>{m.medicine_name} (warehouse stock: {m.quantity || 0})</option>)}
            </select>
            <input value={sendForm.quantity} onChange={(e) => setSendForm({ ...sendForm, quantity: e.target.value })} placeholder="Units" type="number" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
            <select value={sendForm.pharmacy_store_id} onChange={(e) => setSendForm({ ...sendForm, pharmacy_store_id: e.target.value })} style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }}>
              <option value="">Select pharmacy</option>
              {pharmacies.map((p) => <option key={p.id} value={p.id}>{p.node_id} - {p.name}</option>)}
            </select>
            <div style={{ display: "flex", gap: 8 }}>
              <input value={sendForm.note} onChange={(e) => setSendForm({ ...sendForm, note: e.target.value })} placeholder="Note (optional)" style={{ flex: 1, padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
              <Btn variant="primary" size="sm" onClick={sendToPharmacy}>Create</Btn>
            </div>
          </div>
          {sendMsg ? <div style={{ marginTop: 8, fontSize: 12, color: sendMsg === "Transfer created" ? T.green : T.red }}>{sendMsg}</div> : null}
        </div>
      ) : null}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {queuedOutbound.map((t) => (
          <div key={t.id} style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 16, borderLeft: `4px solid ${sc[t.status] || T.gray400}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ fontFamily: "monospace", fontSize: 12, fontWeight: 600 }}>TRF-{String(t.id).padStart(5, "0")}</span>
                <span style={{ background: `${sc[t.status] || T.gray400}15`, color: sc[t.status], padding: "3px 10px", borderRadius: 6, fontSize: 10, fontWeight: 700, textTransform: "uppercase" }}>{t.status}</span>
              </div>
              <span style={{ fontSize: 12, color: T.gray400 }}>to {t.pharmacy_store_name || "-"}</span>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
              <div style={{ padding: "8px 14px", background: T.gray50, borderRadius: 8, fontSize: 12, display: "flex", gap: 8, alignItems: "center" }}>
                <span style={{ fontWeight: 500, color: T.gray800 }}>{t.medicine_name}</span>
                <span style={{ color: T.blue, fontWeight: 700 }}>x{t.quantity}</span>
              </div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              {t.status === "requested" && <Btn variant="primary" size="sm" disabled={savingTransferId === t.id} onClick={() => updateTransferStatus(t.id, "picking")}><Play size={12} />Start Pick</Btn>}
              {t.status === "picking" && <span style={{ fontSize: 12, color: T.yellow, fontWeight: 600 }}>In Picking</span>}
              {t.status === "packed" && <span style={{ fontSize: 12, color: T.green, fontWeight: 600 }}>Ready for Dispatch</span>}
            </div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 20, background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: T.gray900, marginBottom: 8 }}>Inbound from Admin</div>
        {inboundTransfers.slice(0, 8).map((x) => <div key={x.id} style={{ fontSize: 12, color: T.gray700, padding: "6px 0", borderBottom: `1px solid ${T.gray100}` }}>{x.medicine_name} · +{x.quantity} · {new Date(x.created_at).toLocaleString()}</div>)}
      </div>
    </div>
  );
}