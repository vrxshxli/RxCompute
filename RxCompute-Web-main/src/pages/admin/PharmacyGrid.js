import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { Btn, PageHeader, StatCard } from '../../components/shared';
import { Building2, MapPin } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
export default function AdminPharmacyGrid() {
  const { token, apiBase } = useAuth();
  const [stores, setStores] = useState([]);
  const [pharmacyUsers, setPharmacyUsers] = useState([]);
  const [savingId, setSavingId] = useState(null);
  const [error, setError] = useState("");
  const [newStore, setNewStore] = useState({
    node_id: "",
    name: "",
    location: "",
    load: "0",
    stock_count: "0",
    active: true,
  });

  const loadStores = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${apiBase}/pharmacy-stores/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setStores(Array.isArray(data) ? data : []);
      const usersRes = await fetch(`${apiBase}/users/?role=pharmacy_store`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (usersRes.ok) {
        const usersData = await usersRes.json();
        setPharmacyUsers(Array.isArray(usersData) ? usersData : []);
      }
    } catch (_) {}
  };
  useEffect(() => {
    loadStores();
  }, [token, apiBase]);

  const uniqueLocations = useMemo(
    () => new Set(stores.map((s) => (s.location || "").trim().toLowerCase()).filter(Boolean)).size,
    [stores],
  );
  const virtualGrid = useMemo(
    () =>
      pharmacyUsers.map((u) => {
        const expectedNode = `PH-U${String(u.id).padStart(3, "0")}`;
        const mappedStore = stores.find((s) => s.node_id === expectedNode);
        return {
          userId: u.id,
          userName: (u.name || "").trim() || `Pharmacy User ${u.id}`,
          userEmail: u.email || "-",
          expectedNode,
          mappedStore,
        };
      }),
    [pharmacyUsers, stores],
  );

  const saveStore = async (store) => {
    if (!token) return;
    setSavingId(store.id);
    setError("");
    try {
      const res = await fetch(`${apiBase}/pharmacy-stores/${store.id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: store.name,
          location: store.location,
          active: !!store.active,
          load: Number(store.load || 0),
          stock_count: Number(store.stock_count || 0),
        }),
      });
      const data = await res.json();
      if (!res.ok) setError(data?.detail || "Save failed");
      await loadStores();
    } catch (_) {
      setError("Network error while saving store");
    } finally {
      setSavingId(null);
    }
  };

  const createStore = async () => {
    if (!token) return;
    setError("");
    try {
      const res = await fetch(`${apiBase}/pharmacy-stores/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          node_id: newStore.node_id.trim(),
          name: newStore.name.trim(),
          location: newStore.location.trim(),
          active: !!newStore.active,
          load: Number(newStore.load || 0),
          stock_count: Number(newStore.stock_count || 0),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.detail || "Create failed");
        return;
      }
      setNewStore({ node_id: "", name: "", location: "", load: "0", stock_count: "0", active: true });
      await loadStores();
    } catch (_) {
      setError("Network error while creating store");
    }
  };

  return (<div><PageHeader title="Virtual Pharmacy Grid" subtitle="Node health & routing with saved locations"/>
  <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit, minmax(180px, 1fr))",gap:12,marginBottom:16}}>
    <StatCard icon={Building2} label="Pharmacy Stores" value={String(stores.length)} color={T.blue}/>
    <StatCard icon={MapPin} label="Locations" value={String(uniqueLocations)} color={T.orange}/>
    <StatCard icon={Building2} label="Pharmacy Dashboard Users" value={String(pharmacyUsers.length)} color={T.green}/>
  </div>
  <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:14,marginBottom:16}}>
    <div style={{fontSize:13,fontWeight:600,color:T.gray900,marginBottom:8}}>Virtual Pharmacy Grid (from pharmacy dashboard users)</div>
    {virtualGrid.length===0 ? <div style={{fontSize:12,color:T.gray500}}>No pharmacy dashboard users found.</div> : virtualGrid.map((v)=>(
      <div key={v.userId} style={{display:"grid",gridTemplateColumns:"1.4fr 1fr 1fr",gap:8,padding:"7px 0",borderBottom:"1px solid "+T.gray100,fontSize:12}}>
        <div>{v.userName} <span style={{color:T.gray400}}>({v.userEmail})</span></div>
        <div style={{fontFamily:"monospace"}}>{v.expectedNode}</div>
        <div style={{color:v.mappedStore?T.green:T.red}}>{v.mappedStore ? "Mapped" : "Not mapped yet"}</div>
      </div>
    ))}
  </div>
  <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:14,marginBottom:16}}>
    <div style={{fontSize:13,fontWeight:600,color:T.gray900,marginBottom:10}}>Add Pharmacy Store</div>
    <div style={{display:"grid",gridTemplateColumns:"repeat(6, minmax(110px,1fr))",gap:8}}>
      <input value={newStore.node_id} onChange={(e)=>setNewStore({...newStore, node_id:e.target.value})} placeholder="Node ID" style={{padding:"8px",border:`1px solid ${T.gray200}`,borderRadius:8}} />
      <input value={newStore.name} onChange={(e)=>setNewStore({...newStore, name:e.target.value})} placeholder="Store name" style={{padding:"8px",border:`1px solid ${T.gray200}`,borderRadius:8}} />
      <input value={newStore.location} onChange={(e)=>setNewStore({...newStore, location:e.target.value})} placeholder="Location" style={{padding:"8px",border:`1px solid ${T.gray200}`,borderRadius:8}} />
      <input type="number" value={newStore.load} onChange={(e)=>setNewStore({...newStore, load:e.target.value})} placeholder="Load %" style={{padding:"8px",border:`1px solid ${T.gray200}`,borderRadius:8}} />
      <input type="number" value={newStore.stock_count} onChange={(e)=>setNewStore({...newStore, stock_count:e.target.value})} placeholder="Stock count" style={{padding:"8px",border:`1px solid ${T.gray200}`,borderRadius:8}} />
      <Btn variant="primary" size="sm" onClick={createStore}>Save</Btn>
    </div>
    {error ? <div style={{marginTop:8,fontSize:12,color:T.red}}>{error}</div> : null}
  </div>
  <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(260px,1fr))",gap:16,marginBottom:24}}>
    {stores.map((n, idx)=><div key={n.id} style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:24}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16}}><span style={{fontFamily:"monospace",fontSize:14,fontWeight:600,color:T.gray900}}>{n.node_id}</span><div style={{display:"flex",alignItems:"center",gap:6}}><span style={{width:8,height:8,borderRadius:"50%",background:n.active?T.green:T.red}}/><span style={{fontSize:12,color:n.active?T.green:T.red,fontWeight:500}}>{n.active?"Active":"Offline"}</span></div></div>
      <input value={n.name} onChange={(e)=>setStores(stores.map((s,i)=> i===idx ? {...s, name:e.target.value} : s))} style={{width:"100%",marginBottom:8,padding:"8px",border:`1px solid ${T.gray200}`,borderRadius:8,fontSize:13}} />
      <input value={n.location} onChange={(e)=>setStores(stores.map((s,i)=> i===idx ? {...s, location:e.target.value} : s))} style={{width:"100%",marginBottom:12,padding:"8px",border:`1px solid ${T.gray200}`,borderRadius:8,fontSize:12,color:T.gray600}} />
      <div style={{marginBottom:12}}><div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}><span style={{fontSize:11,color:T.gray500}}>Load</span><span style={{fontSize:11,fontWeight:600}}>{n.load}%</span></div><div style={{height:8,borderRadius:4,background:T.gray100,overflow:"hidden"}}><div style={{height:"100%",borderRadius:4,width:n.load+"%",background:n.load>80?T.red:n.load>50?T.yellow:T.green}}/></div></div>
      <div style={{display:"flex",justifyContent:"space-between",gap:8,alignItems:"center"}}>
        <div style={{fontSize:12,color:T.gray500}}>{n.stock_count} in stock</div>
        <Btn variant="secondary" size="sm" onClick={() => saveStore(n)} disabled={savingId===n.id}>{savingId===n.id ? "Saving..." : "Save"}</Btn>
      </div>
    </div>)}
  </div></div>);
}