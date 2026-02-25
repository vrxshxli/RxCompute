import React, { useEffect, useState } from 'react';
import { LayoutGrid, Building2, Warehouse, CheckCircle, ChevronLeft, Mail, Lock, Eye, EyeOff, AlertCircle, ArrowRight, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Logo } from '../../components/shared';
import T from '../../utils/tokens';

const ROLES = [
  { key: "admin", icon: LayoutGrid, label: "Admin Console", desc: "Full platform control", color: T.orange, email: "admin@rxcompute.com", pass: "admin123" },
  { key: "pharmacy_store", icon: Building2, label: "Pharmacy Cockpit", desc: "Order verification & dispensing", color: T.blue, email: "pharmacy@rxcompute.com", pass: "pharma123" },
  { key: "warehouse", icon: Warehouse, label: "Warehouse Console", desc: "Fulfillment & dispatch", color: T.green, email: "warehouse@rxcompute.com", pass: "warehouse123" },
];

export default function LoginPage({ onBack, forcedRole }) {
  const { login } = useAuth();
  const [sel, setSel] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const pickRole = (r) => { setSel(r.key); setEmail(r.email); setPassword(r.pass); setError(""); };
  useEffect(() => {
    if (!forcedRole) return;
    const role = ROLES.find((r) => r.key === forcedRole);
    if (role) pickRole(role);
  }, [forcedRole]);

  const handleLogin = async () => {
    if (!sel) { setError("Select a role"); return; }
    if (!email || !password) { setError("Fill all fields"); return; }
    setLoading(true);
    const res = await login(email, password, sel);
    if (!res.success) setError(res.error);
    setLoading(false);
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", background: T.navy900, position: "relative", overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, opacity: .04, backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='40' height='40' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='20' cy='20' r='1' fill='%23fff'/%3E%3C/svg%3E\")" }} />
      <div style={{ position: "absolute", top: "-20%", right: "-10%", width: 600, height: 600, borderRadius: "50%", background: `radial-gradient(circle,${T.orange}08,transparent 70%)` }} />
      <div style={{ position: "absolute", bottom: "-20%", left: "-10%", width: 500, height: 500, borderRadius: "50%", background: `radial-gradient(circle,${T.blue}08,transparent 70%)` }} />

      {/* Left branding */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", padding: "60px 80px", position: "relative", zIndex: 1 }}>
        <button onClick={onBack} style={{ position: "absolute", top: 32, left: 40, background: "none", border: `1px solid ${T.navy600}`, borderRadius: 8, color: T.gray400, padding: "8px 16px", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}><ChevronLeft size={16} /> Back</button>
        <div style={{ animation: "fadeInUp .6s ease both" }}>
          <Logo size="lg" dark />
          <p style={{ color: T.gray400, fontSize: 18, marginTop: 16, lineHeight: 1.7, maxWidth: 400 }}>AI-Powered Pharmacy Management — Conversational ordering, predictive intelligence, multi-agent safety.</p>
          <div style={{ display: "flex", gap: 24, marginTop: 48 }}>
            {[["6","AI Agents"],["52","Medicines"],["3","Dashboards"]].map(([v,l]) => <div key={l}><div style={{ fontSize: 32, fontWeight: 800, color: T.orange }}>{v}</div><div style={{ fontSize: 12, color: T.gray500, marginTop: 4 }}>{l}</div></div>)}
          </div>
        </div>
      </div>

      {/* Right login */}
      <div style={{ width: 520, display: "flex", flexDirection: "column", justifyContent: "center", padding: "40px 48px", position: "relative", zIndex: 1 }}>
        <div style={{ background: "rgba(255,255,255,.04)", backdropFilter: "blur(20px)", border: `1px solid ${T.navy600}`, borderRadius: 20, padding: 40, animation: "fadeInUp .6s ease .2s both" }}>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: T.white, marginBottom: 4 }}>Welcome Back</h2>
          <p style={{ fontSize: 14, color: T.gray400, marginBottom: 28 }}>Select your role and sign in</p>

          {/* Role cards */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 }}>
            {ROLES.map(r => { const s = sel === r.key; const I = r.icon; return (
              <button key={r.key} onClick={() => pickRole(r)} style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 16px", background: s ? `${r.color}15` : "rgba(255,255,255,.03)", border: `1.5px solid ${s ? r.color : T.navy600}`, borderRadius: 12, cursor: "pointer", transition: "all .2s", textAlign: "left", width: "100%" }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: `${r.color}${s?"20":"10"}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}><I size={20} color={r.color} /></div>
                <div style={{ flex: 1 }}><div style={{ fontSize: 14, fontWeight: 600, color: s ? T.white : T.gray300 }}>{r.label}</div><div style={{ fontSize: 11, color: T.gray500, marginTop: 2 }}>{r.desc}</div></div>
                {s && <CheckCircle size={18} color={r.color} />}
              </button>
            ); })}
          </div>

          {/* Form */}
          {sel && (
            <div style={{ animation: "fadeInUp .3s ease both" }}>
              <div style={{ marginBottom: 16 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: T.gray400, textTransform: "uppercase", letterSpacing: .5, display: "block", marginBottom: 6 }}>Email</label>
                <div style={{ position: "relative" }}><Mail size={16} color={T.gray500} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)" }} /><input value={email} onChange={e => setEmail(e.target.value)} type="email" style={{ width: "100%", padding: "12px 14px 12px 40px", background: "rgba(255,255,255,.06)", border: `1px solid ${T.navy600}`, borderRadius: 10, color: T.white, fontSize: 14, outline: "none", boxSizing: "border-box" }} /></div>
              </div>
              <div style={{ marginBottom: 20 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: T.gray400, textTransform: "uppercase", letterSpacing: .5, display: "block", marginBottom: 6 }}>Password</label>
                <div style={{ position: "relative" }}><Lock size={16} color={T.gray500} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)" }} /><input value={password} onChange={e => setPassword(e.target.value)} type={showPw ? "text" : "password"} onKeyDown={e => e.key === "Enter" && handleLogin()} style={{ width: "100%", padding: "12px 44px 12px 40px", background: "rgba(255,255,255,.06)", border: `1px solid ${T.navy600}`, borderRadius: 10, color: T.white, fontSize: 14, outline: "none", boxSizing: "border-box" }} /><button onClick={() => setShowPw(!showPw)} style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: T.gray500, display: "flex" }}>{showPw ? <EyeOff size={16} /> : <Eye size={16} />}</button></div>
              </div>
              {error && <div style={{ padding: "10px 14px", background: `${T.red}12`, border: `1px solid ${T.red}30`, borderRadius: 8, color: T.red, fontSize: 13, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}><AlertCircle size={14} />{error}</div>}
              <button onClick={handleLogin} disabled={loading} style={{ width: "100%", padding: "13px", background: ROLES.find(x => x.key === sel)?.color || T.orange, color: T.white, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, opacity: loading ? .7 : 1 }}>
                {loading ? <><RefreshCw size={16} style={{ animation: "spin 1s linear infinite" }} /> Signing in...</> : <>Sign In <ArrowRight size={16} /></>}
              </button>
              <div style={{ marginTop: 16, padding: "12px 14px", background: "rgba(255,255,255,.03)", borderRadius: 8, border: `1px dashed ${T.navy600}` }}>
                <div style={{ fontSize: 11, color: T.gray500, fontWeight: 600, marginBottom: 4, textTransform: "uppercase", letterSpacing: .5 }}>Demo Credentials</div>
                <div style={{ fontSize: 12, color: T.gray400, fontFamily: "monospace" }}>{ROLES.find(x => x.key === sel)?.email} / {ROLES.find(x => x.key === sel)?.pass}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}