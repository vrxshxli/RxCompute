import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { StockDot, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Search as SI2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
export default function PharmacyInventory() {
  const { token, apiBase } = useAuth();
  const [search,setSearch]=useState("");
  const [transfers, setTransfers] = useState([]);
  useEffect(() => {
    if (!token) return;
    const load = async () => {
      try {
        const res = await fetch(`${apiBase}/warehouse/transfers?direction=warehouse_to_pharmacy`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data = await res.json();
        setTransfers(Array.isArray(data) ? data : []);
      } catch (_) {}
    };
    load();
  }, [token, apiBase]);
  const medicines = useMemo(() => {
    const dispatched = transfers.filter((x) => x.status === "dispatched");
    const map = {};
    dispatched.forEach((x) => {
      const key = `${x.pharmacy_store_id || "na"}-${x.medicine_id}`;
      if (!map[key]) {
        map[key] = {
          id: key,
          name: x.medicine_name,
          stock: 0,
          price: 0,
          pharmacy: x.pharmacy_store_name || "-",
        };
      }
      map[key].stock += Number(x.quantity || 0);
    });
    return Object.values(map);
  }, [transfers]);
  const fd=search?medicines.filter(m=>m.name.toLowerCase().includes(search.toLowerCase())):medicines;
  return (<div><PageHeader title="Pharmacy Inventory" subtitle="Received from warehouse dispatches" actions={<Btn variant="secondary" size="sm"><SI2 size={14}/>Scan</Btn>}/>
  <div style={{marginBottom:16}}><SearchInput value={search} onChange={setSearch} placeholder="Search..."/></div>
  <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:10}}>
    {fd.slice(0,50).map(m=>(
      <div key={m.id} style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:8,padding:14}}>
        <div style={{fontSize:13,fontWeight:600,color:T.gray900,marginBottom:6,lineHeight:1.3}}>{m.name}</div>
        <div style={{fontSize:11,color:T.gray500,marginBottom:4}}>{m.pharmacy}</div>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div style={{display:"flex",alignItems:"center",gap:4}}><StockDot level={m.stock}/><span style={{fontWeight:700,color:T.gray900}}>{m.stock}</span></div>
          <span style={{fontSize:12,fontWeight:600,color:T.blue}}>From Warehouse</span>
        </div>
      </div>
    ))}
  </div></div>);
}