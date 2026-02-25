import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { StockDot, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Search as SI2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
export default function PharmacyInventory() {
  const { token, apiBase } = useAuth();
  const [search,setSearch]=useState("");
  const [medicines, setMedicines] = useState([]);
  useEffect(() => {
    if (!token) return;
    const load = async () => {
      try {
        const res = await fetch(`${apiBase}/medicines/?limit=500`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data = await res.json();
        setMedicines(Array.isArray(data) ? data : []);
      } catch (_) {}
    };
    load();
  }, [token, apiBase]);
  const fd=search?medicines.filter(m=>m.name.toLowerCase().includes(search.toLowerCase())):medicines;
  return (<div><PageHeader title="Pharmacy Inventory" subtitle="PH-001" actions={<Btn variant="secondary" size="sm"><SI2 size={14}/>Scan</Btn>}/>
  <div style={{marginBottom:16}}><SearchInput value={search} onChange={setSearch} placeholder="Search..."/></div>
  <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:10}}>
    {fd.slice(0,50).map(m=>(
      <div key={m.id} style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:8,padding:14}}>
        <div style={{fontSize:13,fontWeight:600,color:T.gray900,marginBottom:6,lineHeight:1.3}}>{m.name}</div>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div style={{display:"flex",alignItems:"center",gap:4}}><StockDot level={m.stock}/><span style={{fontWeight:700,color:T.gray900}}>{m.stock}</span></div>
          <span style={{fontSize:13,fontWeight:600,color:T.blue}}>₹ {Number(m.price || 0).toFixed(2)}</span>
        </div>
      </div>
    ))}
  </div></div>);
}