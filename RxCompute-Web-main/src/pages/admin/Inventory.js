import React, { useState, useMemo } from 'react';
import T from '../../utils/tokens';
import { StatusPill, StatCard, AgentBadge, StockDot, Toggle, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Grid3X3, Download, Shield, Package } from 'lucide-react';
import { MEDICINES } from '../../data/mockData';

export default function AdminInventory() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [view, setView] = useState("cards");
  const filtered = useMemo(() => {
    let d = MEDICINES;
    if (search) d = d.filter(m => m.name.toLowerCase().includes(search.toLowerCase()));
    if (filter === "in") d = d.filter(m => m.stock > 30);
    if (filter === "low") d = d.filter(m => m.stock > 0 && m.stock <= 30);
    if (filter === "out") d = d.filter(m => m.stock === 0);
    if (filter === "rx") d = d.filter(m => m.rx);
    return d;
  }, [search, filter]);

  return (<div>
    <PageHeader title="Medicine Inventory" badge="52 products" actions={<><Btn variant="secondary" size="sm" onClick={() => setView(view==="cards"?"heatmap":"cards")}><Grid3X3 size={14} />{view==="cards"?"Heatmap":"Cards"}</Btn><Btn variant="secondary" size="sm"><Download size={14} />Export</Btn></>} />
    <div style={{ display:"flex", gap:12, marginBottom:16, flexWrap:"wrap", alignItems:"center" }}>
      <SearchInput value={search} onChange={setSearch} placeholder="Search medicines..." />
      {["all","in","low","out","rx"].map(f => <button key={f} onClick={() => setFilter(f)} style={{ padding:"7px 14px", borderRadius:8, border:"1px solid "+(filter===f?T.blue:T.gray200), background:filter===f?T.blue+"08":T.white, color:filter===f?T.blue:T.gray600, fontSize:12, fontWeight:500, cursor:"pointer" }}>{f==="all"?"All":f==="in"?"In Stock":f==="low"?"Low":f==="out"?"Out":"Rx"}</button>)}
    </div>

    {view==="heatmap" ? (
      <div style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:12, padding:24 }}>
        <div style={{ display:"flex", gap:16, marginBottom:20 }}>{[["Healthy (>50)",T.green],["Low (20-50)",T.yellow],["Critical (<20)",T.red],["Out (0)",T.gray900]].map(([l,c])=><div key={l} style={{display:"flex",alignItems:"center",gap:6,fontSize:11,color:T.gray600}}><span style={{width:14,height:14,borderRadius:3,background:c}}/>{l}</div>)}</div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(8,1fr)", gap:8 }}>
          {MEDICINES.map(m => { const c=m.stock>50?T.green:m.stock>20?T.yellow:m.stock>0?T.red:T.gray900; return <div key={m.id} title={m.name+"\nStock: "+m.stock} style={{ height:64, borderRadius:8, background:c, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", cursor:"pointer", transition:"transform .15s", color:T.white, fontWeight:700, padding:4, textAlign:"center" }} onMouseEnter={e=>e.currentTarget.style.transform="scale(1.1)"} onMouseLeave={e=>e.currentTarget.style.transform="scale(1)"}><span style={{fontSize:16}}>{m.stock}</span><span style={{fontSize:8,opacity:.8}}>{m.name.split(" ")[0]}</span></div>; })}
        </div>
      </div>
    ) : (
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(240px, 1fr))", gap:12 }}>
        {filtered.map(m => (
          <div key={m.id} style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:10, padding:16, borderTop:"3px solid "+(m.stock>50?T.green:m.stock>10?T.yellow:m.stock>0?T.red:T.gray900), transition:"box-shadow .2s" }}
            onMouseEnter={e=>e.currentTarget.style.boxShadow="0 4px 16px rgba(0,0,0,.06)"}
            onMouseLeave={e=>e.currentTarget.style.boxShadow="none"}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:8 }}>
              <div style={{ fontSize:14, fontWeight:600, color:T.gray900, lineHeight:1.3 }}>{m.name}</div>
              {m.rx && <span style={{ background:T.orange+"15", color:T.orange, padding:"2px 6px", borderRadius:4, fontSize:9, fontWeight:700, whiteSpace:"nowrap" }}>Rx</span>}
            </div>
            <div style={{ fontSize:11, color:T.gray400, fontFamily:"monospace", marginBottom:12 }}>PZN: {m.pzn}</div>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
              <div style={{ display:"flex", alignItems:"center", gap:4 }}><StockDot level={m.stock} /><span style={{ fontSize:20, fontWeight:700, color:T.gray900 }}>{m.stock}</span><span style={{ fontSize:11, color:T.gray400 }}>units</span></div>
              <span style={{ fontSize:16, fontWeight:700, color:T.blue }}>€{m.price.toFixed(2)}</span>
            </div>
            <div style={{ height:4, borderRadius:2, background:T.gray100, overflow:"hidden" }}><div style={{ height:"100%", borderRadius:2, width:Math.min(100,(m.stock/300)*100)+"%", background:m.stock>50?T.green:m.stock>10?T.yellow:T.red }} /></div>
            <div style={{ display:"flex", justifyContent:"space-between", marginTop:8 }}>
              <span style={{ fontSize:11, color:T.gray400 }}>{m.package_size}</span>
              <span style={{ fontSize:11, color:T.gray400 }}>{m.category}</span>
            </div>
          </div>
        ))}
      </div>
    )}
  </div>);
}