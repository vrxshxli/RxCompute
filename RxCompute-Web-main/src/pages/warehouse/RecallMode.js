import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { StatusPill, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { AlertTriangle, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function WarehouseRecall() {
  const { token, apiBase } = useAuth();
  const [query,setQuery]=useState("");
  const [active,setActive]=useState(false);
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]);

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

  const userMap = useMemo(() => users.reduce((acc, u) => {
    acc[u.id] = u;
    return acc;
  }, {}), [users]);

  const results = query ? orders.filter((o) => (o.items || []).some((x) => (x.name || "").toLowerCase().includes(query.toLowerCase()))).slice(0, 10) : [];
  return (<div><PageHeader title="Recall Mode"/>
  <div style={{display:"flex",alignItems:"center",gap:16,marginBottom:24}}><div style={{display:"flex",alignItems:"center",gap:10}}><span style={{fontSize:14,fontWeight:600,color:active?T.red:T.gray600}}>RECALL MODE</span><Toggle on={active} onChange={()=>setActive(!active)}/></div>{active&&<div style={{fontSize:11,color:T.red,fontWeight:600,display:"flex",alignItems:"center",gap:4}}><AlertCircle size={14}/>ACTIVE</div>}</div>
  {!active?<div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:40,textAlign:"center"}}><AlertTriangle size={48} color={T.gray300} strokeWidth={1}/><div style={{fontSize:16,fontWeight:600,color:T.gray700,marginTop:16}}>Recall Mode Off</div><div style={{fontSize:13,color:T.gray500,marginTop:8}}>Toggle to trace products across all orders.</div></div>:(
    <div><div style={{marginBottom:16}}><SearchInput value={query} onChange={setQuery} placeholder="Product name or batch..."/></div>
    {query && <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(260px,1fr))",gap:12}}>
      {results.map(o=>(
        <div key={o.id} style={{background:T.white,border:"1px solid "+T.red+"30",borderRadius:10,padding:16,borderLeft:"4px solid "+T.red}}>
          <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}><span style={{fontFamily:"monospace",fontSize:12,fontWeight:600}}>{o.order_uid}</span><StatusPill status={o.status} size="xs"/></div>
          <div style={{fontSize:13,color:T.gray700,marginBottom:4}}>{userMap[o.user_id]?.name || `User #${o.user_id}`} · {o.pharmacy || "-"}</div>
          <div style={{fontSize:11,color:T.gray400}}>{new Date(o.created_at).toLocaleDateString()}</div>
        </div>
      ))}
    </div>}
    {query && results.length>0 && <div style={{marginTop:16}}><Btn variant="danger" size="md"><AlertCircle size={14}/>Notify All Affected</Btn></div>}
    </div>
  )}</div>);
}