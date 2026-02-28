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
          agent_name: (e?.metadata?.agent_name || '').toString().trim() || (String(e.title || '').toLowerCase().includes('scheduler') ? 'scheduler_agent' : 'safety_agent'),
          action: `${e.title} — ${e.body}`,
          trace_id: `safety-${e.id}`,
          confidence:
            Number(e?.metadata?.ocr_details?.[0]?.confidence) ||
            (e?.metadata?.agent_name === 'scheduler_agent' ? 0.93 : 0) ||
            (e.severity === 'blocked' ? 0.99 : e.severity === 'warning' ? 0.82 : 0.75),
          metadata: e.metadata || null,
          target_user_name: e.target_user_name || null,
          target_user_email: e.target_user_email || null,
          target_user_role: e.target_user_role || null,
          target_user_id: e.target_user_id || null,
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

  const renderOcrIndicators = (indicators) => {
    if (!indicators || typeof indicators !== 'object') return null;
    const pairs = Object.entries(indicators);
    if (!pairs.length) return null;
    return (
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {pairs.map(([k, v]) => (
          <span
            key={k}
            style={{
              fontSize: 10,
              border: `1px solid ${v ? T.green : T.red}`,
              color: v ? T.green : T.red,
              borderRadius: 999,
              padding: '2px 8px',
            }}
          >
            {k}: {String(v)}
          </span>
        ))}
      </div>
    );
  };

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
        <div style={{ fontSize:11, color:T.gray600 }}>
          Target user: {l.target_user_name || l.target_user_email || (l.target_user_id ? `User #${l.target_user_id}` : '-')} {l.target_user_role ? `(${l.target_user_role})` : ''}
        </div>
        <div style={{ fontSize:11, color:T.gray500 }}>
          Phase: {l?.metadata?.phase || '-'} · Triggered by: {l?.metadata?.triggered_by_role || '-'} {l?.metadata?.triggered_by_user_id ? `#${l.metadata.triggered_by_user_id}` : ''}
        </div>
        {l?.metadata?.agent_name === 'scheduler_agent' ? (
          <div style={{ fontSize:11, color:T.gray700, lineHeight:1.5 }}>
            Assigned: {l?.metadata?.assigned_pharmacy || '-'} · Score: {l?.metadata?.winning_score ?? '-'} · Fallback: {l?.metadata?.fallback_used ? 'Yes' : 'No'}
          </div>
        ) : null}
        {Array.isArray(l?.metadata?.ocr_details) && l.metadata.ocr_details.length ? (
          <div style={{ border:`1px solid ${T.gray200}`, borderRadius:8, padding:10, background:T.gray50 }}>
            {l.metadata.ocr_details.map((d, idx) => (
              <div key={`${l.id}-ocr-${idx}`} style={{ marginBottom: idx < l.metadata.ocr_details.length - 1 ? 10 : 0 }}>
                <div style={{ fontSize:12, fontWeight:700, color:T.gray900 }}>{d.medicine_name || 'Unknown medicine'}</div>
                <div style={{ fontSize:11, color:T.gray600, marginTop:4 }}>
                  Confidence: {typeof d.confidence === 'number' ? `${Math.round(d.confidence * 100)}%` : '-'}
                </div>
                <div style={{ fontSize:11, color:T.gray700, marginTop:4 }}>{d.reason || '-'}</div>
                <div style={{ marginTop:6 }}>{renderOcrIndicators(d.indicators)}</div>
              </div>
            ))}
          </div>
        ) : null}
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