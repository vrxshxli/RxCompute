import React from 'react';
import { ChevronRight, ChevronLeft, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Logo } from '../shared';
import T from '../../utils/tokens';

export default function Sidebar({ items, active, onSelect, role, collapsed, onToggle, isMobile }) {
  const { user, logout } = useAuth();
  const isPharmacy = role === "pharmacy_store" || role === "pharmacy";
  const roleColor = role === "admin" ? T.orange : isPharmacy ? T.blue : T.green;
  const roleLabel = role === "admin" ? "Admin Console" : isPharmacy ? "Pharmacy Cockpit" : "Warehouse";
  const showMini = !isMobile && collapsed;
  const showSidebar = !isMobile || !collapsed;

  if (!showSidebar) return null;
  return (
    <div style={{
      width: showMini ? 68 : 256,
      minHeight: isMobile ? "calc(100vh - 44px)" : "100vh",
      maxHeight: isMobile ? "calc(100vh - 44px)" : "none",
      background: T.white,
      borderRight: `1px solid ${T.gray200}`,
      display: "flex",
      flexDirection: "column",
      transition: "width 0.25s ease",
      overflow: "hidden",
      flexShrink: 0,
      position: isMobile ? "fixed" : "static",
      top: isMobile ? 44 : "auto",
      left: 0,
      zIndex: 70,
      boxShadow: isMobile ? "0 10px 28px rgba(0,0,0,.18)" : "none",
    }}>
      {/* Header */}
      <div style={{ padding: showMini ? "20px 16px" : "20px 20px", borderBottom: `1px solid ${T.gray200}`, display: "flex", alignItems: "center", justifyContent: showMini ? "center" : "space-between" }}>
        {!showMini && <Logo size="sm" />}
        {showMini && (
          <div style={{ width: 30, height: 30, borderRadius: 8, background: `${roleColor}12`, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: roleColor, fontSize: 13, fontWeight: 800 }}>{role[0].toUpperCase()}</span>
          </div>
        )}
        <button onClick={onToggle} style={{ background: "none", border: "none", cursor: "pointer", padding: 4, color: T.gray400, display: "flex" }}>
          {showMini ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Role badge */}
      {!showMini && (
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
              padding: showMini ? "11px 0" : "11px 20px", border: "none", cursor: "pointer",
              background: isActive ? `${roleColor}08` : "transparent",
              borderLeft: isActive ? `3px solid ${roleColor}` : "3px solid transparent",
              color: isActive ? roleColor : T.gray600, fontSize: 13,
              fontWeight: isActive ? 600 : 500, transition: "all 0.15s",
              justifyContent: showMini ? "center" : "flex-start",
              fontFamily: "var(--font-body)",
            }}>
              <Icon size={18} />
              {!showMini && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* User section */}
      <div style={{ padding: showMini ? "16px 8px" : "16px 20px", borderTop: `1px solid ${T.gray200}` }}>
        {!showMini && (
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
          {!showMini && "Sign Out"}
        </button>
      </div>
    </div>
  );
}