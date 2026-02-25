import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Eye, Globe, Zap } from 'lucide-react';
import { WEBHOOK_LOGS } from '../../data/mockData';
export default function AdminWebhookLogs() {
  const [expanded, setExpanded] = useState(null);
  const ec = {order_confirmed:T.green,fulfillment_request:T.blue,notification_sent:T.yellow,stock_alert:T.red};
  return (<div><PageHeader title="Webhook Activity" subtitle="Proof of real actions"/>
  {/* Timeline-style webhook feed */}
  <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
    {WEBHOOK_LOGS.map(w => (
      <div key={w.id} style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:10, padding:16, display:"flex", alignItems:"center", gap:16, transition:"box-shadow .2s" }}
        onMouseEnter={e=>e.currentTarget.style.boxShadow="0 2px 12px rgba(0,0,0,.05)"}
        onMouseLeave={e=>e.currentTarget.style.boxShadow="none"}>
        <div style={{ width:40, height:40, borderRadius:10, background:(ec[w.event_type]||T.gray400)+"12", display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>
          <Globe size={18} color={ec[w.event_type]||T.gray400} />
        </div>
        <div style={{ flex:1 }}>
          <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:4 }}>
            <span style={{ background:(ec[w.event_type]||T.gray400)+"15", color:ec[w.event_type]||T.gray400, padding:"2px 8px", borderRadius:4, fontSize:10, fontWeight:700, textTransform:"uppercase" }}>{w.event_type.replace(/_/g," ")}</span>
            <span style={{ background:w.response_status===200?T.green+"15":T.red+"15", color:w.response_status===200?T.green:T.red, padding:"2px 8px", borderRadius:4, fontSize:11, fontWeight:700, fontFamily:"monospace" }}>{w.response_status}</span>
          </div>
          <div style={{ fontFamily:"monospace", fontSize:11, color:T.gray500, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{w.target_url}</div>
        </div>
        <span style={{ fontSize:11, color:T.gray400, whiteSpace:"nowrap" }}>{new Date(w.created_at).toLocaleTimeString("en-GB",{hour12:false})}</span>
        <Btn variant="ghost" size="sm" onClick={()=>setExpanded(expanded===w.id?null:w.id)}><Eye size={14}/></Btn>
      </div>
    ))}
  </div>
  {expanded && <div style={{marginTop:8,background:T.navy900,borderRadius:10,padding:16}}><pre style={{fontFamily:"monospace",fontSize:12,color:T.gray300,margin:0,whiteSpace:"pre-wrap"}}>{JSON.stringify(WEBHOOK_LOGS.find(w=>w.id===expanded)?.payload,null,2)}</pre></div>}
  </div>);
}