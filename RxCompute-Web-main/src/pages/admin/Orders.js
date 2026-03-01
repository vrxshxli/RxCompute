import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { StatusPill, SearchInput, Btn, PageHeader } from '../../components/shared';
import { useAuth } from '../../context/AuthContext';

export default function AdminOrders() {
  const { token, apiBase, user } = useAuth();
  const [search, setSearch] = useState("");
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]);
  const [savingId, setSavingId] = useState(null);
  const [error, setError] = useState("");

  const load = async () => {
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const [ordersRes, usersRes] = await Promise.all([
        fetch(`${apiBase}/orders/`, { headers }),
        fetch(`${apiBase}/users/`, { headers }),
      ]);
      if (ordersRes.ok) {
        const data = await ordersRes.json();
        setOrders(Array.isArray(data) ? data : []);
      }
      if (usersRes.ok) {
        const data = await usersRes.json();
        setUsers(Array.isArray(data) ? data : []);
      }
    } catch (_) {}
  };

  useEffect(() => {
    load();
  }, [token, apiBase]);

  const userMap = useMemo(
    () =>
      users.reduce((acc, u) => {
        acc[u.id] = (u.name || "").trim() || `User #${u.id}`;
        return acc;
      }, {}),
    [users],
  );
  const viewRows = useMemo(
    () =>
      orders.map((o) => ({
        id: o.id,
        order_id: o.order_uid,
        patient_name: userMap[o.user_id] || `User #${o.user_id}`,
        status: o.status,
        total_price: o.total || 0,
        pharmacy_node: o.pharmacy || "-",
        pharmacy_approved_by_name: o.pharmacy_approved_by_name || null,
        pharmacy_approved_at: o.pharmacy_approved_at || null,
        last_status_updated_by_role: o.last_status_updated_by_role || null,
        last_status_updated_by_name: o.last_status_updated_by_name || null,
        last_status_updated_at: o.last_status_updated_at || null,
        cancel_reason: o.cancel_reason || null,
        items: o.items || [],
      })),
    [orders, userMap],
  );
  const filtered = search
    ? viewRows.filter(
        (o) =>
          o.order_id.toLowerCase().includes(search.toLowerCase()) ||
          o.patient_name.toLowerCase().includes(search.toLowerCase()),
      )
    : viewRows;
  const groups = {};
  filtered.forEach(o => { if(!groups[o.status]) groups[o.status]=[]; groups[o.status].push(o); });
  const statusOrder = ["pending","confirmed","verified","picking","packed","dispatched","delivered","cancelled"];
  const statusColor = {pending:T.yellow,confirmed:T.blue,verified:T.green,picking:T.yellow,packed:T.blue,dispatched:T.green,delivered:T.green,cancelled:T.red};
  const getStatusOptions = (order) => {
    const current = order?.status;
    const isRefill = String(order?.order_id || "").toUpperCase().startsWith("RFL-");
    if (user?.role !== "admin") return [current];
    if (current === "pending") {
      if (isRefill) {
        // Refill orders can move directly through logistics from pending.
        return ["pending", "verified", "picking", "packed", "dispatched", "delivered", "cancelled"];
      }
      return ["pending"];
    }
    if (current === "verified") return ["verified", "picking", "cancelled"];
    if (current === "picking") return ["picking", "packed", "cancelled"];
    if (current === "packed") return ["packed", "dispatched", "cancelled"];
    if (current === "dispatched") return ["dispatched", "delivered", "cancelled"];
    return [current];
  };

  const updateStatus = async (orderId, status) => {
    if (!token) return;
    setSavingId(orderId);
    setError("");
    try {
      const res = await fetch(`${apiBase}/orders/${orderId}/status`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.detail || "Failed to update status");
      } else {
        await load();
      }
    } catch (_) {
      setError("Network error while updating status");
    } finally {
      setSavingId(null);
    }
  };

  return (<div>
    <PageHeader title="All Orders" badge={String(viewRows.length)}/>
    <div style={{marginBottom:16}}><SearchInput value={search} onChange={setSearch} placeholder="Search orders..."/></div>
    {error ? <div style={{marginBottom:10, color:T.red, fontSize:12}}>{error}</div> : null}
    <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
      {statusOrder.filter(s=>groups[s]).map(status => (
        <div key={status}>
          <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:12, padding:"8px 12px", background:T.white, borderRadius:8, border:"1px solid "+T.gray200 }}>
            <span style={{ width:10, height:10, borderRadius:"50%", background:statusColor[status]||T.gray400 }} />
            <span style={{ fontSize:13, fontWeight:600, color:T.gray900, textTransform:"capitalize" }}>{status.replace(/_/g," ")}</span>
            <span style={{ fontSize:11, color:T.gray400, marginLeft:"auto" }}>{groups[status].length}</span>
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(280px, 1fr))", gap:10 }}>
            {groups[status].map(o => (
              <div key={o.order_id} style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:8, padding:14, transition:"box-shadow .2s" }}
                onMouseEnter={e=>e.currentTarget.style.boxShadow="0 2px 12px rgba(0,0,0,.06)"}
                onMouseLeave={e=>e.currentTarget.style.boxShadow="none"}>
                <div style={{ fontFamily:"monospace", fontSize:11, color:T.gray400, marginBottom:4 }}>{o.order_id}</div>
                <div style={{ fontSize:13, fontWeight:600, color:T.gray900, marginBottom:4 }}>{o.patient_name}</div>
                <div style={{ fontSize:12, color:T.gray500, marginBottom:6 }}>{o.items.length} items · {o.pharmacy_node}</div>
                <div style={{ fontSize:15, fontWeight:700, color:T.blue, marginBottom:8 }}>₹{o.total_price.toFixed(2)}</div>
                {(o.pharmacy_approved_by_name || o.last_status_updated_by_name) ? (
                  <div style={{ fontSize:11, color:T.gray500, marginBottom:8 }}>
                    {o.pharmacy_approved_by_name ? `Pharmacy approved by ${o.pharmacy_approved_by_name}` : `${o.last_status_updated_by_role || "staff"}: ${o.last_status_updated_by_name || "-"}`}{" · "}
                    {new Date(o.pharmacy_approved_at || o.last_status_updated_at || Date.now()).toLocaleString()}
                  </div>
                ) : null}
                {o.status === "cancelled" && o.cancel_reason ? (
                  <div style={{ fontSize:11, color:T.red, marginBottom:8 }}>
                    Reason: {o.cancel_reason}
                  </div>
                ) : null}
                <div style={{ display:"flex", gap:8, alignItems:"center" }}>
                  <StatusPill status={o.status} size="xs" />
                  <select
                    value={o.status}
                    onChange={(e) => updateStatus(o.id, e.target.value)}
                    disabled={savingId === o.id || getStatusOptions(o).length === 1}
                    style={{ fontSize:11, padding:"4px 6px", border:`1px solid ${T.gray200}`, borderRadius:6 }}
                  >
                    {getStatusOptions(o).map((s) => (
                      <option key={s} value={s}>{s.replace(/_/g," ")}</option>
                    ))}
                  </select>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>);
}