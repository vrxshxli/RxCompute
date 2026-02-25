import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Truck, Package } from 'lucide-react';
import { ORDERS } from '../../data/mockData';
export default function WarehouseDispatch() {
  const packed=ORDERS.filter(o=>o.status==="packed"||o.status==="dispatched").map(o=>({...o,tracking:o.status==="dispatched"?"TRK-"+Math.random().toString(36).slice(2,10).toUpperCase():null}));
  return (<div><PageHeader title="Dispatch" actions={<Btn variant="primary" size="sm"><Truck size={14}/>Batch</Btn>}/>
  <div style={{display:"flex",flexDirection:"column",gap:12}}>{packed.map(o=><div key={o.order_id} style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:16,display:"flex",justifyContent:"space-between",alignItems:"center"}}>
    <div><div style={{display:"flex",alignItems:"center",gap:12,marginBottom:4}}><span style={{fontFamily:"monospace",fontSize:12,fontWeight:600}}>{o.order_id}</span><StatusPill status={o.status}/></div><div style={{fontSize:12,color:T.gray500}}>{o.items.map(x=>x.product_name.split(" ").slice(0,2).join(" ")).join(", ")}</div>{o.tracking&&<div style={{fontSize:11,fontFamily:"monospace",color:T.blue,marginTop:4}}>{o.tracking}</div>}</div>
    {o.status!=="dispatched"?<Btn variant="success" size="sm"><Truck size={12}/>Dispatch</Btn>:<span style={{fontSize:12,color:T.green,fontWeight:600}}>Dispatched</span>}
  </div>)}{packed.length===0&&<div style={{textAlign:"center",padding:60,color:T.gray400}}><Package size={48} strokeWidth={1}/><div style={{marginTop:16,fontWeight:600}}>No packed orders</div></div>}</div></div>);
}