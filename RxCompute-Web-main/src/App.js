import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import { LayoutGrid, Package, Bell, ShoppingCart, Shield, Search, Link2, Users, Map, Inbox, CheckCircle2, AlertTriangle, BarChart3, Grid3X3, Truck, Wifi, Menu, UserCircle2, ActivitySquare } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { NotificationProvider, useNotifications } from './context/NotificationContext';
import { Logo } from './components/shared';
import VoiceSafetyAssistant from './components/shared/VoiceSafetyAssistant';
import Sidebar from './components/layout/Sidebar';
import LandingPage from './pages/landing/LandingPage';
import LoginPage from './pages/auth/LoginPage';
import T from './utils/tokens';

// Admin screens
import AdminDashboard from './pages/admin/Dashboard';
import AdminInventory from './pages/admin/Inventory';
import AdminRefillAlerts from './pages/admin/RefillAlerts';
import AdminOrders from './pages/admin/Orders';
import AdminSafetyRules from './pages/admin/SafetyRules';
import AdminSafetyEvents from './pages/admin/SafetyEvents';
import AdminAgentTraces from './pages/admin/AgentTraces';
import AdminWebhookLogs from './pages/admin/WebhookLogs';
import AdminPatients from './pages/admin/Patients';
import AdminPharmacyGrid from './pages/admin/PharmacyGrid';
import AdminProfile from './pages/admin/Profile';
import AdminSystemHealth from './pages/admin/SystemHealth';

// Pharmacy screens
import PharmacyOrderQueue from './pages/pharmacy/OrderQueue';
import PharmacyVerify from './pages/pharmacy/OrderVerify';
import PharmacyInventory from './pages/pharmacy/PharmacyInventory';
import PharmacyExceptions from './pages/pharmacy/Exceptions';
import PharmacyAnalytics from './pages/pharmacy/Analytics';
import PharmacyProfile from './pages/pharmacy/Profile';

// Warehouse screens
import WarehouseFulfillment from './pages/warehouse/Fulfillment';
import WarehousePickPack from './pages/warehouse/PickPack';
import WarehouseShelfHeatmap from './pages/warehouse/ShelfHeatmap';
import WarehouseDispatch from './pages/warehouse/Dispatch';
import WarehouseRecall from './pages/warehouse/RecallMode';
import WarehouseProfile from './pages/warehouse/Profile';

/* ═══════ NAV CONFIGS ═══════ */
const ADMIN_NAV = [
  { key: "dashboard", label: "Dashboard", icon: LayoutGrid },
  { key: "inventory", label: "Inventory", icon: Package },
  { key: "refill-alerts", label: "Refill Alerts", icon: Bell },
  { key: "orders", label: "Orders", icon: ShoppingCart },
  { key: "safety-events", label: "Agent Workflow", icon: AlertTriangle },
  { key: "safety-rules", label: "Safety Rules", icon: Shield },
  { key: "agent-traces", label: "Agent Traces", icon: Search },
  { key: "webhook-logs", label: "Webhook Logs", icon: Link2 },
  { key: "patients", label: "Patients", icon: Users },
  { key: "pharmacy-grid", label: "Pharmacy Grid", icon: Map },
  { key: "system-health", label: "System Health", icon: ActivitySquare },
  { key: "profile", label: "Profile", icon: UserCircle2 },
];

const PHARMACY_NAV = [
  { key: "order-queue", label: "Order Queue", icon: Inbox },
  { key: "verify-orders", label: "Verify Orders", icon: CheckCircle2 },
  { key: "inventory", label: "Inventory", icon: Package },
  { key: "exceptions", label: "Exceptions", icon: AlertTriangle },
  { key: "analytics", label: "Analytics", icon: BarChart3 },
  { key: "profile", label: "Profile", icon: UserCircle2 },
];

const WAREHOUSE_NAV = [
  { key: "fulfillment", label: "Fulfillment Queue", icon: Inbox },
  { key: "pick-pack", label: "Pick & Pack", icon: Package },
  { key: "shelf-heatmap", label: "Shelf Heatmap", icon: Grid3X3 },
  { key: "dispatch", label: "Dispatch", icon: Truck },
  { key: "recalls", label: "Recall Mode", icon: AlertTriangle },
  { key: "profile", label: "Profile", icon: UserCircle2 },
];

/* ═══════ DASHBOARD SHELL (sidebar + topbar + content) ═══════ */
function DashboardShell() {
  const { user, token, apiBase } = useAuth();
  const { notifications, unreadCount, markRead, markAllRead } = useNotifications();
  const role = user?.role || "admin";
  const isAdmin = role === "admin" || role === "user";
  const isPharmacy = role === "pharmacy_store" || role === "pharmacy";
  const defaultPage = isAdmin ? "dashboard" : isPharmacy ? "order-queue" : "fulfillment";
  const [page, setPage] = useState(defaultPage);
  const [collapsed, setCollapsed] = useState(window.innerWidth < 992);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 992);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    setPage(isAdmin ? "dashboard" : isPharmacy ? "order-queue" : "fulfillment");
  }, [isAdmin, isPharmacy]);
  useEffect(() => {
    const onResize = () => {
      const mobile = window.innerWidth < 992;
      setIsMobile(mobile);
      setCollapsed(mobile);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const nav = isAdmin ? ADMIN_NAV : isPharmacy ? PHARMACY_NAV : WAREHOUSE_NAV;
  const handleSelectPage = (nextPage) => {
    setPage(nextPage);
    if (isMobile) setCollapsed(true);
  };

  const renderPage = () => {
    if (isAdmin) {
      switch (page) {
        case "dashboard": return <AdminDashboard onNavigate={handleSelectPage} />;
        case "inventory": return <AdminInventory />;
        case "refill-alerts": return <AdminRefillAlerts />;
        case "orders": return <AdminOrders />;
        case "safety-events": return <AdminSafetyEvents />;
        case "safety-rules": return <AdminSafetyRules />;
        case "agent-traces": return <AdminAgentTraces />;
        case "webhook-logs": return <AdminWebhookLogs />;
        case "patients": return <AdminPatients />;
        case "pharmacy-grid": return <AdminPharmacyGrid />;
        case "system-health": return <AdminSystemHealth />;
        case "profile": return <AdminProfile />;
        default: return <AdminDashboard />;
      }
    }
    if (isPharmacy) {
      switch (page) {
        case "order-queue": return <PharmacyOrderQueue />;
        case "verify-orders": return <PharmacyVerify />;
        case "inventory": return <PharmacyInventory />;
        case "exceptions": return <PharmacyExceptions />;
        case "analytics": return <PharmacyAnalytics />;
        case "profile": return <PharmacyProfile />;
        default: return <PharmacyOrderQueue />;
      }
    }
    // warehouse
    switch (page) {
      case "fulfillment": return <WarehouseFulfillment />;
      case "pick-pack": return <WarehousePickPack />;
      case "shelf-heatmap": return <WarehouseShelfHeatmap />;
      case "dispatch": return <WarehouseDispatch />;
      case "recalls": return <WarehouseRecall />;
      case "profile": return <WarehouseProfile />;
      default: return <WarehouseFulfillment />;
    }
  };

  const roleColor = isAdmin ? T.orange : isPharmacy ? T.blue : T.green;
  return (
    <div style={{ minHeight: "100vh", background: T.gray100 }}>
      {/* Top bar */}
      <div style={{ position: "sticky", top: 0, zIndex: 50, background: T.navy900, height: 44, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <button
            onClick={() => setCollapsed((v) => !v)}
            style={{ background: "transparent", border: "none", color: T.white, display: "flex", alignItems: "center", cursor: "pointer" }}
          >
            <Menu size={18} />
          </button>
          <Logo size="sm" dark />
          <span style={{ background: `${roleColor}20`, color: roleColor, padding: "3px 12px", borderRadius: 6, fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>
            {isAdmin ? "Admin" : isPharmacy ? "Pharmacy" : "Warehouse"}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: T.green }}><Wifi size={12} /> Systems OK</div>
          <div style={{ width: 1, height: 20, background: T.navy600 }} />
          <VoiceSafetyAssistant
            nav={nav}
            onSelectPage={handleSelectPage}
            notifications={notifications}
            markAllRead={markAllRead}
            token={token}
            apiBase={apiBase}
          />
          <div style={{ position: "relative" }}>
            <button
              onClick={() => setShowNotifications((v) => !v)}
              style={{ background: "transparent", border: "none", color: T.white, cursor: "pointer", display: "flex", alignItems: "center", position: "relative" }}
            >
              <Bell size={16} />
              {unreadCount > 0 ? <span style={{ position: "absolute", top: -6, right: -7, minWidth: 14, height: 14, borderRadius: 7, background: T.red, color: T.white, fontSize: 9, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", padding: "0 3px" }}>{Math.min(99, unreadCount)}</span> : null}
            </button>
            {showNotifications ? (
              <div style={{ position: "absolute", right: 0, top: 28, width: 360, maxHeight: 420, overflowY: "auto", background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 10, boxShadow: "0 10px 24px rgba(0,0,0,.15)", zIndex: 80 }}>
                <div style={{ padding: 10, borderBottom: `1px solid ${T.gray100}`, fontSize: 12, fontWeight: 700, color: T.gray800, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span>Notifications</span>
                  <button onClick={markAllRead} style={{ border: "none", background: "transparent", color: T.blue, cursor: "pointer", fontSize: 11, fontWeight: 600 }}>Mark all read</button>
                </div>
                {notifications.length === 0 ? <div style={{ padding: 12, fontSize: 12, color: T.gray500 }}>No notifications yet</div> : notifications.map((n) => <button key={n.id} onClick={() => markRead(n.id)} style={{ width: "100%", textAlign: "left", border: "none", background: n.is_read ? T.white : `${T.blue}08`, padding: 10, borderBottom: `1px solid ${T.gray100}`, cursor: "pointer" }}><div style={{ fontSize: 12, fontWeight: 600, color: T.gray800 }}>{n.title}</div><div style={{ fontSize: 11, color: T.gray500, marginTop: 3 }}>{n.body}</div></button>)}
              </div>
            ) : null}
          </div>
          <div style={{ fontSize: 12, color: T.gray300, fontWeight: 600 }}>{user?.name || "User"}</div>
          <div style={{ width: 28, height: 28, borderRadius: "50%", background: T.navy700, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, color: T.white, fontWeight: 700 }}>{user?.avatar}</div>
        </div>
      </div>
      {/* Body */}
      <div style={{ display: "flex", alignItems: "flex-start", minHeight: "calc(100vh - 44px)" }}>
        <Sidebar items={nav} active={page} onSelect={handleSelectPage} role={role} collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} isMobile={isMobile} />
        {isMobile && !collapsed ? (
          <div
            onClick={() => setCollapsed(true)}
            style={{ position: "fixed", top: 44, left: 0, right: 0, bottom: 0, background: "rgba(15,23,42,.35)", zIndex: 60 }}
          />
        ) : null}
        <main style={{ flex: 1, padding: 24, minHeight: "calc(100vh - 44px)", overflow: "auto" }}>
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

/* ═══════ PROTECTED ROUTE ═══════ */
function ProtectedRoute({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

/* ═══════ APP ROUTER ═══════ */
function AppRoutes() {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Redirect to dashboard if already logged in
  useEffect(() => {
    if (user) navigate('/dashboard', { replace: true });
  }, [user, navigate]);

  return (
    <Routes>
      <Route path="/" element={<LandingPage onGoToLogin={() => navigate('/login')} />} />
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage onBack={() => navigate('/')} />} />
      <Route path="/login/admin" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage onBack={() => navigate('/')} forcedRole="admin" />} />
      <Route path="/login/pharmacy" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage onBack={() => navigate('/')} forcedRole="pharmacy_store" />} />
      <Route path="/login/warehouse" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage onBack={() => navigate('/')} forcedRole="warehouse" />} />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardShell /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

/* ═══════ ROOT APP ═══════ */
export default function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
      <AppRoutes />
      </NotificationProvider>
    </AuthProvider>
  );
}

