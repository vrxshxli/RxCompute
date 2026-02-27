import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { Btn, PageHeader } from '../../components/shared';
import { Play, PlusCircle, Upload, Download } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function WarehouseFulfillment() {
  const { token, apiBase } = useAuth();
  const [stock, setStock] = useState([]);
  const [inboundTransfers, setInboundTransfers] = useState([]);
  const [outboundTransfers, setOutboundTransfers] = useState([]);
  const [pharmacies, setPharmacies] = useState([]);
  const [savingTransferId, setSavingTransferId] = useState(null);
  const [showSendPharmacy, setShowSendPharmacy] = useState(false);
  const [showSendAdmin, setShowSendAdmin] = useState(false);
  const [showSingleAdd, setShowSingleAdd] = useState(false);
  const [showBulkAdd, setShowBulkAdd] = useState(false);
  const [showCsvAdd, setShowCsvAdd] = useState(false);
  const [sendMsg, setSendMsg] = useState("");
  const [sendAdminMsg, setSendAdminMsg] = useState("");
  const [singleMsg, setSingleMsg] = useState("");
  const [bulkMsg, setBulkMsg] = useState("");
  const [csvMsg, setCsvMsg] = useState("");
  const [tableMsg, setTableMsg] = useState("");
  const [editingMedicineId, setEditingMedicineId] = useState(null);
  const [editMedicineForm, setEditMedicineForm] = useState({ name: "", pzn: "", price: "", warehouse_stock: "" });
  const [sendForm, setSendForm] = useState({
    medicine_id: "",
    quantity: "10",
    pharmacy_store_id: "",
    note: "",
  });
  const [sendAdminForm, setSendAdminForm] = useState({
    medicine_id: "",
    quantity: "10",
    note: "",
  });
  const [singleForm, setSingleForm] = useState({
    name: "",
    pzn: "",
    price: "",
    package: "",
    initial_stock: "50",
    rx_required: false,
    description: "",
    image_url: "",
  });
  const [bulkText, setBulkText] = useState("");
  const [csvFile, setCsvFile] = useState(null);

  const load = async () => {
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const [stockRes, inboundRes, outboundRes, storesRes] = await Promise.all([
        fetch(`${apiBase}/warehouse/stock`, { headers }),
        fetch(`${apiBase}/warehouse/transfers?direction=admin_to_warehouse`, { headers }),
        fetch(`${apiBase}/warehouse/transfers?direction=warehouse_to_pharmacy`, { headers }),
        fetch(`${apiBase}/warehouse/pharmacy-options`, { headers }),
      ]);
      if (stockRes.ok) {
        const data = await stockRes.json();
        setStock(Array.isArray(data) ? data : []);
      }
      if (inboundRes.ok) {
        const data = await inboundRes.json();
        setInboundTransfers(Array.isArray(data) ? data : []);
      }
      if (outboundRes.ok) {
        const data = await outboundRes.json();
        setOutboundTransfers(Array.isArray(data) ? data : []);
      }
      if (storesRes.ok) {
        const data = await storesRes.json();
        setPharmacies(Array.isArray(data) ? data : []);
      }
    } catch (_) {}
  };

  useEffect(() => {
    load();
  }, [token, apiBase]);

  const updateTransferStatus = async (transferId, status) => {
    if (!token) return;
    setSavingTransferId(transferId);
    try {
      await fetch(`${apiBase}/warehouse/transfers/${transferId}/status`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
      });
      await load();
    } catch (_) {
    } finally {
      setSavingTransferId(null);
    }
  };

  const sendToPharmacy = async () => {
    if (!token || !sendForm.medicine_id || !sendForm.pharmacy_store_id || Number(sendForm.quantity) <= 0) {
      setSendMsg("Choose medicine, pharmacy and valid quantity");
      return;
    }
    setSendMsg("");
    try {
      const res = await fetch(`${apiBase}/warehouse/transfers/warehouse-to-pharmacy`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          medicine_id: Number(sendForm.medicine_id),
          quantity: Number(sendForm.quantity),
          pharmacy_store_id: Number(sendForm.pharmacy_store_id),
          note: sendForm.note.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setSendMsg(data?.detail || "Unable to create pharmacy transfer");
        return;
      }
      setSendMsg("Transfer created");
      setSendForm({ medicine_id: "", quantity: "10", pharmacy_store_id: "", note: "" });
      await load();
    } catch (_) {
      setSendMsg("Network error while creating transfer");
    }
  };

  const sendToAdmin = async () => {
    if (!token || !sendAdminForm.medicine_id || Number(sendAdminForm.quantity) <= 0) {
      setSendAdminMsg("Choose medicine and valid quantity");
      return;
    }
    setSendAdminMsg("");
    try {
      const res = await fetch(`${apiBase}/warehouse/transfers/warehouse-to-admin`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          medicine_id: Number(sendAdminForm.medicine_id),
          quantity: Number(sendAdminForm.quantity),
          note: sendAdminForm.note.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setSendAdminMsg(data?.detail || "Unable to send medicine to admin");
        return;
      }
      setSendAdminMsg("Sent to admin inventory");
      setSendAdminForm({ medicine_id: "", quantity: "10", note: "" });
      await load();
    } catch (_) {
      setSendAdminMsg("Network error while creating transfer");
    }
  };

  const addSingleMedicine = async () => {
    if (!token) return;
    if (!singleForm.name.trim() || !singleForm.pzn.trim() || !singleForm.price.trim()) {
      setSingleMsg("Name, PZN and price are required");
      return;
    }
    setSingleMsg("");
    try {
      const res = await fetch(`${apiBase}/warehouse/medicines`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: singleForm.name.trim(),
          pzn: singleForm.pzn.trim(),
          price: Number(singleForm.price),
          package: singleForm.package.trim() || null,
          initial_stock: Number(singleForm.initial_stock || 0),
          rx_required: !!singleForm.rx_required,
          description: singleForm.description.trim() || null,
          image_url: singleForm.image_url.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setSingleMsg(data?.detail || "Unable to add medicine");
        return;
      }
      setSingleMsg("Medicine added in warehouse");
      setSingleForm({
        name: "",
        pzn: "",
        price: "",
        package: "",
        initial_stock: "50",
        rx_required: false,
        description: "",
        image_url: "",
      });
      await load();
    } catch (_) {
      setSingleMsg("Network error while adding medicine");
    }
  };

  const parseBulkLines = () => {
    const lines = bulkText.split("\n").map((x) => x.trim()).filter(Boolean);
    const medicines = [];
    for (const line of lines) {
      const parts = line.split("|").map((x) => x.trim());
      if (parts.length < 5) continue;
      medicines.push({
        name: parts[0],
        pzn: parts[1],
        price: Number(parts[2]),
        package: parts[3] || null,
        initial_stock: Number(parts[4] || 0),
        rx_required: (parts[5] || "").toLowerCase() === "true",
        description: parts[6] || null,
        image_url: parts[7] || null,
      });
    }
    return medicines;
  };

  const uploadBulkMedicines = async () => {
    if (!token) return;
    const medicines = parseBulkLines();
    if (!medicines.length) {
      setBulkMsg("Invalid bulk format. Use template shown below");
      return;
    }
    setBulkMsg("");
    try {
      const res = await fetch(`${apiBase}/warehouse/medicines/bulk`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ medicines }),
      });
      const data = await res.json();
      if (!res.ok) {
        setBulkMsg(data?.detail || "Bulk upload failed");
        return;
      }
      setBulkMsg(`Bulk upload complete: ${data.processed} medicines`);
      setBulkText("");
      await load();
    } catch (_) {
      setBulkMsg("Network error while bulk upload");
    }
  };

  const uploadCsvMedicines = async () => {
    if (!token || !csvFile) {
      setCsvMsg("Please choose CSV file");
      return;
    }
    setCsvMsg("");
    try {
      const formData = new FormData();
      formData.append("file", csvFile);
      const res = await fetch(`${apiBase}/warehouse/medicines/import-csv`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        setCsvMsg(data?.detail || "CSV upload failed");
        return;
      }
      setCsvMsg(`CSV uploaded: processed ${data.processed}, skipped ${data.skipped}`);
      setCsvFile(null);
      await load();
    } catch (_) {
      setCsvMsg("Network error while CSV upload");
    }
  };

  const downloadCsvTemplate = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${apiBase}/warehouse/medicines/csv-template`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const text = await res.text();
      const blob = new Blob([text], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "warehouse_medicines_template.csv";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (_) {}
  };

  const startEditMedicine = (m) => {
    setEditingMedicineId(m.medicine_id);
    setEditMedicineForm({
      name: m.medicine_name || "",
      pzn: m.pzn || "",
      price: String(m.price ?? ""),
      warehouse_stock: String(m.quantity ?? 0),
    });
    setTableMsg("");
  };

  const saveEditMedicine = async () => {
    if (!token || !editingMedicineId) return;
    setTableMsg("");
    try {
      const res = await fetch(`${apiBase}/warehouse/medicines/${editingMedicineId}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: editMedicineForm.name.trim() || null,
          price: editMedicineForm.price === "" ? null : Number(editMedicineForm.price),
          warehouse_stock: editMedicineForm.warehouse_stock === "" ? null : Number(editMedicineForm.warehouse_stock),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setTableMsg(data?.detail || "Unable to update medicine");
        return;
      }
      setTableMsg("Medicine updated");
      setEditingMedicineId(null);
      await load();
    } catch (_) {
      setTableMsg("Network error while updating medicine");
    }
  };

  const deleteMedicine = async (medicineId) => {
    if (!token) return;
    if (!window.confirm("Delete this medicine from warehouse stock?")) return;
    setTableMsg("");
    try {
      const res = await fetch(`${apiBase}/warehouse/medicines/${medicineId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setTableMsg(data?.detail || "Unable to delete medicine");
        return;
      }
      setTableMsg("Medicine removed from warehouse");
      await load();
    } catch (_) {
      setTableMsg("Network error while deleting medicine");
    }
  };

  const queuedOutbound = useMemo(
    () => outboundTransfers.filter((x) => ["requested", "picking", "packed"].includes(x.status)),
    [outboundTransfers],
  );
  const sc = { requested: T.blue, picking: T.yellow, packed: T.green, dispatched: T.gray400, received: T.green };

  return (
    <div>
      <PageHeader
        title="Warehouse Fulfillment"
        badge={`Stock SKUs: ${stock.length}`}
        actions={
          <>
            <Btn variant="secondary" size="sm" onClick={() => setShowSingleAdd((v) => !v)}><PlusCircle size={12} />{showSingleAdd ? "Close Add" : "Add Medicine"}</Btn>
            <Btn variant="secondary" size="sm" onClick={() => setShowBulkAdd((v) => !v)}><Upload size={12} />{showBulkAdd ? "Close Bulk" : "Bulk Upload"}</Btn>
            <Btn variant="secondary" size="sm" onClick={() => setShowCsvAdd((v) => !v)}><Upload size={12} />{showCsvAdd ? "Close CSV" : "CSV Upload"}</Btn>
            <Btn variant="secondary" size="sm" onClick={downloadCsvTemplate}><Download size={12} />CSV Format</Btn>
            <Btn variant="secondary" size="sm" onClick={() => setShowSendAdmin((v) => !v)}><PlusCircle size={12} />{showSendAdmin ? "Close" : "Send Medicine to Admin"}</Btn>
            <Btn variant="secondary" size="sm" onClick={() => setShowSendPharmacy((v) => !v)}><PlusCircle size={12} />{showSendPharmacy ? "Close" : "Send Medicine to Pharmacy"}</Btn>
          </>
        }
      />
      {showSingleAdd ? (
        <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14, marginBottom: 12 }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 8, marginBottom: 8 }}>
            <input value={singleForm.name} onChange={(e) => setSingleForm({ ...singleForm, name: e.target.value })} placeholder="Medicine name" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
            <input value={singleForm.pzn} onChange={(e) => setSingleForm({ ...singleForm, pzn: e.target.value })} placeholder="PZN" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
            <input value={singleForm.price} onChange={(e) => setSingleForm({ ...singleForm, price: e.target.value })} placeholder="Price" type="number" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
            <input value={singleForm.initial_stock} onChange={(e) => setSingleForm({ ...singleForm, initial_stock: e.target.value })} placeholder="Initial Stock" type="number" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: 8 }}>
            <input value={singleForm.package} onChange={(e) => setSingleForm({ ...singleForm, package: e.target.value })} placeholder="Package" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
            <input value={singleForm.description} onChange={(e) => setSingleForm({ ...singleForm, description: e.target.value })} placeholder="Description" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
            <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
              <input type="checkbox" checked={singleForm.rx_required} onChange={(e) => setSingleForm({ ...singleForm, rx_required: e.target.checked })} />
              Rx Required
            </label>
            <Btn variant="primary" size="sm" onClick={addSingleMedicine}>Save</Btn>
          </div>
          {singleMsg ? <div style={{ marginTop: 8, fontSize: 12, color: singleMsg.includes("added") ? T.green : T.red }}>{singleMsg}</div> : null}
        </div>
      ) : null}
      {showBulkAdd ? (
        <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14, marginBottom: 12 }}>
          <div style={{ fontSize: 12, color: T.gray600, marginBottom: 8 }}>
            Bulk line format: <code>name|pzn|price|package|initial_stock|rx_required|description|image_url</code>
          </div>
          <textarea value={bulkText} onChange={(e) => setBulkText(e.target.value)} rows={6} placeholder={"Paracetamol 500mg|11111111|22.5|10 tabs|120|false|Pain relief|\nAmoxicillin 250mg|22222222|88.0|6 caps|75|true|Antibiotic|"} style={{ width: "100%", padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8, fontFamily: "monospace", fontSize: 12 }} />
          <div style={{ marginTop: 8 }}><Btn variant="primary" size="sm" onClick={uploadBulkMedicines}>Upload Bulk</Btn></div>
          {bulkMsg ? <div style={{ marginTop: 8, fontSize: 12, color: bulkMsg.includes("complete") ? T.green : T.red }}>{bulkMsg}</div> : null}
        </div>
      ) : null}
      {showCsvAdd ? (
        <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14, marginBottom: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input type="file" accept=".csv" onChange={(e) => setCsvFile(e.target.files?.[0] || null)} />
            <Btn variant="primary" size="sm" onClick={uploadCsvMedicines}>Upload CSV</Btn>
            <Btn variant="secondary" size="sm" onClick={downloadCsvTemplate}><Download size={12} />Download Format</Btn>
          </div>
          {csvMsg ? <div style={{ marginTop: 8, fontSize: 12, color: csvMsg.includes("processed") ? T.green : T.red }}>{csvMsg}</div> : null}
        </div>
      ) : null}
      {showSendPharmacy ? (
        <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14, marginBottom: 12 }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 2fr 2fr", gap: 8 }}>
            <select value={sendForm.medicine_id} onChange={(e) => setSendForm({ ...sendForm, medicine_id: e.target.value })} style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }}>
              <option value="">Select medicine</option>
              {stock.map((m) => <option key={m.medicine_id} value={m.medicine_id}>{m.medicine_name} (warehouse stock: {m.quantity || 0})</option>)}
            </select>
            <input value={sendForm.quantity} onChange={(e) => setSendForm({ ...sendForm, quantity: e.target.value })} placeholder="Units" type="number" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
            <select value={sendForm.pharmacy_store_id} onChange={(e) => setSendForm({ ...sendForm, pharmacy_store_id: e.target.value })} style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }}>
              <option value="">Select pharmacy</option>
              {pharmacies.map((p) => <option key={p.id} value={p.id}>{p.node_id} - {p.name}</option>)}
            </select>
            <div style={{ display: "flex", gap: 8 }}>
              <input value={sendForm.note} onChange={(e) => setSendForm({ ...sendForm, note: e.target.value })} placeholder="Note (optional)" style={{ flex: 1, padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
              <Btn variant="primary" size="sm" onClick={sendToPharmacy}>Create</Btn>
            </div>
          </div>
          {pharmacies.length === 0 ? <div style={{ marginTop: 8, fontSize: 12, color: T.red }}>No pharmacy configured yet. Create pharmacy user/store first.</div> : null}
          {sendMsg ? <div style={{ marginTop: 8, fontSize: 12, color: sendMsg === "Transfer created" ? T.green : T.red }}>{sendMsg}</div> : null}
        </div>
      ) : null}
      {showSendAdmin ? (
        <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14, marginBottom: 12 }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 2fr auto", gap: 8 }}>
            <select value={sendAdminForm.medicine_id} onChange={(e) => setSendAdminForm({ ...sendAdminForm, medicine_id: e.target.value })} style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }}>
              <option value="">Select medicine</option>
              {stock.map((m) => <option key={m.medicine_id} value={m.medicine_id}>{m.medicine_name} (warehouse stock: {m.quantity || 0})</option>)}
            </select>
            <input value={sendAdminForm.quantity} onChange={(e) => setSendAdminForm({ ...sendAdminForm, quantity: e.target.value })} placeholder="Units" type="number" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
            <input value={sendAdminForm.note} onChange={(e) => setSendAdminForm({ ...sendAdminForm, note: e.target.value })} placeholder="Note (optional)" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
            <Btn variant="primary" size="sm" onClick={sendToAdmin}>Create</Btn>
          </div>
          {sendAdminMsg ? <div style={{ marginTop: 8, fontSize: 12, color: sendAdminMsg === "Sent to admin inventory" ? T.green : T.red }}>{sendAdminMsg}</div> : null}
        </div>
      ) : null}
      <div style={{ marginBottom: 12, background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: T.gray900, marginBottom: 8 }}>Warehouse Medicines Table</div>
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr", gap: 6, fontSize: 11, color: T.gray500, marginBottom: 8 }}>
          <div>Name</div><div>PZN</div><div>Price</div><div>Warehouse Stock</div><div>Actions</div>
        </div>
        {stock.length === 0 ? <div style={{ fontSize: 12, color: T.gray500 }}>No medicines in warehouse stock yet. Use Add/Bulk/CSV upload.</div> : stock.map((m) => <div key={m.medicine_id} style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr", gap: 6, padding: "7px 0", borderBottom: `1px solid ${T.gray100}`, fontSize: 12 }}><div>{m.medicine_name}</div><div>{m.pzn}</div><div>₹{Number(m.price || 0).toFixed(2)}</div><div>{m.quantity}</div><div style={{ display:"flex", gap:6 }}><Btn variant="secondary" size="sm" onClick={() => startEditMedicine(m)}>Edit</Btn><Btn variant="secondary" size="sm" style={{ color:T.red }} onClick={() => deleteMedicine(m.medicine_id)}>Delete</Btn></div></div>)}
        {editingMedicineId ? (
          <div style={{ marginTop:10, border:`1px solid ${T.gray200}`, borderRadius:10, padding:10 }}>
            <div style={{ fontSize:12, fontWeight:600, marginBottom:8 }}>Edit Warehouse Medicine</div>
            <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr 1fr 1fr auto", gap:8 }}>
              <input value={editMedicineForm.name} onChange={(e)=>setEditMedicineForm({...editMedicineForm, name:e.target.value})} placeholder="Name" style={{ padding:8, border:`1px solid ${T.gray200}`, borderRadius:8 }} />
              <input value={editMedicineForm.pzn} disabled style={{ padding:8, border:`1px solid ${T.gray200}`, borderRadius:8, background:T.gray50 }} />
              <input value={editMedicineForm.price} onChange={(e)=>setEditMedicineForm({...editMedicineForm, price:e.target.value})} placeholder="Price" type="number" style={{ padding:8, border:`1px solid ${T.gray200}`, borderRadius:8 }} />
              <input value={editMedicineForm.warehouse_stock} onChange={(e)=>setEditMedicineForm({...editMedicineForm, warehouse_stock:e.target.value})} placeholder="Warehouse stock" type="number" style={{ padding:8, border:`1px solid ${T.gray200}`, borderRadius:8 }} />
              <div style={{ display:"flex", gap:6 }}>
                <Btn variant="primary" size="sm" onClick={saveEditMedicine}>Save</Btn>
                <Btn variant="secondary" size="sm" onClick={()=>setEditingMedicineId(null)}>Cancel</Btn>
              </div>
            </div>
          </div>
        ) : null}
        {tableMsg ? <div style={{ marginTop:8, fontSize:12, color: tableMsg.toLowerCase().includes("unable") || tableMsg.toLowerCase().includes("error") ? T.red : T.green }}>{tableMsg}</div> : null}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {queuedOutbound.map((t) => (
          <div key={t.id} style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 16, borderLeft: `4px solid ${sc[t.status] || T.gray400}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ fontFamily: "monospace", fontSize: 12, fontWeight: 600 }}>TRF-{String(t.id).padStart(5, "0")}</span>
                <span style={{ background: `${sc[t.status] || T.gray400}15`, color: sc[t.status], padding: "3px 10px", borderRadius: 6, fontSize: 10, fontWeight: 700, textTransform: "uppercase" }}>{t.status}</span>
              </div>
              <span style={{ fontSize: 12, color: T.gray400 }}>to {t.pharmacy_store_name || "-"}</span>
            </div>
            <div style={{ fontSize: 11, color: T.gray500, marginBottom: 8 }}>
              Requested by: {(t.created_by_user_role || "-").replace("_", " ")} · {t.created_by_user_name || `User #${t.created_by_user_id}`}
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
              <div style={{ padding: "8px 14px", background: T.gray50, borderRadius: 8, fontSize: 12, display: "flex", gap: 8, alignItems: "center" }}>
                <span style={{ fontWeight: 500, color: T.gray800 }}>{t.medicine_name}</span>
                <span style={{ color: T.blue, fontWeight: 700 }}>x{t.quantity}</span>
              </div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              {t.status === "requested" && <Btn variant="primary" size="sm" disabled={savingTransferId === t.id} onClick={() => updateTransferStatus(t.id, "picking")}><Play size={12} />Start Pick</Btn>}
              {t.status === "picking" && <span style={{ fontSize: 12, color: T.yellow, fontWeight: 600 }}>In Picking</span>}
              {t.status === "packed" && <span style={{ fontSize: 12, color: T.green, fontWeight: 600 }}>Ready for Dispatch</span>}
            </div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 20, background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: T.gray900, marginBottom: 8 }}>Inbound from Admin</div>
        {inboundTransfers.length === 0 ? <div style={{ fontSize: 12, color: T.gray500 }}>No inbound transfers yet. Admin should use "Send to Warehouse".</div> : inboundTransfers.slice(0, 8).map((x) => <div key={x.id} style={{ fontSize: 12, color: T.gray700, padding: "6px 0", borderBottom: `1px solid ${T.gray100}` }}>{x.medicine_name} · +{x.quantity} · {new Date(x.created_at).toLocaleString()}</div>)}
      </div>
    </div>
  );
}