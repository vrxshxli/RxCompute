import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Edit3, Search as SI2 } from 'lucide-react';
import { MEDICINES } from '../../data/mockData';
export default function PharmacyInventory() {
  const [search,setSearch]=useState("");
  const fd=search?MEDICINES.filter(m=>m.name.toLowerCase().includes(search.toLowerCase())):MEDICINES;
  return (<div><PageHeader title="Pharmacy Inventory" subtitle="PH-001" actions={<Btn variant="secondary" size="sm"><SI2 size={14}/>Scan</Btn>}/>
  <div style={{marginBottom:16}}><SearchInput value={search} onChange={setSearch} placeholder="Search..."/></div>
  <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:10}}>
    {fd.slice(0,30).map(m=>(
      <div key={m.id} style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:8,padding:14}}>
        <div style={{fontSize:13,fontWeight:600,color:T.gray900,marginBottom:6,lineHeight:1.3}}>{m.name}</div>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div style={{display:"flex",alignItems:"center",gap:4}}><StockDot level={m.stock}/><span style={{fontWeight:700,color:T.gray900}}>{m.stock}</span></div>
          <span style={{fontSize:13,fontWeight:600,color:T.blue}}>EUR {m.price.toFixed(2)}</span>
        </div>
      </div>
    ))}
  </div></div>);
}