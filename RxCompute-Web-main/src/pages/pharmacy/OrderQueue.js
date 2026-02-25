import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { CheckCircle } from 'lucide-react';
import { ORDERS, MEDICINES, REFILL_ALERTS } from '../../data/mockData';
export default function PharmacyOrderQueue() {
  const urgent=ORDERS.filter(o=>o.items.some(it=>MEDICINES.find(m=>m.id===it.product_id)?.rx));
  const normal=ORDERS.filter(o=>!urgent.includes(o)&&o.status!=="delivered"&&o.status!=="cancelled");
  const scheduled=REFILL_ALERTS.filter(a=>a.status==="pending").slice(0,5);
  const Col=({title,color,children,count})=><div style={{flex:1,minWidth:280}}><div style={{background:color,height:3,borderRadius:"10px 10px 0 0"}}/><div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:"0 0 10px 10px",padding:16}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:16}}><span style={{fontWeight:600,fontSize:14,color:T.gray900}}>{title}</span><span style={{background:color+"15",color,padding:"2px 8px",borderRadius:4,fontSize:11,fontWeight:700}}>{count}</span></div><div style={{display:"flex",flexDirection:"column",gap:12}}>{children}</div></div></div>;
  const OC=({order,type})=><div style={{border:"1px solid "+T.gray200,borderLeft:"3px solid "+(type==="urgent"?T.red:type==="normal"?T.blue:T.gray400),borderRadius:8,padding:14}}>
    <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}><span style={{fontFamily:"monospace",fontSize:11,color:T.gray500}}>{order.order_id}</span></div>
    <div style={{fontSize:13,color:T.gray700,marginBottom:4}}>{order.patient_name}</div>
    <div style={{fontSize:12,color:T.gray500,marginBottom:8}}>{order.items?.map(x=>x.product_name.split(" ").slice(0,3).join(" ")+" x"+x.quantity).join(", ")}</div>
    {type==="urgent"&&<div style={{fontSize:11,color:T.red,fontWeight:500,marginBottom:8}}>Prescription Required</div>}
    {type==="normal"&&<div style={{display:"flex",alignItems:"center",gap:6,marginBottom:8}}><span style={{fontSize:11,color:T.gray500}}>AI:</span><div style={{width:60,height:4,borderRadius:2,background:T.gray100,overflow:"hidden"}}><div style={{height:"100%",width:"96%",borderRadius:2,background:T.green}}/></div><span style={{fontSize:11,fontWeight:600,color:T.green}}>96%</span></div>}
    <div style={{display:"flex",gap:8}}>{type==="urgent"&&<><Btn variant="primary" size="sm">Review</Btn><Btn variant="secondary" size="sm" style={{color:T.red}}>Reject</Btn></>}{type==="normal"&&<><Btn variant="success" size="sm"><CheckCircle size={12}/>Approve</Btn><Btn variant="secondary" size="sm">Review</Btn></>}</div>
  </div>;
  return (<div><PageHeader title="Order Queue" badge={String(ORDERS.length)} actions={<Btn variant="success" size="sm"><CheckCircle size={14}/>Approve All</Btn>}/>
  <div style={{display:"flex",gap:16,overflowX:"auto"}}><Col title="Urgent" color={T.red} count={urgent.length}>{urgent.slice(0,4).map(o=><OC key={o.order_id} order={o} type="urgent"/>)}</Col><Col title="Normal" color={T.blue} count={normal.length}>{normal.slice(0,4).map(o=><OC key={o.order_id} order={o} type="normal"/>)}</Col><Col title="Scheduled" color={T.gray400} count={scheduled.length}>{scheduled.map(a=><div key={a.id} style={{border:"1px solid "+T.gray200,borderLeft:"3px solid "+T.gray400,borderRadius:8,padding:14}}><div style={{fontSize:12,color:T.gray700}}>{a.patient_id} — {a.medicine.split(" ").slice(0,3).join(" ")}</div><div style={{fontSize:11,color:T.gray500,marginTop:4}}>Predicted: {a.predicted_runout}</div></div>)}</Col></div></div>);
}