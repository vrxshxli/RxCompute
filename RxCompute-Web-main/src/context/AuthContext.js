import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

const AuthContext = createContext(null);
const API_BASE = process.env.REACT_APP_API_BASE_URL || "https://rxcompute-api.onrender.com";
const TOKEN_KEY = "rxcompute_web_token";
const USER_KEY = "rxcompute_web_user";

const ROLE_ALIASES = { pharmacy: "pharmacy_store" };

function normalizeRole(role) {
  const raw = (role || "user").toLowerCase();
  return ROLE_ALIASES[raw] || raw;
}

function deriveAvatar(name, fallback = "RX") {
  const safe = (name || "").trim();
  if (!safe) return fallback;
  const parts = safe.split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase() || "").join("") || fallback;
}

function fallbackNameForRole(role, providedName) {
  if ((providedName || "").trim()) return providedName;
  const normalized = normalizeRole(role);
  if (normalized === "admin") return "Admin";
  if (normalized === "pharmacy_store") return "Pharmacy";
  if (normalized === "warehouse") return "Warehouse";
  return "Rx User";
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);

  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY);
    const savedUser = localStorage.getItem(USER_KEY);
    if (!savedToken || !savedUser) return;
    try {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    } catch (_) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  }, []);

  const login = async (email, password, role) => {
    try {
      const res = await fetch(`${API_BASE}/auth/web-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password,
          role: normalizeRole(role),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        return { success: false, error: data?.detail || "Login failed" };
      }
      const userPayload = {
        id: data.user_id,
        email: data.email,
        name: fallbackNameForRole(data.role, data.name),
        role: normalizeRole(data.role),
        avatar: deriveAvatar(fallbackNameForRole(data.role, data.name)),
      };
      try {
        const meRes = await fetch(`${API_BASE}/users/me`, {
          headers: { Authorization: `Bearer ${data.access_token}` },
        });
        if (meRes.ok) {
          const me = await meRes.json();
          const bestName = fallbackNameForRole(me.role || data.role, me.name);
          userPayload.name = bestName;
          userPayload.avatar = deriveAvatar(bestName);
        }
      } catch (_) {}
      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(userPayload));
      setToken(data.access_token);
      setUser(userPayload);
      return { success: true, user: userPayload };
    } catch (_) {
      return { success: false, error: "Network error during login" };
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  };

  const value = useMemo(() => ({ user, token, login, logout, apiBase: API_BASE }), [user, token]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}