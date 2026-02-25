import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { CheckCircle, Map } from 'lucide-react';
import { ORDERS } from '../../data/mockData';
export default function WarehousePickPack() {
  const items=ORDERS.filter(o=>o.status==="picking"||o.status==="pharmacy_verified").flatMap(o=>o.items.map(it=>({...it,oid:o.order_id,rack:"Rack "+String.fromCharCode(65+(it.product_id%6)),shelf:"Shelf "+(it.product_id%4+1),done:Math.random()>.5}))).slice(0,12);
  return (<div><PageHeader title="Pick & Pack" subtitle="Grouped by rack"/>
  <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(280px,1fr))",gap:12}}>{items.map((x,i)=><div key={i} style={{background:T.white,border:"1px solid "+(x.done?T.green:T.gray200),borderRadius:10,padding:16,opacity:x.done?.7:1}}>
    <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}><span style={{fontFamily:"monospace",fontSize:11,color:T.gray500}}>{x.oid}</span>{x.done&&<CheckCircle size={16} color={T.green}/>}</div>
    <div style={{fontWeight:500,color:T.gray900,marginBottom:4}}>{x.product_name}</div>
    <div style={{fontSize:12,color:T.gray500,marginBottom:8}}>Qty: {x.quantity}</div>
    <div style={{display:"flex",alignItems:"center",gap:8,padding:"8px 12px",background:T.blue+"08",borderRadius:8,fontSize:12}}><Map size={14} color={T.blue}/><span style={{color:T.blue,fontWeight:600}}>{x.rack}, {x.shelf}</span></div>
    {!x.done&&<Btn variant="primary" size="sm" style={{marginTop:10,width:"100%"}}><CheckCircle size={12}/>Pick</Btn>}
  </div>)}</div></div>);
}