import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { Btn, PageHeader } from '../../components/shared';
import { Zap, CheckCircle, AlertTriangle, XCircle, ExternalLink } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
export default function PharmacyVerify() {
  const { token, apiBase } = useAuth();
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]);
  const [activeOrderId, setActiveOrderId] = useState(null);

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
        const list = Array.isArray(data) ? data : [];
        setOrders(list);
        if (!activeOrderId && list.length) setActiveOrderId(list[0].id);
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
        acc[u.id] = u;
        return acc;
      }, {}),
    [users],
  );
  const o = orders.find((x) => x.id === activeOrderId) || orders[0];
  const p = o ? userMap[o.user_id] : null;

  const setStatus = async (status) => {
    if (!token || !o) return;
    await fetch(`${apiBase}/orders/${o.id}/status`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status }),
    });
    await load();
  };

  if (!o) return <div><PageHeader title="Order Verification" subtitle="No orders"/></div>;
  return (<div><PageHeader title="Order Verification" subtitle={o.order_uid}/>
  <div style={{display:"flex",gap:8,marginBottom:12,overflowX:"auto"}}>
    {orders.slice(0,20).map((x) => (
      <button key={x.id} onClick={() => setActiveOrderId(x.id)} style={{border:`1px solid ${activeOrderId===x.id?T.blue:T.gray200}`,background:activeOrderId===x.id?T.blue+"10":T.white,borderRadius:8,padding:"6px 10px",fontSize:11,cursor:"pointer",fontFamily:"monospace"}}>{x.order_uid}</button>
    ))}
  </div>
  <div style={{display:"grid",gridTemplateColumns:"1.4fr 1fr",gap:16}}>
    <div>
      <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:10,padding:20,marginBottom:16}}><div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:12}}>Patient</div><div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>{[["ID",`U-${o.user_id}`],["Name",p?.name || `User #${o.user_id}`],["Email",p?.email || "-"],["Role",p?.role || "user"]].map(([l,v])=><div key={l}><div style={{fontSize:11,color:T.gray400,textTransform:"uppercase"}}>{l}</div><div style={{fontSize:13,color:T.gray800,fontWeight:500}}>{v}</div></div>)}</div></div>
      <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:10,padding:20}}><div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:12}}>Items</div>{(o.items || []).map((it,i)=><div key={i} style={{display:"flex",justifyContent:"space-between",padding:"10px 0",borderBottom:i<(o.items || []).length-1?"1px solid "+T.gray100:"none"}}><div><div style={{fontWeight:500,color:T.gray800}}>{it.name}</div><div style={{fontSize:11,color:T.gray400}}>Qty: {it.quantity} · ₹ {Number(it.price || 0).toFixed(2)} {it.rx_required ? "· Rx" : ""}</div></div></div>)}<div style={{display:"flex",justifyContent:"flex-end",paddingTop:12,fontSize:15,fontWeight:700}}>₹ {Number(o.total || 0).toFixed(2)}</div></div>
    </div>
    <div>
      <div style={{background:T.navy900,borderRadius:10,padding:20,color:T.gray300,marginBottom:16}}><div style={{fontWeight:600,fontSize:14,color:T.white,marginBottom:16,display:"flex",alignItems:"center",gap:8}}><Zap size={16} color={T.yellow}/>AI Analysis</div>{[{i:"OK",t:`Prescription: ${((o.items || []).some(it=>it.rx_required)) ? "required" : "not required"}`,c:T.green},{i:"OK",t:`Items: ${(o.items || []).length}`,c:T.green},{i:"OK",t:`Current status: ${o.status}`,c:T.green},{i:">>",t:"Recommendation: APPROVE",c:T.blue}].map((x,j)=><div key={j} style={{display:"flex",gap:10,marginBottom:12,fontSize:13}}><span style={{color:x.c,fontWeight:700}}>{x.i}</span><span style={{color:x.c}}>{x.t}</span></div>)}<Btn variant="ghost" size="sm" style={{color:T.blue,marginTop:8}}><ExternalLink size={12}/>Langfuse</Btn></div>
      <div style={{display:"flex",flexDirection:"column",gap:8}}><Btn variant="success" size="md" style={{width:"100%",justifyContent:"center"}} onClick={() => setStatus((o.items || []).some(it=>it.rx_required) ? "verified" : "confirmed")}><CheckCircle size={16}/>Approve</Btn><Btn variant="secondary" size="md" style={{width:"100%",justifyContent:"center",color:T.yellow}} onClick={() => setStatus("picking")}><AlertTriangle size={16}/>Move to Picking</Btn><Btn variant="secondary" size="md" style={{width:"100%",justifyContent:"center",color:T.red}} onClick={() => setStatus("cancelled")}><XCircle size={16}/>Reject</Btn></div>
    </div>
  </div></div>);
}