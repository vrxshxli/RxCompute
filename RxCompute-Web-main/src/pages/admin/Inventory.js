import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { StockDot, SearchInput, Btn, PageHeader } from '../../components/shared';
import { Grid3X3, Download } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function AdminInventory() {
  const { token, apiBase } = useAuth();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [view, setView] = useState("cards");
  const [medicines, setMedicines] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [showSendWarehouse, setShowSendWarehouse] = useState(false);
  const [saving, setSaving] = useState(false);
  const [sendingWarehouse, setSendingWarehouse] = useState(false);
  const [addError, setAddError] = useState("");
  const [warehouseMsg, setWarehouseMsg] = useState("");
  const [editId, setEditId] = useState(null);
  const [editForm, setEditForm] = useState({ name: "", pzn: "", price: "", stock: "", package: "", description: "", rx_required: false });
  const [form, setForm] = useState({
    name: "",
    pzn: "",
    price: "",
    package: "",
    stock: "50",
    rx_required: false,
    description: "",
  });
  const [warehouseForm, setWarehouseForm] = useState({
    medicine_id: "",
    quantity: "10",
    note: "",
  });

  const loadMedicines = async () => {
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const res = await fetch(`${apiBase}/medicines/?limit=500`, { headers });
      if (!res.ok) return;
      const data = await res.json();
      const mapped = (Array.isArray(data) ? data : []).map((m) => ({
        id: m.id,
        name: m.name,
        pzn: m.pzn,
        price: m.price,
        package_size: m.package || "-",
        stock: m.stock || 0,
        rx: !!m.rx_required,
        category: m.description ? "General" : "-",
      }));
      setMedicines(mapped);
    } catch (_) {}
  };

  useEffect(() => {
    loadMedicines();
  }, [token, apiBase]);

  const createMedicine = async () => {
    if (!form.name.trim() || !form.pzn.trim() || !form.price.trim()) {
      setAddError("Name, PZN and price are required");
      return;
    }
    setSaving(true);
    setAddError("");
    try {
      const headers = {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      };
      const res = await fetch(`${apiBase}/medicines/`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          name: form.name.trim(),
          pzn: form.pzn.trim(),
          price: Number(form.price),
          package: form.package.trim() || null,
          stock: Number(form.stock || 0),
          rx_required: !!form.rx_required,
          description: form.description.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setAddError(data?.detail || "Unable to add medicine");
        setSaving(false);
        return;
      }
      setForm({
        name: "",
        pzn: "",
        price: "",
        package: "",
        stock: "50",
        rx_required: false,
        description: "",
      });
      setShowAdd(false);
      await loadMedicines();
    } catch (_) {
      setAddError("Network error while adding medicine");
    } finally {
      setSaving(false);
    }
  };

  const sendToWarehouse = async () => {
    if (!token) return;
    if (!warehouseForm.medicine_id || Number(warehouseForm.quantity) <= 0) {
      setWarehouseMsg("Choose medicine and valid quantity");
      return;
    }
    setSendingWarehouse(true);
    setWarehouseMsg("");
    try {
      const res = await fetch(`${apiBase}/warehouse/transfers/admin-to-warehouse`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          medicine_id: Number(warehouseForm.medicine_id),
          quantity: Number(warehouseForm.quantity),
          note: warehouseForm.note.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setWarehouseMsg(data?.detail || "Unable to send medicine to warehouse");
      } else {
        setWarehouseMsg("Sent to warehouse");
        setWarehouseForm({ medicine_id: "", quantity: "10", note: "" });
        await loadMedicines();
      }
    } catch (_) {
      setWarehouseMsg("Network error while sending");
    } finally {
      setSendingWarehouse(false);
    }
  };

  const openEdit = (m) => {
    setEditId(m.id);
    setEditForm({
      name: m.name || "",
      pzn: m.pzn || "",
      price: String(m.price ?? ""),
      stock: String(m.stock ?? 0),
      package: m.package_size === "-" ? "" : (m.package_size || ""),
      description: m.category === "-" ? "" : (m.category || ""),
      rx_required: !!m.rx,
    });
  };

  const saveEdit = async () => {
    if (!token || !editId) return;
    setAddError("");
    try {
      const res = await fetch(`${apiBase}/medicines/${editId}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: editForm.name.trim() || null,
          price: editForm.price === "" ? null : Number(editForm.price),
          stock: editForm.stock === "" ? null : Number(editForm.stock),
          package: editForm.package.trim() || null,
          description: editForm.description.trim() || null,
          rx_required: !!editForm.rx_required,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setAddError(data?.detail || "Unable to update medicine");
        return;
      }
      setEditId(null);
      await loadMedicines();
    } catch (_) {
      setAddError("Network error while updating medicine");
    }
  };

  const deleteMedicine = async (id) => {
    if (!token) return;
    if (!window.confirm("Delete this medicine?")) return;
    setAddError("");
    try {
      const res = await fetch(`${apiBase}/medicines/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setAddError(data?.detail || "Unable to delete medicine");
        return;
      }
      await loadMedicines();
    } catch (_) {
      setAddError("Network error while deleting medicine");
    }
  };

  const filtered = useMemo(() => {
    let d = medicines;
    if (search) d = d.filter(m => m.name.toLowerCase().includes(search.toLowerCase()));
    if (filter === "in") d = d.filter(m => m.stock > 30);
    if (filter === "low") d = d.filter(m => m.stock > 0 && m.stock <= 30);
    if (filter === "out") d = d.filter(m => m.stock === 0);
    if (filter === "rx") d = d.filter(m => m.rx);
    return d;
  }, [medicines, search, filter]);

  return (<div>
    <PageHeader title="Medicine Inventory" badge={`${medicines.length} products`} actions={<><Btn variant="secondary" size="sm" onClick={() => setShowAdd(!showAdd)}>{showAdd ? "Close Add" : "Add Medicine"}</Btn><Btn variant="secondary" size="sm" onClick={() => setShowSendWarehouse(!showSendWarehouse)}>{showSendWarehouse ? "Close Transfer" : "Send to Warehouse"}</Btn><Btn variant="secondary" size="sm" onClick={() => setView(view==="cards"?"heatmap":"cards")}><Grid3X3 size={14} />{view==="cards"?"Heatmap":"Cards"}</Btn><Btn variant="secondary" size="sm"><Download size={14} />Export</Btn></>} />
    {showAdd && (
      <div style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:12, padding:14, marginBottom:12 }}>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(4, minmax(120px, 1fr))", gap:10 }}>
          <input value={form.name} onChange={(e)=>setForm({...form, name:e.target.value})} placeholder="Medicine name" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }} />
          <input value={form.pzn} onChange={(e)=>setForm({...form, pzn:e.target.value})} placeholder="PZN" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }} />
          <input value={form.price} onChange={(e)=>setForm({...form, price:e.target.value})} placeholder="Price (₹)" type="number" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }} />
          <input value={form.stock} onChange={(e)=>setForm({...form, stock:e.target.value})} placeholder="Stock" type="number" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }} />
          <input value={form.package} onChange={(e)=>setForm({...form, package:e.target.value})} placeholder="Package size" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }} />
          <input value={form.description} onChange={(e)=>setForm({...form, description:e.target.value})} placeholder="Description" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8, gridColumn:"span 2" }} />
          <label style={{ display:"flex", alignItems:"center", gap:8, fontSize:12, color:T.gray700 }}>
            <input type="checkbox" checked={form.rx_required} onChange={(e)=>setForm({...form, rx_required:e.target.checked})} />
            Prescription required
          </label>
          <Btn variant="primary" size="sm" onClick={createMedicine} disabled={saving}>{saving ? "Saving..." : "Save"}</Btn>
        </div>
        {addError ? <div style={{ marginTop:8, color:T.red, fontSize:12 }}>{addError}</div> : null}
      </div>
    )}
    {showSendWarehouse && (
      <div style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:12, padding:14, marginBottom:12 }}>
        <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr 2fr auto", gap:10 }}>
          <select value={warehouseForm.medicine_id} onChange={(e)=>setWarehouseForm({...warehouseForm, medicine_id:e.target.value})} style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }}>
            <option value="">Select medicine</option>
            {medicines.map((m)=><option key={m.id} value={m.id}>{m.name} (admin stock: {m.stock})</option>)}
          </select>
          <input value={warehouseForm.quantity} onChange={(e)=>setWarehouseForm({...warehouseForm, quantity:e.target.value})} placeholder="Qty" type="number" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }} />
          <input value={warehouseForm.note} onChange={(e)=>setWarehouseForm({...warehouseForm, note:e.target.value})} placeholder="Note (optional)" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }} />
          <Btn variant="primary" size="sm" onClick={sendToWarehouse} disabled={sendingWarehouse}>{sendingWarehouse ? "Sending..." : "Send"}</Btn>
        </div>
        {warehouseMsg ? <div style={{ marginTop:8, color:warehouseMsg==="Sent to warehouse"?T.green:T.red, fontSize:12 }}>{warehouseMsg}</div> : null}
      </div>
    )}
    {editId ? (
      <div style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:12, padding:14, marginBottom:12 }}>
        <div style={{ fontSize:13, fontWeight:600, color:T.gray900, marginBottom:8 }}>Edit Medicine</div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(4, minmax(120px, 1fr))", gap:10 }}>
          <input value={editForm.name} onChange={(e)=>setEditForm({...editForm, name:e.target.value})} placeholder="Medicine name" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }} />
          <input value={editForm.pzn} disabled placeholder="PZN" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8, background:T.gray50 }} />
          <input value={editForm.price} onChange={(e)=>setEditForm({...editForm, price:e.target.value})} placeholder="Price" type="number" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }} />
          <input value={editForm.stock} onChange={(e)=>setEditForm({...editForm, stock:e.target.value})} placeholder="Stock" type="number" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }} />
          <input value={editForm.package} onChange={(e)=>setEditForm({...editForm, package:e.target.value})} placeholder="Package size" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8 }} />
          <input value={editForm.description} onChange={(e)=>setEditForm({...editForm, description:e.target.value})} placeholder="Description" style={{ padding:"10px", border:`1px solid ${T.gray200}`, borderRadius:8, gridColumn:"span 2" }} />
          <label style={{ display:"flex", alignItems:"center", gap:8, fontSize:12, color:T.gray700 }}>
            <input type="checkbox" checked={editForm.rx_required} onChange={(e)=>setEditForm({...editForm, rx_required:e.target.checked})} />
            Prescription required
          </label>
          <div style={{ display:"flex", gap:8 }}>
            <Btn variant="primary" size="sm" onClick={saveEdit}>Save</Btn>
            <Btn variant="secondary" size="sm" onClick={()=>setEditId(null)}>Cancel</Btn>
          </div>
        </div>
      </div>
    ) : null}
    <div style={{ display:"flex", gap:12, marginBottom:16, flexWrap:"wrap", alignItems:"center" }}>
      <SearchInput value={search} onChange={setSearch} placeholder="Search medicines..." />
      {["all","in","low","out","rx"].map(f => <button key={f} onClick={() => setFilter(f)} style={{ padding:"7px 14px", borderRadius:8, border:"1px solid "+(filter===f?T.blue:T.gray200), background:filter===f?T.blue+"08":T.white, color:filter===f?T.blue:T.gray600, fontSize:12, fontWeight:500, cursor:"pointer" }}>{f==="all"?"All":f==="in"?"In Stock":f==="low"?"Low":f==="out"?"Out":"Rx"}</button>)}
    </div>

    {view==="heatmap" ? (
      <div style={{ background:T.white, border:"1px solid "+T.gray200, borderRadius:12, padding:24 }}>
        <div style={{ display:"flex", gap:16, marginBottom:20 }}>{[["Healthy (>50)",T.green],["Low (20-50)",T.yellow],["Critical (<20)",T.red],["Out (0)",T.gray900]].map(([l,c])=><div key={l} style={{display:"flex",alignItems:"center",gap:6,fontSize:11,color:T.gray600}}><span style={{width:14,height:14,borderRadius:3,background:c}}/>{l}</div>)}</div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(8,1fr)", gap:8 }}>
          {medicines.map(m => { const c=m.stock>50?T.green:m.stock>20?T.yellow:m.stock>0?T.red:T.gray900; return <div key={m.id} title={m.name+"\nStock: "+m.stock} style={{ height:64, borderRadius:8, background:c, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", cursor:"pointer", transition:"transform .15s", color:T.white, fontWeight:700, padding:4, textAlign:"center" }} onMouseEnter={e=>e.currentTarget.style.transform="scale(1.1)"} onMouseLeave={e=>e.currentTarget.style.transform="scale(1)"}><span style={{fontSize:16}}>{m.stock}</span><span style={{fontSize:8,opacity:.8}}>{m.name.split(" ")[0]}</span></div>; })}
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
              <span style={{ fontSize:16, fontWeight:700, color:T.blue }}>₹{m.price.toFixed(2)}</span>
            </div>
            <div style={{ height:4, borderRadius:2, background:T.gray100, overflow:"hidden" }}><div style={{ height:"100%", borderRadius:2, width:Math.min(100,(m.stock/300)*100)+"%", background:m.stock>50?T.green:m.stock>10?T.yellow:T.red }} /></div>
            <div style={{ display:"flex", justifyContent:"space-between", marginTop:8 }}>
              <span style={{ fontSize:11, color:T.gray400 }}>{m.package_size}</span>
              <span style={{ fontSize:11, color:T.gray400 }}>{m.category}</span>
            </div>
            <div style={{ display:"flex", gap:8, marginTop:10 }}>
              <Btn variant="secondary" size="sm" onClick={() => openEdit(m)}>Edit</Btn>
              <Btn variant="secondary" size="sm" style={{ color:T.red }} onClick={() => deleteMedicine(m.id)}>Delete</Btn>
            </div>
          </div>
        ))}
      </div>
    )}
  </div>);
}