import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Play, CheckCircle, PackageCheck } from 'lucide-react';
import { ORDERS } from '../../data/mockData';
export default function WarehouseFulfillment() {
  const tasks=ORDERS.filter(o=>["confirmed","pharmacy_verified","picking","packed"].includes(o.status)).map((o,i)=>({...o,ts:["ready_to_pick","picking","ready_to_pack","dispatched"][i%4],rack:"Rack "+String.fromCharCode(65+(i%6))+(Math.floor(i/6)+1)}));
  const sc={ready_to_pick:T.blue,picking:T.yellow,ready_to_pack:T.green,dispatched:T.gray400};
  const sl={ready_to_pick:"Ready to Pick",picking:"Picking",ready_to_pack:"Ready to Pack",dispatched:"Dispatched"};
  return (<div><PageHeader title="Fulfillment Queue" badge={String(tasks.length)}/>
  <div style={{display:"flex",flexDirection:"column",gap:12}}>{tasks.map(t=><div key={t.order_id} style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:16,borderLeft:"4px solid "+(sc[t.ts]||T.gray400)}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
      <div style={{display:"flex",alignItems:"center",gap:12}}><span style={{fontFamily:"monospace",fontSize:12,fontWeight:600}}>{t.order_id}</span><span style={{background:(sc[t.ts]||T.gray400)+"15",color:sc[t.ts],padding:"3px 10px",borderRadius:6,fontSize:10,fontWeight:700,textTransform:"uppercase"}}>{sl[t.ts]}</span></div>
      <span style={{fontSize:12,color:T.gray400}}>to {t.pharmacy_node}</span>
    </div>
    <div style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:12}}>{t.items.map((x,i)=><div key={i} style={{padding:"8px 14px",background:T.gray50,borderRadius:8,fontSize:12,display:"flex",gap:8,alignItems:"center"}}><span style={{fontWeight:500,color:T.gray800}}>{x.product_name.split(" ").slice(0,3).join(" ")}</span><span style={{color:T.blue,fontWeight:700}}>x{x.quantity}</span><span style={{color:T.gray400,fontSize:10}}>{t.rack}</span></div>)}</div>
    <div style={{display:"flex",gap:8}}>{t.ts==="ready_to_pick"&&<Btn variant="primary" size="sm"><Play size={12}/>Start Pick</Btn>}{t.ts==="picking"&&<Btn variant="primary" size="sm"><CheckCircle size={12}/>Verify</Btn>}{t.ts==="ready_to_pack"&&<Btn variant="success" size="sm"><PackageCheck size={12}/>Pack</Btn>}{t.ts==="dispatched"&&<span style={{fontSize:12,color:T.green,fontWeight:600}}>Done</span>}</div>
  </div>)}</div></div>);
}