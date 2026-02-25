import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Zap } from 'lucide-react';
import { MEDICINES } from '../../data/mockData';
export default function WarehouseShelfHeatmap() {
  return (<div><PageHeader title="Shelf Heatmap"/>
  <div style={{display:"flex",gap:16,marginBottom:20}}>{[["Healthy",T.green],["Low",T.yellow],["Critical",T.red],["Out",T.gray900]].map(([l,c])=><div key={l} style={{display:"flex",alignItems:"center",gap:6,fontSize:12,color:T.gray600}}><span style={{width:16,height:16,borderRadius:4,background:c}}/>{l}</div>)}</div>
  <div style={{display:"grid",gridTemplateColumns:"1fr 280px",gap:16}}>
    <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:24}}><div style={{display:"grid",gridTemplateColumns:"repeat(8,1fr)",gap:8}}>{MEDICINES.map(m=>{const c=m.stock>50?T.green:m.stock>20?T.yellow:m.stock>0?T.red:T.gray900;return<div key={m.id} title={m.name} style={{height:60,borderRadius:8,background:c,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",cursor:"pointer",transition:"transform .15s",color:T.white,fontWeight:700}} onMouseEnter={e=>e.currentTarget.style.transform="scale(1.1)"} onMouseLeave={e=>e.currentTarget.style.transform="scale(1)"}><span style={{fontSize:15}}>{m.stock}</span><span style={{fontSize:8,opacity:.8}}>{m.name.split(" ")[0]}</span></div>})}</div></div>
    <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:20}}><div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:16,display:"flex",alignItems:"center",gap:8}}><Zap size={16} color={T.orange}/>Auto-Reorder</div>{MEDICINES.filter(m=>m.stock<25).slice(0,5).map(m=><div key={m.id} style={{padding:"10px 0",borderBottom:"1px solid "+T.gray100}}><div style={{fontWeight:500,fontSize:13,color:T.gray800}}>{m.name}</div><div style={{fontSize:11,color:T.gray500,marginTop:2}}>Stock: {m.stock}</div><div style={{fontSize:11,color:T.orange,marginTop:2}}>Suggest: {Math.floor(Math.random()*50+30)} units</div></div>)}</div>
  </div></div>);
}