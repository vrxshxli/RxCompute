import React from 'react';
import { ChevronRight, ChevronLeft, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Logo } from '../shared';
import T from '../../utils/tokens';

export default function Sidebar({ items, active, onSelect, role, collapsed, onToggle }) {
  const { user, logout } = useAuth();
  const roleColor = role === "admin" ? T.orange : role === "pharmacy" ? T.blue : T.green;
  const roleLabel = role === "admin" ? "Admin Console" : role === "pharmacy" ? "Pharmacy Cockpit" : "Warehouse";

  return (
    <div style={{
      width: collapsed ? 68 : 256, minHeight: "100vh", background: T.white,
      borderRight: `1px solid ${T.gray200}`, display: "flex", flexDirection: "column",
      transition: "width 0.25s ease", overflow: "hidden", flexShrink: 0,
    }}>
      {/* Header */}
      <div style={{ padding: collapsed ? "20px 16px" : "20px 20px", borderBottom: `1px solid ${T.gray200}`, display: "flex", alignItems: "center", justifyContent: collapsed ? "center" : "space-between" }}>
        {!collapsed && <Logo size="sm" />}
        {collapsed && (
          <div style={{ width: 30, height: 30, borderRadius: 8, background: `${roleColor}12`, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: roleColor, fontSize: 13, fontWeight: 800 }}>{role[0].toUpperCase()}</span>
          </div>
        )}
        <button onClick={onToggle} style={{ background: "none", border: "none", cursor: "pointer", padding: 4, color: T.gray400, display: "flex" }}>
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Role badge */}
      {!collapsed && (
        <div style={{ padding: "10px 20px" }}>
          <span style={{ background: `${roleColor}12`, color: roleColor, padding: "3px 10px", borderRadius: 6, fontSize: 10, fontWeight: 700, letterSpacing: 0.8, textTransform: "uppercase" }}>
            {roleLabel}
          </span>
        </div>
      )}

      {/* Nav links */}
      <nav style={{ flex: 1, padding: "8px 0" }}>
        {items.map(item => {
          const isActive = active === item.key;
          const Icon = item.icon;
          return (
            <button key={item.key} onClick={() => onSelect(item.key)} style={{
              display: "flex", alignItems: "center", gap: 12, width: "100%",
              padding: collapsed ? "11px 0" : "11px 20px", border: "none", cursor: "pointer",
              background: isActive ? `${roleColor}08` : "transparent",
              borderLeft: isActive ? `3px solid ${roleColor}` : "3px solid transparent",
              color: isActive ? roleColor : T.gray600, fontSize: 13,
              fontWeight: isActive ? 600 : 500, transition: "all 0.15s",
              justifyContent: collapsed ? "center" : "flex-start",
              fontFamily: "var(--font-body)",
            }}>
              <Icon size={18} />
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* User section */}
      <div style={{ padding: collapsed ? "16px 8px" : "16px 20px", borderTop: `1px solid ${T.gray200}` }}>
        {!collapsed && (
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: `${roleColor}15`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, color: roleColor }}>
              {user?.avatar}
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: T.gray800 }}>{user?.name}</div>
              <div style={{ fontSize: 11, color: T.gray500 }}>{user?.email}</div>
            </div>
          </div>
        )}
        <button onClick={logout} style={{ display: "flex", alignItems: "center", gap: 8, background: "none", border: "none", cursor: "pointer", color: T.red, fontSize: 12, fontWeight: 500, padding: 0 }}>
          <LogOut size={14} />
          {!collapsed && "Sign Out"}
        </button>
      </div>
    </div>
  );
}