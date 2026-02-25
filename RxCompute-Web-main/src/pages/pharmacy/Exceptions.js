import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { StatusPill, Btn, PageHeader } from '../../components/shared';
import { useAuth } from '../../context/AuthContext';
export default function PharmacyExceptions() {
  const { token, apiBase } = useAuth();
  const [orders, setOrders] = useState([]);
  useEffect(() => {
    if (!token) return;
    const load = async () => {
      try {
        const res = await fetch(`${apiBase}/orders/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data = await res.json();
        setOrders(Array.isArray(data) ? data : []);
      } catch (_) {}
    };
    load();
  }, [token, apiBase]);
  const exceptions = useMemo(
    () =>
      orders
        .filter((o) => o.status === "pending")
        .flatMap((o) =>
          (o.items || [])
            .filter((it) => !!it.rx_required || (it.quantity || 0) > 5)
            .map((it) => ({
              t: it.rx_required ? "Prescription Required" : "High Quantity",
              o: o.order_uid,
              m: `${it.name} x${it.quantity}`,
              p: `User #${o.user_id}`,
              s: it.rx_required ? "high" : "medium",
            })),
        )
        .slice(0, 20),
    [orders],
  );
  return (<div><PageHeader title="Exceptions" subtitle="Manual review"/>
  <div style={{display:"flex",flexDirection:"column",gap:12}}>
    {exceptions.map((x,i)=>
      <div key={i} style={{background:T.white,border:"1px solid "+T.gray200,borderLeft:"4px solid "+(x.s==="high"?T.red:T.yellow),borderRadius:10,padding:16}}>
        <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}><span style={{fontWeight:600,color:T.gray900}}>{x.t}</span><StatusPill status={x.s} size="xs"/></div>
        <div style={{fontSize:13,color:T.gray600,marginBottom:4}}>Order: <span style={{fontFamily:"monospace"}}>{x.o}</span></div>
        <div style={{fontSize:13,color:T.gray600,marginBottom:4}}>{x.m} · {x.p}</div>
        <div style={{display:"flex",gap:8,marginTop:8}}><Btn variant="primary" size="sm">Resolve</Btn><Btn variant="secondary" size="sm">Escalate</Btn></div>
      </div>
    )}
  </div></div>);
}