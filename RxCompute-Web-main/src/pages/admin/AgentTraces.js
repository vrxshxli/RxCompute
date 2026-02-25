import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { ExternalLink } from 'lucide-react';
import { AGENT_LOGS } from '../../data/mockData';
export default function AdminAgentTraces() {
  return (<div><PageHeader title="Agent Observability" subtitle="Full traceability"/>
  <div style={{marginBottom:24}}><button style={{display:"flex",alignItems:"center",gap:10,padding:"14px 24px",background:T.blue,color:T.white,border:"none",borderRadius:10,cursor:"pointer",fontWeight:600,fontSize:14,boxShadow:"0 4px 12px "+T.blue+"40"}}><ExternalLink size={18}/>Open Langfuse Dashboard →</button><p style={{fontSize:12,color:T.gray400,marginTop:8}}>Public link — judges access without login</p></div>
  {/* Trace cards instead of table */}
  <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(320px, 1fr))", gap:12 }}>
    {AGENT_LOGS.map(l => (
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
  </div></div>);
}