import React, { useEffect, useState } from 'react';
import T from '../../utils/tokens';
import { AgentBadge, Btn, PageHeader } from '../../components/shared';
import { ExternalLink } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
export default function AdminAgentTraces() {
  const { token, apiBase } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [agentFilter, setAgentFilter] = useState('all');
  const [agentOptions, setAgentOptions] = useState([]);
  const [search, setSearch] = useState('');
  const [searchDebounced, setSearchDebounced] = useState('');

  const load = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const qs = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (agentFilter && agentFilter !== 'all') qs.set('agent_name', agentFilter);
      if (searchDebounced.trim()) qs.set('search', searchDebounced.trim());
      const res = await fetch(`${apiBase}/notifications/agent-traces?${qs.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok) {
        const mapped = (Array.isArray(data?.items) ? data.items : []).map((e) => ({
          id: e.id,
          agent_name: e.agent_name || (e?.metadata?.agent_name || '').toString().trim() || 'safety_agent',
          action: `${e.title || ''} — ${e.body || ''}`,
          trace_id: e.trace_id || `trace-${e.id}`,
          confidence:
            Number(e?.metadata?.ocr_details?.[0]?.confidence) ||
            (e?.metadata?.agent_name === 'scheduler_agent' ? 0.93 : 0) ||
            (String(e?.title || '').toLowerCase().includes('blocked') ? 0.99 : String(e?.title || '').toLowerCase().includes('warning') ? 0.82 : 0.75),
          metadata: e.metadata || null,
          target_user_name: e.target_user_name || null,
          target_user_email: e.target_user_email || null,
          target_user_role: e.target_user_role || null,
          target_user_id: e.target_user_id || null,
          created_at: e.created_at,
        }));
        setLogs(mapped);
        setTotal(Number(data?.total || 0));
        setTotalPages(Math.max(1, Number(data?.total_pages || 1)));
        setAgentOptions(Array.isArray(data?.agent_options) ? data.agent_options : []);
      }
    } catch (_) {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const id = setTimeout(() => {
      setPage(1);
      setSearchDebounced(search);
    }, 280);
    return () => clearTimeout(id);
  }, [search]);

  useEffect(() => {
    load();
  }, [token, apiBase, page, pageSize, agentFilter, searchDebounced]);

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
  <div style={{marginBottom:16, display:"flex", gap:8, alignItems:"center", flexWrap:"wrap"}}>
    <button
      onClick={() => window.open("https://cloud.langfuse.com", "_blank", "noopener,noreferrer")}
      style={{display:"flex",alignItems:"center",gap:10,padding:"14px 24px",background:T.blue,color:T.white,border:"none",borderRadius:10,cursor:"pointer",fontWeight:600,fontSize:14,boxShadow:"0 4px 12px "+T.blue+"40"}}
    >
      <ExternalLink size={18}/>Open Langfuse Dashboard →
    </button>
    <select value={agentFilter} onChange={(e)=>{ setPage(1); setAgentFilter(e.target.value); }} style={{padding:"10px 12px", borderRadius:8, border:"1px solid "+T.gray300}}>
      <option value="all">All agents</option>
      {agentOptions.map((a) => <option key={a} value={a}>{a}</option>)}
    </select>
    <input
      value={search}
      onChange={(e)=>setSearch(e.target.value)}
      onKeyDown={(e)=>{ if (e.key === "Enter") { setPage(1); setSearchDebounced(search); } }}
      placeholder="Search trace text..."
      style={{padding:"10px 12px", borderRadius:8, border:"1px solid "+T.gray300, minWidth:220}}
    />
    <Btn variant="secondary" size="sm" onClick={()=>{ setPage(1); setSearchDebounced(search); }}>{loading ? "Refreshing..." : "Refresh"}</Btn>
    <p style={{fontSize:12,color:T.gray400,marginTop:8}}>Showing {logs.length} of {total} traces</p>
  </div>
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
          Target user: {l.target_user_name || l?.metadata?.target_user_name || l.target_user_email || (l.target_user_id ? `User #${l.target_user_id}` : '-')} {l.target_user_role ? `(${l.target_user_role})` : ''}
        </div>
        <div style={{ fontSize:11, color:T.gray500 }}>
          Phase: {l?.metadata?.phase || '-'} · Triggered by: {l?.metadata?.triggered_by_role || '-'} {l?.metadata?.triggered_by_user_id ? `#${l.metadata.triggered_by_user_id}` : ''}
        </div>
        {l?.metadata?.agent_name === 'scheduler_agent' ? (
          <div style={{ fontSize:11, color:T.gray700, lineHeight:1.5 }}>
            Assigned: {l?.metadata?.assigned_pharmacy || '-'} · Score: {l?.metadata?.winning_score ?? '-'} · Fallback: {l?.metadata?.fallback_used ? 'Yes' : 'No'}
          </div>
        ) : null}
        {l?.metadata?.agent_name === 'prediction_agent' ? (
          <div style={{ fontSize:11, color:T.gray700, lineHeight:1.5 }}>
            Target: {l?.metadata?.target_user_name || (l?.metadata?.target_user_id ? `#${l.metadata.target_user_id}` : '-')} · Candidates: {l?.metadata?.candidate_count ?? l?.metadata?.prediction_count ?? '-'} · Alerts: {l?.metadata?.actions?.alerts_created ?? l?.metadata?.alerts_created ?? '-'}
          </div>
        ) : null}
        {l?.metadata?.rag_context ? (
          <div style={{ fontSize:11, color:T.gray700, lineHeight:1.5 }}>
            RAG evidence: candidates {l?.metadata?.rag_context?.total_candidates ?? '-'} · snippets {Array.isArray(l?.metadata?.rag_context?.snippets) ? l.metadata.rag_context.snippets.length : (Array.isArray(l?.metadata?.rag_context?.evidence_by_medicine) ? l.metadata.rag_context.evidence_by_medicine.length : '-')}
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
    {logs.length === 0 ? <div style={{fontSize:12,color:T.gray500}}>No traces found yet. Trigger agent flows from order/prediction modules.</div> : null}
  </div>
  <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginTop:14}}>
    <span style={{fontSize:12, color:T.gray500}}>Page {page} / {totalPages}</span>
    <div style={{display:"flex", gap:8}}>
      <Btn variant="secondary" size="sm" onClick={()=>setPage((p)=>Math.max(1,p-1))} disabled={page<=1 || loading}>Prev</Btn>
      <Btn variant="secondary" size="sm" onClick={()=>setPage((p)=>Math.min(totalPages,p+1))} disabled={page>=totalPages || loading}>Next</Btn>
    </div>
  </div>
  </div>);
}