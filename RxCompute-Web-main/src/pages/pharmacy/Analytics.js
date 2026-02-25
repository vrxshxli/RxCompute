import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { ShoppingCart, Zap, Shield, AlertTriangle } from 'lucide-react';
import { MEDICINES } from '../../data/mockData';
export default function PharmacyAnalytics() {
  return (<div><PageHeader title="Analytics" subtitle="PH-001"/>
  <div style={{display:"flex",gap:16,marginBottom:24,flexWrap:"wrap"}}><StatCard icon={ShoppingCart} label="Orders" value="23" trend="up" trendValue="+8%" color={T.blue}/><StatCard icon={Zap} label="AI Assist" value="87%" color={T.purple}/><StatCard icon={Shield} label="Rx Verified" value="9" color={T.orange}/><StatCard icon={AlertTriangle} label="Blocks" value="3" color={T.red}/></div>
  <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
    <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:20}}><div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:16}}>Orders — 7 Days</div><div style={{display:"flex",alignItems:"flex-end",gap:8,height:160}}>{[18,22,15,28,32,25,23].map((v,i)=><div key={i} style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",gap:4}}><span style={{fontSize:10,color:T.gray500,fontWeight:600}}>{v}</span><div style={{width:"100%",height:(v/35)*140+"px",borderRadius:6,background:i===6?T.blue:T.blue+"30"}}/><span style={{fontSize:9,color:T.gray400}}>{["M","T","W","T","F","S","S"][i]}</span></div>)}</div></div>
    <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:20}}><div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:16}}>Top Dispensed</div>{MEDICINES.slice(0,6).map((m,i)=><div key={i} style={{display:"flex",alignItems:"center",gap:12,marginBottom:12}}><span style={{width:24,height:24,borderRadius:6,background:T.orange+"15",display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:700,color:T.orange}}>{i+1}</span><span style={{fontSize:13,color:T.gray700,flex:1,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{m.name}</span><div style={{width:80,height:6,borderRadius:3,background:T.gray100,overflow:"hidden"}}><div style={{height:"100%",borderRadius:3,width:(70-i*10)+"%",background:T.orange}}/></div></div>)}</div>
  </div></div>);
}