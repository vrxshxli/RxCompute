import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { XCircle, Clock, CheckCircle, RefreshCw, Send, FileText, AlertTriangle } from 'lucide-react';
import { REFILL_ALERTS } from '../../data/mockData';

export default function AdminRefillAlerts() {
  const [search, setSearch] = useState("");
  const overdue = REFILL_ALERTS.filter(a=>a.risk_level==="overdue").length;
  const dueWeek = REFILL_ALERTS.filter(a=>a.days_remaining>=0&&a.days_remaining<=7).length;
  const notified = REFILL_ALERTS.filter(a=>a.status==="notified").length;
  const filtered = search ? REFILL_ALERTS.filter(a=>a.patient_id.toLowerCase().includes(search.toLowerCase())||a.medicine.toLowerCase().includes(search.toLowerCase())) : REFILL_ALERTS;

  const riskColor = r => r==="overdue"?T.red:r==="high"?T.orange:r==="medium"?T.yellow:T.green;

  return (<div>
    <PageHeader title="Proactive Refill Alerts" badge={String(REFILL_ALERTS.length)} actions={<Btn variant="primary" size="sm"><RefreshCw size={14}/>Run Predictions</Btn>} />
    <div style={{display:"flex",gap:16,marginBottom:24,flexWrap:"wrap"}}>
      <StatCard icon={XCircle} label="Overdue" value={String(overdue)} color={T.red}/>
      <StatCard icon={Clock} label="Due This Week" value={String(dueWeek)} color={T.yellow}/>
      <StatCard icon={CheckCircle} label="Notified" value={String(notified)} color={T.green}/>
    </div>
    <div style={{marginBottom:16}}><SearchInput value={search} onChange={setSearch} placeholder="Search patient or medicine..."/></div>

    {/* Horizontal scrolling risk cards */}
    <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(300px, 1fr))", gap:12, marginBottom:24 }}>
      {filtered.slice(0,12).map(a => (
        <div key={a.id} style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:10, padding:16, borderLeft:"4px solid "+riskColor(a.risk_level), transition:"box-shadow .2s" }}
          onMouseEnter={e=>e.currentTarget.style.boxShadow="0 4px 16px rgba(0,0,0,.06)"}
          onMouseLeave={e=>e.currentTarget.style.boxShadow="none"}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
            <span style={{ fontFamily:"monospace", fontSize:12, fontWeight:600, color:T.gray700 }}>{a.patient_id}</span>
            <StatusPill status={a.risk_level} size="xs" />
          </div>
          <div style={{ fontSize:14, fontWeight:600, color:T.gray900, marginBottom:4 }}>{a.medicine.split(" ").slice(0,4).join(" ")}</div>
          <div style={{ fontSize:12, color:T.gray500, marginBottom:8 }}>{a.dosage} · Last: {a.last_purchase}</div>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
            <div>
              <span style={{ fontSize:22, fontWeight:800, color:riskColor(a.risk_level) }}>{a.days_remaining}d</span>
              <span style={{ fontSize:11, color:T.gray400, marginLeft:4 }}>{a.days_remaining<0?"overdue":"remaining"}</span>
            </div>
            <div style={{ display:"flex", alignItems:"center", gap:6 }}>
              <StatusPill status={a.status} size="xs" />
              {a.status==="pending" && <Btn variant="ghost" size="sm"><Send size={12}/></Btn>}
            </div>
          </div>
        </div>
      ))}
    </div>

    <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:10,padding:20}}>
      <div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:12,display:"flex",alignItems:"center",gap:8}}><FileText size={16} color={T.gray600}/>Prediction Logic</div>
      <div style={{background:T.navy900,borderRadius:8,padding:16,fontFamily:"monospace",fontSize:12,color:T.gray300,lineHeight:1.8}}>
        <div><span style={{color:T.green}}>// Formula</span></div>
        <div>days_supply = (qty * pkg_units) / doses_per_day</div>
        <div>predicted_runout = last_purchase + days_supply</div>
        <div>days_remaining = predicted_runout - <span style={{color:T.orange}}>today</span>()</div>
      </div>
    </div>
  </div>);
}