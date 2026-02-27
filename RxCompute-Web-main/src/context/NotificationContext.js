import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from './AuthContext';

const NotificationContext = createContext(null);
const SOUNDED_KEY = "rxcompute_web_sounded_notification_ids";

function readSoundedIds() {
  try {
    const raw = localStorage.getItem(SOUNDED_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return new Set(Array.isArray(parsed) ? parsed : []);
  } catch (_) {
    return new Set();
  }
}

function persistSoundedIds(setObj) {
  try {
    localStorage.setItem(SOUNDED_KEY, JSON.stringify(Array.from(setObj).slice(-500)));
  } catch (_) {}
}

export function NotificationProvider({ children }) {
  const { token, apiBase } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const soundedIdsRef = useRef(readSoundedIds());
  const pollRef = useRef(null);

  const fetchNotifications = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/notifications/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      const list = Array.isArray(data) ? data : [];
      const newUnheard = list.filter((n) => !n.is_read && !soundedIdsRef.current.has(String(n.id)));
      if (newUnheard.length > 0) {
        try {
          const audio = new Audio("/rx_tune.wav");
          audio.volume = 0.9;
          audio.play().catch(() => {});
        } catch (_) {}
        newUnheard.forEach((n) => soundedIdsRef.current.add(String(n.id)));
        persistSoundedIds(soundedIdsRef.current);
      }
      setNotifications(list.slice(0, 100));
    } catch (_) {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) {
      setNotifications([]);
      return undefined;
    }
    fetchNotifications();
    pollRef.current = window.setInterval(fetchNotifications, 5000);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [token, apiBase]);

  const markRead = async (notificationId) => {
    if (!token) return;
    try {
      await fetch(`${apiBase}/notifications/${notificationId}/read`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotifications((prev) => prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n)));
    } catch (_) {}
  };

  const markAllRead = async () => {
    if (!token) return;
    try {
      await fetch(`${apiBase}/notifications/read-all`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (_) {}
  };

  const unreadCount = useMemo(() => notifications.filter((n) => !n.is_read).length, [notifications]);

  const value = useMemo(
    () => ({
      notifications,
      unreadCount,
      loading,
      fetchNotifications,
      markRead,
      markAllRead,
    }),
    [notifications, unreadCount, loading],
  );

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications must be used within NotificationProvider");
  return ctx;
}
