import React, { useEffect, useState } from 'react';
import T from '../../utils/tokens';
import { AgentBadge, Btn, PageHeader } from '../../components/shared';
import { ExternalLink } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
export default function AdminAgentTraces() {
  const { token, apiBase } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/notifications/safety-events?limit=150`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok) {
        const mapped = (Array.isArray(data) ? data : []).map((e) => ({
          id: e.id,
          agent_name: 'safety_agent',
          action: `${e.title} — ${e.body}`,
          trace_id: `safety-${e.id}`,
          confidence: e.severity === 'blocked' ? 0.99 : e.severity === 'warning' ? 0.82 : 0.75,
          created_at: e.created_at,
        }));
        setLogs(mapped);
      }
    } catch (_) {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [token, apiBase]);

  return (<div><PageHeader title="Agent Observability" subtitle="Full traceability"/>
  <div style={{marginBottom:24, display:"flex", gap:8, alignItems:"center"}}><button style={{display:"flex",alignItems:"center",gap:10,padding:"14px 24px",background:T.blue,color:T.white,border:"none",borderRadius:10,cursor:"pointer",fontWeight:600,fontSize:14,boxShadow:"0 4px 12px "+T.blue+"40"}}><ExternalLink size={18}/>Open Langfuse Dashboard →</button><Btn variant="secondary" size="sm" onClick={load}>{loading ? "Refreshing..." : "Refresh"}</Btn><p style={{fontSize:12,color:T.gray400,marginTop:8}}>Safety traces + notifications</p></div>
  {/* Trace cards instead of table */}
  <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(320px, 1fr))", gap:12 }}>
    {logs.map(l => (
      <div key={l.id} style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:10, padding:16, display:"flex", flexDirection:"column", gap:8 }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
          <AgentBadge agent={l.agent_name} />
          <span style={{ fontFamily:"monospace", fontSize:11, color:T.gray400 }}>{new Date(l.created_at).toLocaleTimeString("en-GB",{hour12:false})}</span>
        </div>
        <div style={{ fontSize:13, color:T.gray800, lineHeight:1.5 }}>{l.action}</div>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
          <span style={{ fontFamily:"monospace", fontSize:10, color:T.gray400 }}>{l.trace_id}</span>
          <div style={{ display:"flex", alignItems:"center", gap:6 }}>
            <div style={{ width:48, height:4, borderRadius:2, background:T.gray100, overflow:"hidden" }}><div style={{ height:"100%", width:l.confidence*100+"%", borderRadius:2, background:l.confidence>.9?T.green:l.confidence>.7?T.yellow:T.red }} /></div>
            <span style={{ fontSize:10, fontFamily:"monospace", color:T.gray500 }}>{(l.confidence*100).toFixed(0)}%</span>
          </div>
        </div>
      </div>
    ))}
    {logs.length === 0 ? <div style={{fontSize:12,color:T.gray500}}>No traces found yet. Trigger safety checks from order flow.</div> : null}
  </div></div>);
}