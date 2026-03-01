import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { StatusPill, Btn, PageHeader } from '../../components/shared';
import { useAuth } from '../../context/AuthContext';
export default function PharmacyExceptions() {
  const { token, apiBase } = useAuth();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!token) return;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await fetch(`${apiBase}/exceptions/queue?limit=120`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          const txt = await res.text();
          setError(txt || "Unable to load exception queue");
          setRows([]);
          return;
        }
        const data = await res.json();
        setRows(Array.isArray(data) ? data : []);
      } catch (_) {
        setError("Network error while loading exception queue");
      }
      finally { setLoading(false); }
    };
    load();
  }, [token, apiBase]);
  const exceptions = useMemo(() => rows.slice(0, 80), [rows]);

  const resolve = async (x, action) => {
    if (!token || !x?.medicine_id) return;
    try {
      await fetch(`${apiBase}/exceptions/resolve/${x.medicine_id}?action=${encodeURIComponent(action)}&notes=${encodeURIComponent("Resolved from pharmacy dashboard")}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      setRows((prev) => prev.filter((r) => r.id !== x.id));
    } catch (_) {}
  };

  return (<div><PageHeader title="Exceptions" subtitle="Manual review"/>
  <div style={{display:"flex",flexDirection:"column",gap:12}}>
    {loading ? <div style={{fontSize:12,color:T.gray500}}>Loading exception queue...</div> : null}
    {error ? <div style={{fontSize:12,color:T.red,background:`${T.red}12`,border:`1px solid ${T.red}33`,borderRadius:8,padding:"10px 12px"}}>{error}</div> : null}
    {exceptions.map((x,i)=>
      <div key={i} style={{background:T.white,border:"1px solid "+T.gray200,borderLeft:"4px solid "+((String(x.severity||"").toLowerCase()==="critical" || String(x.severity||"").toLowerCase()==="high")?T.red:T.yellow),borderRadius:10,padding:16}}>
        <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}><span style={{fontWeight:600,color:T.gray900}}>{x.exception_type || "Exception"}</span><StatusPill status={(x.severity||"medium").toLowerCase()} size="xs"/></div>
        <div style={{fontSize:13,color:T.gray600,marginBottom:4}}>Medicine: <span style={{fontFamily:"monospace"}}>{x.medicine_name || "-"}</span></div>
        <div style={{fontSize:13,color:T.gray600,marginBottom:4}}>Level: {x.escalation_level || "-"} · Patient: {x.target_user_name || (x.target_user_id ? `User #${x.target_user_id}` : "-")}</div>
        <div style={{fontSize:12,color:T.gray500,marginBottom:4}}>{x.reasoning || x.body}</div>
        <div style={{display:"flex",gap:8,marginTop:8}}><Btn variant="primary" size="sm" onClick={()=>resolve(x,"approved")}>Resolve</Btn><Btn variant="secondary" size="sm" onClick={()=>resolve(x,"alternative_offered")}>Alternative</Btn></div>
      </div>
    )}
    {exceptions.length===0 ? <div style={{fontSize:12,color:T.gray500}}>No active exception-agent items.</div> : null}
  </div></div>);
}