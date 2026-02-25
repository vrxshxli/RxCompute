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
      })),
    [orders, userMap],
  );
  const urgent = mapped.filter((o) => o.status === "pending" && o.items.some((it) => !!it.rx_required));
  const normal = mapped.filter((o) => o.status === "pending" && o.items.every((it) => !it.rx_required));
  const scheduled = mapped.filter((o) => ["confirmed", "verified", "picking", "packed", "dispatched"].includes(o.status)).slice(0, 5);

  const setStatus = async (orderId, status) => {
    if (!token) return;
    setSavingId(orderId);
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
      setSavingId(null);
    }
  };
  const Col=({title,color,children,count})=><div style={{flex:1,minWidth:280}}><div style={{background:color,height:3,borderRadius:"10px 10px 0 0"}}/><div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:"0 0 10px 10px",padding:16}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:16}}><span style={{fontWeight:600,fontSize:14,color:T.gray900}}>{title}</span><span style={{background:color+"15",color,padding:"2px 8px",borderRadius:4,fontSize:11,fontWeight:700}}>{count}</span></div><div style={{display:"flex",flexDirection:"column",gap:12}}>{children}</div></div></div>;
  const OC=({order,type})=><div style={{border:"1px solid "+T.gray200,borderLeft:"3px solid "+(type==="urgent"?T.red:type==="normal"?T.blue:T.gray400),borderRadius:8,padding:14}}>
    <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}><span style={{fontFamily:"monospace",fontSize:11,color:T.gray500}}>{order.order_id}</span></div>
    <div style={{fontSize:13,color:T.gray700,marginBottom:4}}>{order.patient_name}</div>
    <div style={{fontSize:12,color:T.gray500,marginBottom:8}}>{order.items?.map(x=>x.name.split(" ").slice(0,3).join(" ")+" x"+x.quantity).join(", ")}</div>
    <div style={{fontSize:14,fontWeight:700,color:T.blue,marginBottom:8}}>₹{order.total_price.toFixed(2)}</div>
    {type==="urgent"&&<div style={{fontSize:11,color:T.red,fontWeight:500,marginBottom:8}}>Prescription Required</div>}
    {type==="normal"&&<div style={{display:"flex",alignItems:"center",gap:6,marginBottom:8}}><span style={{fontSize:11,color:T.gray500}}>AI:</span><div style={{width:60,height:4,borderRadius:2,background:T.gray100,overflow:"hidden"}}><div style={{height:"100%",width:"96%",borderRadius:2,background:T.green}}/></div><span style={{fontSize:11,fontWeight:600,color:T.green}}>96%</span></div>}
    <div style={{display:"flex",gap:8}}>
      {type==="urgent"&&<><Btn variant="primary" size="sm" disabled={savingId===order.id} onClick={()=>setStatus(order.id,"verified")}>Approve Rx</Btn><Btn variant="secondary" size="sm" style={{color:T.red}} disabled={savingId===order.id} onClick={()=>setStatus(order.id,"cancelled")}>Reject</Btn></>}
      {type==="normal"&&<><Btn variant="success" size="sm" disabled={savingId===order.id} onClick={()=>setStatus(order.id,"confirmed")}><CheckCircle size={12}/>Approve</Btn><Btn variant="secondary" size="sm" disabled={savingId===order.id} onClick={()=>setStatus(order.id,"picking")}>Process</Btn></>}
      {type==="scheduled"&&<Btn variant="secondary" size="sm" disabled={savingId===order.id} onClick={()=>setStatus(order.id,"dispatched")}>Mark Dispatch</Btn>}
    </div>
  </div>;
  return (<div><PageHeader title="Order Queue" badge={String(mapped.length)} actions={<Btn variant="success" size="sm" onClick={load}><CheckCircle size={14}/>Refresh</Btn>}/>
  <div style={{display:"flex",gap:16,overflowX:"auto"}}><Col title="Urgent (Rx)" color={T.red} count={urgent.length}>{urgent.slice(0,8).map(o=><OC key={o.order_id} order={o} type="urgent"/>)}</Col><Col title="Normal" color={T.blue} count={normal.length}>{normal.slice(0,8).map(o=><OC key={o.order_id} order={o} type="normal"/>)}</Col><Col title="Scheduled" color={T.gray400} count={scheduled.length}>{scheduled.map(a=><OC key={a.order_id} order={a} type="scheduled"/>)}</Col></div></div>);
}