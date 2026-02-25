import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Plus, Edit3, Trash2 } from 'lucide-react';
import { SAFETY_RULES } from '../../data/mockData';
export default function AdminSafetyRules() {
  const [rules, setRules] = useState(SAFETY_RULES);
  return (<div><PageHeader title="Safety Rules Engine" badge={rules.filter(r=>r.active).length+" active"} actions={<Btn variant="primary" size="sm"><Plus size={14}/>Add Rule</Btn>}/>
  <div style={{display:"flex",flexDirection:"column",gap:12}}>{rules.map(r=><div key={r.id} style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:10,padding:20,opacity:r.active?1:.6}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}><span style={{fontWeight:600,fontSize:15,color:T.gray900}}>{r.name}</span><Toggle on={r.active} onChange={()=>setRules(rs=>rs.map(x=>x.id===r.id?{...x,active:!x.active}:x))}/></div>
    <div style={{background:T.navy900,borderRadius:8,padding:12,fontFamily:"monospace",fontSize:12,color:T.gray300,marginBottom:12}}>IF <span style={{color:T.yellow}}>{r.condition.field}</span> {r.condition.operator} <span style={{color:T.orange}}>{String(r.condition.value)}</span></div>
    <div style={{display:"flex",alignItems:"center",gap:12,marginBottom:12}}><span style={{fontSize:12,color:T.gray500}}>THEN</span><StatusPill status={r.action} size="xs"/></div>
    <div style={{fontSize:13,color:T.gray600,fontStyle:"italic",marginBottom:12}}>"{r.message}"</div>
    <div style={{display:"flex",gap:12}}><Btn variant="ghost" size="sm"><Edit3 size={12}/>Edit</Btn><Btn variant="ghost" size="sm" style={{color:T.red}}><Trash2 size={12}/>Delete</Btn></div>
  </div>)}</div></div>);
}