import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Zap, CheckCircle, AlertTriangle, XCircle, ExternalLink } from 'lucide-react';
import { ORDERS, PATIENTS } from '../../data/mockData';
export default function PharmacyVerify() {
  const o=ORDERS[0]; const p=PATIENTS[0];
  return (<div><PageHeader title="Order Verification" subtitle={o.order_id}/>
  <div style={{display:"grid",gridTemplateColumns:"1.4fr 1fr",gap:16}}>
    <div>
      <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:10,padding:20,marginBottom:16}}><div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:12}}>Patient</div><div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>{[["ID",p.pid],["Name",p.name],["Age",p.age],["Gender",p.gender]].map(([l,v])=><div key={l}><div style={{fontSize:11,color:T.gray400,textTransform:"uppercase"}}>{l}</div><div style={{fontSize:13,color:T.gray800,fontWeight:500}}>{v}</div></div>)}</div></div>
      <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:10,padding:20}}><div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:12}}>Items</div>{o.items.map((it,i)=><div key={i} style={{display:"flex",justifyContent:"space-between",padding:"10px 0",borderBottom:i<o.items.length-1?"1px solid "+T.gray100:"none"}}><div><div style={{fontWeight:500,color:T.gray800}}>{it.product_name}</div><div style={{fontSize:11,color:T.gray400}}>Qty: {it.quantity} · EUR {it.unit_price.toFixed(2)}</div></div></div>)}<div style={{display:"flex",justifyContent:"flex-end",paddingTop:12,fontSize:15,fontWeight:700}}>EUR {o.total_price.toFixed(2)}</div></div>
    </div>
    <div>
      <div style={{background:T.navy900,borderRadius:10,padding:20,color:T.gray300,marginBottom:16}}><div style={{fontWeight:600,fontSize:14,color:T.white,marginBottom:16,display:"flex",alignItems:"center",gap:8}}><Zap size={16} color={T.yellow}/>AI Analysis</div>{[{i:"OK",t:"Prescription: NOT required",c:T.green},{i:"OK",t:"Interactions: None",c:T.green},{i:"OK",t:"Dosage: Normal",c:T.green},{i:">>",t:"Recommendation: APPROVE",c:T.blue}].map((x,j)=><div key={j} style={{display:"flex",gap:10,marginBottom:12,fontSize:13}}><span style={{color:x.c,fontWeight:700}}>{x.i}</span><span style={{color:x.c}}>{x.t}</span></div>)}<Btn variant="ghost" size="sm" style={{color:T.blue,marginTop:8}}><ExternalLink size={12}/>Langfuse</Btn></div>
      <div style={{display:"flex",flexDirection:"column",gap:8}}><Btn variant="success" size="md" style={{width:"100%",justifyContent:"center"}}><CheckCircle size={16}/>Approve</Btn><Btn variant="secondary" size="md" style={{width:"100%",justifyContent:"center",color:T.yellow}}><AlertTriangle size={16}/>Modify</Btn><Btn variant="secondary" size="md" style={{width:"100%",justifyContent:"center",color:T.red}}><XCircle size={16}/>Reject</Btn></div>
    </div>
  </div></div>);
}