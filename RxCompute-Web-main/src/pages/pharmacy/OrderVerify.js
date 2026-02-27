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
  const [safetySummary, setSafetySummary] = useState('');
  const [safetyBlocked, setSafetyBlocked] = useState(false);
  const [safetyReady, setSafetyReady] = useState(false);
  const [safetyResults, setSafetyResults] = useState([]);
  const [checkingSafety, setCheckingSafety] = useState(false);

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

  const runSafetyCheck = async (order) => {
    if (!token || !order) return;
    setCheckingSafety(true);
    setSafetyReady(false);
    try {
      const payload = {
        items: (order.items || []).map((it) => ({
          medicine_id: it.medicine_id,
          name: it.name,
          quantity: it.quantity,
          dosage_instruction: it.dosage_instruction || '',
          strips_count: it.strips_count || 1,
          prescription_file: it.prescription_file || null,
        })),
        message: `Pharmacy verify order ${order.order_uid}`,
      };
      const res = await fetch(`${apiBase}/safety/check`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setSafetySummary((data?.safety_summary || '').toString());
      setSafetyBlocked(Boolean(data?.blocked));
      setSafetyResults(Array.isArray(data?.safety_results) ? data.safety_results : []);
      setSafetyReady(true);
    } catch (_) {
      setSafetySummary('Safety check failed');
      setSafetyBlocked(true);
      setSafetyResults([]);
      setSafetyReady(true);
    } finally {
      setCheckingSafety(false);
    }
  };

  useEffect(() => {
    if (o) runSafetyCheck(o);
  }, [activeOrderId, token, apiBase, orders.length]);

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
  const resolveFileUrl = (path) => {
    if (!path) return "";
    if (/^https?:\/\//i.test(path)) return path;
    return `${apiBase}${path}`;
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
      <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:10,padding:20}}><div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:12}}>Items</div>{(o.items || []).map((it,i)=><div key={i} style={{display:"flex",justifyContent:"space-between",padding:"10px 0",borderBottom:i<(o.items || []).length-1?"1px solid "+T.gray100:"none"}}><div><div style={{fontWeight:500,color:T.gray800}}>{it.name}</div><div style={{fontSize:11,color:T.gray400}}>Qty: {it.quantity} · Strips: {it.strips_count || 1} · ₹ {Number(it.price || 0).toFixed(2)} {it.rx_required ? "· Rx" : ""}</div><div style={{fontSize:11,color:T.gray500,marginTop:4}}>Dosage: {it.dosage_instruction || "-"}</div>{it.prescription_file ? <div style={{marginTop:6}}><a href={resolveFileUrl(it.prescription_file)} target="_blank" rel="noreferrer" style={{fontSize:12,color:T.blue}}>View Prescription</a></div> : <div style={{marginTop:6,fontSize:11,color:T.red}}>Prescription missing</div>}</div>{it.prescription_file && /\.(png|jpe?g|webp)$/i.test(it.prescription_file) ? <img src={resolveFileUrl(it.prescription_file)} alt="Prescription" style={{width:80,height:80,objectFit:"cover",borderRadius:8,border:`1px solid ${T.gray200}`}} /> : null}</div>)}<div style={{display:"flex",justifyContent:"flex-end",paddingTop:12,fontSize:15,fontWeight:700}}>₹ {Number(o.total || 0).toFixed(2)}</div></div>
    </div>
    <div>
      <div style={{background:T.navy900,borderRadius:10,padding:20,color:T.gray300,marginBottom:16}}><div style={{fontWeight:600,fontSize:14,color:T.white,marginBottom:16,display:"flex",alignItems:"center",gap:8}}><Zap size={16} color={T.yellow}/>AI Analysis</div>{[{i:!safetyReady||checkingSafety?"..":(safetyBlocked?"NO":"OK"),t:`Prescription: ${((o.items || []).some(it=>it.rx_required)) ? "required" : "not required"}`,c:!safetyReady||checkingSafety?T.yellow:(safetyBlocked?T.red:T.green)},{i:"OK",t:`Items: ${(o.items || []).length}`,c:T.green},{i:"OK",t:`Current status: ${o.status}`,c:T.green},{i:checkingSafety?"..":(safetyBlocked?"XX":">>"),t:checkingSafety?"Recommendation: CHECKING":"Recommendation: " + (safetyBlocked ? "REJECT" : "APPROVE"),c:safetyBlocked?T.red:T.blue}].map((x,j)=><div key={j} style={{display:"flex",gap:10,marginBottom:12,fontSize:13}}><span style={{color:x.c,fontWeight:700}}>{x.i}</span><span style={{color:x.c}}>{x.t}</span></div>)}{safetySummary ? <div style={{fontSize:11,color:safetyBlocked?T.red:T.gray300,marginTop:6,whiteSpace:"pre-wrap"}}>{safetySummary}</div> : null}{Array.isArray(safetyResults) && safetyResults.length ? <div style={{marginTop:8,fontSize:11,color:T.gray200,maxHeight:140,overflow:"auto"}}>{safetyResults.slice(0,6).map((r,idx)=><div key={`sr-${idx}`} style={{marginBottom:6}}>{(r.status || '').toUpperCase()} · {r.medicine_name || '-'} · {r.rule || '-'}{r.message ? `: ${r.message}` : ''}</div>)}</div> : null}<Btn variant="ghost" size="sm" style={{color:T.blue,marginTop:8}}><ExternalLink size={12}/>Langfuse</Btn></div>
      <div style={{display:"flex",flexDirection:"column",gap:8}}><Btn variant="success" size="md" style={{width:"100%",justifyContent:"center"}} disabled={checkingSafety || !safetyReady || safetyBlocked} onClick={() => setStatus("verified")}><CheckCircle size={16}/>Approve</Btn><Btn variant="secondary" size="md" style={{width:"100%",justifyContent:"center",color:T.yellow}} disabled={checkingSafety || !safetyReady || safetyBlocked} onClick={() => setStatus("verified")}><AlertTriangle size={16}/>Approve with Note</Btn><Btn variant="secondary" size="md" style={{width:"100%",justifyContent:"center",color:T.red}} onClick={() => setStatus("cancelled")}><XCircle size={16}/>Reject</Btn></div>
    </div>
  </div></div>);
}