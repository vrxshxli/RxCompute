import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { StockDot, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Search as SI2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
export default function PharmacyInventory() {
  const { token, apiBase } = useAuth();
  const [search,setSearch]=useState("");
  const [stocks, setStocks] = useState([]);
  const [requestForm, setRequestForm] = useState({ medicine_id: "", quantity: "10", note: "" });
  const [requestMsg, setRequestMsg] = useState("");
  useEffect(() => {
    if (!token) return;
    const load = async () => {
      try {
        const res = await fetch(`${apiBase}/warehouse/pharmacy-stock`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data = await res.json();
        setStocks(Array.isArray(data) ? data : []);
      } catch (_) {}
    };
    load();
    const timer = window.setInterval(load, 10000);
    return () => window.clearInterval(timer);
  }, [token, apiBase]);
  const medicines = useMemo(() => {
    return stocks.map((x) => ({
      id: `${x.pharmacy_store_id}-${x.medicine_id}`,
      medicine_id: x.medicine_id,
      name: x.medicine_name,
      stock: Number(x.quantity || 0),
      price: Number(x.price || 0),
      pharmacy: x.pharmacy_store_name || "-",
    }));
  }, [stocks]);
  const fd=search?medicines.filter(m=>m.name.toLowerCase().includes(search.toLowerCase())):medicines;
  const requestFromWarehouse = async () => {
    if (!token || !requestForm.medicine_id || Number(requestForm.quantity) <= 0) {
      setRequestMsg("Choose medicine and valid quantity");
      return;
    }
    setRequestMsg("");
    try {
      const res = await fetch(`${apiBase}/warehouse/transfers/pharmacy-request`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          medicine_id: Number(requestForm.medicine_id),
          quantity: Number(requestForm.quantity),
          note: requestForm.note.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setRequestMsg(data?.detail || "Unable to request medicine");
      } else {
        setRequestMsg("Request sent to warehouse");
        setRequestForm({ medicine_id: "", quantity: "10", note: "" });
      }
    } catch (_) {
      setRequestMsg("Network error while sending request");
    }
  };
  return (<div><PageHeader title="Pharmacy Inventory" subtitle="Your pharmacy stock" actions={<Btn variant="secondary" size="sm"><SI2 size={14}/>Scan</Btn>}/>
  <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:8,padding:12,marginBottom:12}}>
    <div style={{fontSize:12,color:T.gray700,fontWeight:600,marginBottom:8}}>Request medicine from warehouse</div>
    <div style={{display:"grid",gridTemplateColumns:"2fr 1fr 2fr auto",gap:8}}>
      <select value={requestForm.medicine_id} onChange={(e)=>setRequestForm({...requestForm, medicine_id:e.target.value})} style={{padding:"9px",border:`1px solid ${T.gray200}`,borderRadius:8}}>
        <option value="">Select medicine</option>
        {medicines.map((m)=><option key={m.id} value={m.medicine_id}>{m.name} (current: {m.stock})</option>)}
      </select>
      <input type="number" value={requestForm.quantity} onChange={(e)=>setRequestForm({...requestForm, quantity:e.target.value})} placeholder="Qty" style={{padding:"9px",border:`1px solid ${T.gray200}`,borderRadius:8}} />
      <input value={requestForm.note} onChange={(e)=>setRequestForm({...requestForm, note:e.target.value})} placeholder="Reason / note" style={{padding:"9px",border:`1px solid ${T.gray200}`,borderRadius:8}} />
      <Btn variant="primary" size="sm" onClick={requestFromWarehouse}>Request</Btn>
    </div>
    {requestMsg ? <div style={{marginTop:8,fontSize:12,color:requestMsg === "Request sent to warehouse" ? T.green : T.red}}>{requestMsg}</div> : null}
  </div>
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