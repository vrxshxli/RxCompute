import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { SearchInput, PageHeader } from '../../components/shared';
import { useAuth } from '../../context/AuthContext';
export default function AdminPatients() {
  const { token, apiBase } = useAuth();
  const [search, setSearch] = useState("");
  const [patients, setPatients] = useState([]);

  useEffect(() => {
    if (!token) return;
    const load = async () => {
      try {
        const res = await fetch(`${apiBase}/users/?role=user`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data = await res.json();
        const mapped = (Array.isArray(data) ? data : []).map((u) => ({
          pid: `PAT-${u.id}`,
          name: (u.name || "").trim() || `User #${u.id}`,
          email: u.email || "-",
        }));
        setPatients(mapped);
      } catch (_) {}
    };
    load();
  }, [token, apiBase]);

  const filtered = useMemo(
    () =>
      search
        ? patients.filter(
            (p) =>
              p.name.toLowerCase().includes(search.toLowerCase()) ||
              p.pid.toLowerCase().includes(search.toLowerCase()),
          )
        : patients,
    [patients, search],
  );
  return (<div><PageHeader title="Patients" badge={String(patients.length)}/>
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
        <div style={{ fontSize:12, color:T.gray500 }}>{p.email}</div>
      </div>
    ))}
  </div></div>);
}