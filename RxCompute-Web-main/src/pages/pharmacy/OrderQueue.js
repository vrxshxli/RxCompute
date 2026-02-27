import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { Btn, PageHeader } from '../../components/shared';
import { CheckCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
export default function PharmacyOrderQueue() {
  const { token, apiBase } = useAuth();
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]);
  const [savingId, setSavingId] = useState(null);
  const [queueFilter, setQueueFilter] = useState("all");
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

  const mapped = useMemo(
    () =>
      orders.map((o) => ({
        id: o.id,
        order_id: o.order_uid,
        patient_name: userMap[o.user_id] || `User #${o.user_id}`,
        status: o.status,
        items: o.items || [],
        total_price: o.total || 0,
        pharmacy_approved_by_name: o.pharmacy_approved_by_name || null,
        pharmacy_approved_at: o.pharmacy_approved_at || null,
        last_status_updated_by_role: o.last_status_updated_by_role || null,
        last_status_updated_by_name: o.last_status_updated_by_name || null,
        last_status_updated_at: o.last_status_updated_at || null,
      })),
    [orders, userMap],
  );
  const urgent = mapped.filter((o) => o.status === "pending" && o.items.some((it) => !!it.rx_required));
  const normal = mapped.filter((o) => o.status === "pending" && o.items.every((it) => !it.rx_required));
  const scheduled = mapped.filter((o) => ["verified", "picking", "packed", "dispatched"].includes(o.status));
  const queueCards = [
    ...urgent.map((o) => ({ ...o, queue_type: "urgent" })),
    ...normal.map((o) => ({ ...o, queue_type: "normal" })),
    ...scheduled.map((o) => ({ ...o, queue_type: "scheduled" })),
  ];
  const visibleCards = queueFilter === "all" ? queueCards : queueCards.filter((x) => x.queue_type === queueFilter);

  const setStatus = async (orderId, status) => {
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
        setError(data?.detail?.message || data?.detail || "Failed to update status");
      } else {
        await load();
      }
    } catch (_) {
      setError("Network error while updating status");
    } finally {
      setSavingId(null);
    }
  };
  const OC=({order,type})=><div style={{border:"1px solid "+T.gray200,borderLeft:"3px solid "+(type==="urgent"?T.red:type==="normal"?T.blue:T.gray400),borderRadius:8,padding:14}}>
    <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}><span style={{fontFamily:"monospace",fontSize:11,color:T.gray500}}>{order.order_id}</span></div>
    <div style={{fontSize:13,color:T.gray700,marginBottom:4}}>{order.patient_name}</div>
    <div style={{fontSize:12,color:T.gray500,marginBottom:8}}>{order.items?.map(x=>x.name.split(" ").slice(0,3).join(" ")+" x"+x.quantity).join(", ")}</div>
    <div style={{fontSize:14,fontWeight:700,color:T.blue,marginBottom:8}}>₹{order.total_price.toFixed(2)}</div>
    {type==="urgent"&&<div style={{fontSize:11,color:T.red,fontWeight:500,marginBottom:8}}>Prescription Required</div>}
    {type==="normal"&&<div style={{display:"flex",alignItems:"center",gap:6,marginBottom:8}}><span style={{fontSize:11,color:T.gray500}}>AI:</span><div style={{width:60,height:4,borderRadius:2,background:T.gray100,overflow:"hidden"}}><div style={{height:"100%",width:"96%",borderRadius:2,background:T.green}}/></div><span style={{fontSize:11,fontWeight:600,color:T.green}}>96%</span></div>}
    {(order.pharmacy_approved_by_name || order.last_status_updated_by_name) ? (
      <div style={{fontSize:11,color:T.gray500,marginBottom:8}}>
        {order.pharmacy_approved_by_name ? `Pharmacy: ${order.pharmacy_approved_by_name}` : `Updated by: ${order.last_status_updated_by_name || "-"}`}{" · "}
        {new Date(order.pharmacy_approved_at || order.last_status_updated_at || Date.now()).toLocaleString()}
      </div>
    ) : null}
    <div style={{display:"flex",gap:8}}>
      {type==="urgent"&&<><Btn variant="primary" size="sm" disabled={savingId===order.id} onClick={()=>setStatus(order.id,"verified")}>Approve Rx</Btn><Btn variant="secondary" size="sm" style={{color:T.red}} disabled={savingId===order.id} onClick={()=>setStatus(order.id,"cancelled")}>Reject</Btn></>}
      {type==="normal"&&<><Btn variant="success" size="sm" disabled={savingId===order.id} onClick={()=>setStatus(order.id,"verified")}><CheckCircle size={12}/>Approve</Btn><Btn variant="secondary" size="sm" disabled={savingId===order.id} onClick={()=>setStatus(order.id,"cancelled")}>Reject</Btn></>}
      {type==="scheduled"&&<span style={{fontSize:11,color:T.gray500}}>Status is handled by admin logistics</span>}
    </div>
  </div>;
  return (<div><PageHeader title="Order Queue" badge={String(mapped.length)} actions={<Btn variant="success" size="sm" onClick={load}><CheckCircle size={14}/>Refresh</Btn>}/>
  {error ? <div style={{ marginBottom:10, color:T.red, fontSize:12 }}>{error}</div> : null}
  <div style={{display:"flex",gap:10,marginBottom:12,alignItems:"center"}}>
    <span style={{fontSize:12,color:T.gray500}}>Filter:</span>
    <select value={queueFilter} onChange={(e)=>setQueueFilter(e.target.value)} style={{padding:"8px 10px",border:`1px solid ${T.gray200}`,borderRadius:8,fontSize:12}}>
      <option value="all">All ({queueCards.length})</option>
      <option value="urgent">Urgent Rx ({urgent.length})</option>
      <option value="normal">Normal ({normal.length})</option>
      <option value="scheduled">Scheduled ({scheduled.length})</option>
    </select>
  </div>
  <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))",gap:12}}>
    {visibleCards.map((o)=><OC key={`${o.queue_type}-${o.order_id}`} order={o} type={o.queue_type}/>)}
  </div></div>);
}