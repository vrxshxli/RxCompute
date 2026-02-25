import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
export default function PharmacyExceptions() {
  return (<div><PageHeader title="Exceptions" subtitle="Manual review"/>
  <div style={{display:"flex",flexDirection:"column",gap:12}}>
    {[{t:"Prescription Required",o:"ORD-004",m:"Mucosolvan 75mg",p:"PAT004",s:"high"},{t:"High Quantity",o:"ORD-011",m:"Paracetamol x8",p:"PAT011",s:"medium"},{t:"Drug Interaction",o:"ORD-015",m:"Ramipril+Ibuprofen",p:"PAT015",s:"high"}].map((x,i)=>
      <div key={i} style={{background:T.white,border:"1px solid "+T.gray200,borderLeft:"4px solid "+(x.s==="high"?T.red:T.yellow),borderRadius:10,padding:16}}>
        <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}><span style={{fontWeight:600,color:T.gray900}}>{x.t}</span><StatusPill status={x.s} size="xs"/></div>
        <div style={{fontSize:13,color:T.gray600,marginBottom:4}}>Order: <span style={{fontFamily:"monospace"}}>{x.o}</span></div>
        <div style={{fontSize:13,color:T.gray600,marginBottom:4}}>{x.m} · {x.p}</div>
        <div style={{display:"flex",gap:8,marginTop:8}}><Btn variant="primary" size="sm">Resolve</Btn><Btn variant="secondary" size="sm">Escalate</Btn></div>
      </div>
    )}
  </div></div>);
}