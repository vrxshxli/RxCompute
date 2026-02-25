import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { ORDERS } from '../../data/mockData';

export default function AdminOrders() {
  const [search, setSearch] = useState("");
  const filtered = search ? ORDERS.filter(o=>o.order_id.toLowerCase().includes(search.toLowerCase())||o.patient_name.toLowerCase().includes(search.toLowerCase())) : ORDERS;
  const groups = {};
  filtered.forEach(o => { if(!groups[o.status]) groups[o.status]=[]; groups[o.status].push(o); });
  const statusOrder = ["pending","confirmed","pharmacy_verified","picking","packed","dispatched","delivered","cancelled"];
  const statusColor = {pending:T.yellow,confirmed:T.blue,pharmacy_verified:T.green,picking:T.yellow,packed:T.blue,dispatched:T.green,delivered:T.green,cancelled:T.red};

  return (<div>
    <PageHeader title="All Orders" badge={String(ORDERS.length)}/>
    <div style={{marginBottom:16}}><SearchInput value={search} onChange={setSearch} placeholder="Search orders..."/></div>
    <div style={{ display:"flex", gap:12, overflowX:"auto", paddingBottom:8 }}>
      {statusOrder.filter(s=>groups[s]).map(status => (
        <div key={status} style={{ minWidth:280, flexShrink:0 }}>
          <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:12, padding:"8px 12px", background:T.white, borderRadius:8, border:"1px solid "+T.gray200 }}>
            <span style={{ width:10, height:10, borderRadius:"50%", background:statusColor[status]||T.gray400 }} />
            <span style={{ fontSize:13, fontWeight:600, color:T.gray900, textTransform:"capitalize" }}>{status.replace(/_/g," ")}</span>
            <span style={{ fontSize:11, color:T.gray400, marginLeft:"auto" }}>{groups[status].length}</span>
          </div>
          <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
            {groups[status].map(o => (
              <div key={o.order_id} style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:8, padding:14, transition:"box-shadow .2s" }}
                onMouseEnter={e=>e.currentTarget.style.boxShadow="0 2px 12px rgba(0,0,0,.06)"}
                onMouseLeave={e=>e.currentTarget.style.boxShadow="none"}>
                <div style={{ fontFamily:"monospace", fontSize:11, color:T.gray400, marginBottom:4 }}>{o.order_id}</div>
                <div style={{ fontSize:13, fontWeight:600, color:T.gray900, marginBottom:4 }}>{o.patient_name}</div>
                <div style={{ fontSize:12, color:T.gray500, marginBottom:6 }}>{o.items.length} items · {o.pharmacy_node}</div>
                <div style={{ fontSize:15, fontWeight:700, color:T.blue }}>€{o.total_price.toFixed(2)}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>);
}