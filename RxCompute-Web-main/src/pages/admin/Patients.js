import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { PATIENTS } from '../../data/mockData';
export default function AdminPatients() {
  const [search, setSearch] = useState("");
  const filtered = search?PATIENTS.filter(p=>p.name.toLowerCase().includes(search.toLowerCase())||p.pid.toLowerCase().includes(search.toLowerCase())):PATIENTS;
  return (<div><PageHeader title="Patients" badge={String(PATIENTS.length)}/>
  <div style={{marginBottom:16}}><SearchInput value={search} onChange={setSearch} placeholder="Search patients..."/></div>
  {/* Grid of patient cards */}
  <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(220px, 1fr))", gap:12 }}>
    {filtered.map(p => (
      <div key={p.pid} style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:10, padding:16, transition:"box-shadow .2s" }}
        onMouseEnter={e=>e.currentTarget.style.boxShadow="0 4px 16px rgba(0,0,0,.06)"}
        onMouseLeave={e=>e.currentTarget.style.boxShadow="none"}>
        <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:12 }}>
          <div style={{ width:36, height:36, borderRadius:"50%", background:T.blue+"15", display:"flex", alignItems:"center", justifyContent:"center", fontSize:13, fontWeight:700, color:T.blue }}>{p.name.split(" ").map(n=>n[0]).join("")}</div>
          <div><div style={{ fontSize:14, fontWeight:600, color:T.gray900 }}>{p.name}</div><div style={{ fontFamily:"monospace", fontSize:11, color:T.gray400 }}>{p.pid}</div></div>
        </div>
        <div style={{ display:"flex", gap:16, fontSize:12, color:T.gray500 }}>
          <span>Age: {p.age}</span><span>{p.gender==="M"?"Male":"Female"}</span>
        </div>
      </div>
    ))}
  </div></div>);
}