import React from 'react';
import T from '../../utils/tokens';
import {
  ArrowUpRight, ArrowDownRight, Search, Database,
  ChevronUp, ChevronDown,
} from 'lucide-react';

/* ─── StatCard ─── */
export function StatCard({ icon: Icon, label, value, subtitle, trend, trendValue, color = T.blue }) {
  return (
    <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 10, padding: "20px 24px", flex: 1, minWidth: 190, transition: "box-shadow 0.2s" }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = "0 4px 20px rgba(0,0,0,0.06)"}
      onMouseLeave={e => e.currentTarget.style.boxShadow = "none"}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ color: T.gray500, fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.8, marginBottom: 8 }}>{label}</div>
          <div style={{ color: T.gray900, fontSize: 28, fontWeight: 700, lineHeight: 1 }}>{value}</div>
          {subtitle && <div style={{ color: T.gray500, fontSize: 12, marginTop: 6 }}>{subtitle}</div>}
        </div>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: `${color}12`, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Icon size={20} color={color} />
        </div>
      </div>
      {trend && (
        <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 12, fontSize: 12 }}>
          {trend === "up" ? <ArrowUpRight size={14} color={T.green} /> : <ArrowDownRight size={14} color={T.red} />}
          <span style={{ color: trend === "up" ? T.green : T.red, fontWeight: 600 }}>{trendValue}</span>
          <span style={{ color: T.gray400 }}>vs yesterday</span>
        </div>
      )}
    </div>
  );
}

/* ─── AgentBadge ─── */
const AGENT_MAP = {
  conversation_agent: { color: T.blue, label: "Conv" },
  safety_agent: { color: T.red, label: "Safety" },
  inventory_agent: { color: T.green, label: "Inv" },
  scheduler_agent: { color: T.yellow, label: "Sched" },
  order_agent: { color: T.orange, label: "Order" },
  prediction_agent: { color: T.purple, label: "Pred" },
};
export function AgentBadge({ agent }) {
  const m = AGENT_MAP[agent] || { color: T.gray400, label: agent };
  return (
    <span style={{ background: `${m.color}15`, color: m.color, padding: "2px 7px", borderRadius: 4, fontSize: 10, fontWeight: 700, letterSpacing: 0.4, textTransform: "uppercase" }}>
      {m.label}
    </span>
  );
}

/* ─── StockDot ─── */
export function StockDot({ level }) {
  const c = level > 30 ? T.green : level > 10 ? T.yellow : level > 0 ? T.red : T.gray900;
  return <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: c, marginRight: 6 }} />;
}

/* ─── Toggle ─── */
export function Toggle({ on, onChange }) {
  return (
    <button onClick={onChange} style={{ width: 40, height: 22, borderRadius: 11, border: "none", cursor: "pointer", background: on ? T.blue : T.gray300, position: "relative", transition: "background 0.2s" }}>
      <span style={{ position: "absolute", top: 2, left: on ? 20 : 2, width: 18, height: 18, borderRadius: "50%", background: T.white, transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)" }} />
    </button>
  );
}

/* ─── SearchInput ─── */
export function SearchInput({ value, onChange, placeholder = "Search..." }) {
  return (
    <div style={{ position: "relative", flex: 1, maxWidth: 320 }}>
      <Search size={16} color={T.gray400} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)" }} />
      <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
        style={{ width: "100%", padding: "9px 12px 9px 36px", border: `1px solid ${T.gray200}`, borderRadius: 8, fontSize: 13, color: T.gray900, background: T.white, outline: "none", boxSizing: "border-box", fontFamily: "var(--font-body)" }} />
    </div>
  );
}

/* ─── Btn ─── */
export function Btn({ children, variant = "primary", size = "sm", onClick, style: sx, disabled }) {
  const base = { border: "none", cursor: disabled ? "not-allowed" : "pointer", fontWeight: 600, borderRadius: 8, display: "inline-flex", alignItems: "center", gap: 6, opacity: disabled ? 0.5 : 1, transition: "all 0.15s", fontFamily: "var(--font-body)" };
  const variants = {
    primary: { background: T.orange, color: T.white, padding: size === "sm" ? "8px 16px" : "11px 22px", fontSize: size === "sm" ? 12 : 13 },
    secondary: { background: T.white, color: T.gray700, padding: size === "sm" ? "7px 15px" : "10px 21px", fontSize: size === "sm" ? 12 : 13, border: `1px solid ${T.gray200}` },
    ghost: { background: "transparent", color: T.blue, padding: size === "sm" ? "6px 10px" : "9px 16px", fontSize: size === "sm" ? 12 : 13 },
    danger: { background: T.red, color: T.white, padding: size === "sm" ? "8px 16px" : "11px 22px", fontSize: size === "sm" ? 12 : 13 },
    success: { background: T.green, color: T.white, padding: size === "sm" ? "8px 16px" : "11px 22px", fontSize: size === "sm" ? 12 : 13 },
  };
  return <button onClick={onClick} disabled={disabled} style={{ ...base, ...variants[variant], ...sx }}>{children}</button>;
}

/* ─── Logo ─── */
export function Logo({ size = "md", dark = false }) {
  const fs = size === "sm" ? 16 : size === "md" ? 20 : size === "lg" ? 32 : 40;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 2, fontWeight: 800, fontSize: fs, fontFamily: "var(--font-display)" }}>
      <span style={{ color: T.orange }}>Rx</span>
      <span style={{ color: dark ? T.white : T.blue }}>Compute</span>
    </div>
  );
}

/* ─── PageHeader ─── */
export function PageHeader({ title, subtitle, badge, actions }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: T.gray900, margin: 0 }}>{title}</h1>
          {badge && <span style={{ background: `${T.blue}12`, color: T.blue, padding: "2px 10px", borderRadius: 6, fontSize: 11, fontWeight: 600 }}>{badge}</span>}
        </div>
        {subtitle && <p style={{ color: T.gray500, fontSize: 13, marginTop: 4, marginBottom: 0 }}>{subtitle}</p>}
      </div>
      {actions && <div style={{ display: "flex", gap: 8 }}>{actions}</div>}
    </div>
  );
}

/* ─── EmptyState ─── */
export function EmptyState({ icon: Icon, title, subtitle }) {
  return (
    <div style={{ textAlign: "center", padding: "60px 20px", color: T.gray400 }}>
      <Icon size={48} strokeWidth={1} />
      <div style={{ fontSize: 16, fontWeight: 600, color: T.gray600, marginTop: 16 }}>{title}</div>
      {subtitle && <div style={{ fontSize: 13, marginTop: 8 }}>{subtitle}</div>}
    </div>
  );
}