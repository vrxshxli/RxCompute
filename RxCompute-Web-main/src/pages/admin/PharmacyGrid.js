import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { PHARMACY_NODES } from '../../data/mockData';
export default function AdminPharmacyGrid() {
  const rh=[{o:"ORD-043",n:"PH-002",r:"stock 100%, 2.3km, load 35%"},{o:"ORD-044",n:"PH-001",r:"stock 98%, 1.1km, load 42%"},{o:"ORD-045",n:"PH-002",r:"stock 100%, 2.3km, load 38%"},{o:"ORD-046",n:"PH-001",r:"stock 96%, load 48%"},{o:"ORD-047",n:"PH-002",r:"PH-003 offline, rerouted"}];
  return (<div><PageHeader title="Virtual Pharmacy Grid" subtitle="Node health & routing"/>
  <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:16,marginBottom:24}}>
    {PHARMACY_NODES.map(n=><div key={n.node_id} style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:24}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16}}><span style={{fontFamily:"monospace",fontSize:14,fontWeight:600,color:T.gray900}}>{n.node_id}</span><div style={{display:"flex",alignItems:"center",gap:6}}><span style={{width:8,height:8,borderRadius:"50%",background:n.active?T.green:T.red}}/><span style={{fontSize:12,color:n.active?T.green:T.red,fontWeight:500}}>{n.active?"Active":"Offline"}</span></div></div>
      <div style={{fontSize:14,fontWeight:500,color:T.gray900,marginBottom:4}}>{n.name}</div><div style={{fontSize:12,color:T.gray500,marginBottom:16}}>{n.location}</div>
      <div style={{marginBottom:12}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}><span style={{fontSize:11,color:T.gray500}}>Load</span><span style={{fontSize:11,fontWeight:600}}>{n.load}%</span></div><div style={{height:8,borderRadius:4,background:T.gray100,overflow:"hidden"}}><div style={{height:"100%",borderRadius:4,width:n.load+"%",background:n.load>80?T.red:n.load>50?T.yellow:T.green}}/></div></div>
      <div style={{fontSize:12,color:T.gray500}}>{n.stock_count}/52 in stock</div>
    </div>)}
  </div>
  <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:20}}>
    <div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:16}}>Routing History</div>
    {rh.map((x,i)=><div key={i} style={{display:"flex",alignItems:"center",gap:12,padding:"10px 0",borderBottom:i<rh.length-1?"1px solid "+T.gray100:"none"}}><span style={{fontFamily:"monospace",fontSize:12,color:T.orange,fontWeight:600}}>{x.o}</span><span style={{color:T.gray400}}>→</span><span style={{fontFamily:"monospace",fontSize:12,color:T.blue,fontWeight:600}}>{x.n}</span><span style={{fontSize:12,color:T.gray500}}>{x.r}</span></div>)}
  </div></div>);
}