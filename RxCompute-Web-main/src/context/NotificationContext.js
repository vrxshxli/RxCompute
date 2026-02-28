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
  const audioUnlockedRef = useRef(false);
  const pendingAnnounceRef = useRef([]);

  const announceUnheard = (newUnheard) => {
    if (!newUnheard || newUnheard.length === 0) return;
    try {
      const hasSafety = newUnheard.some((n) => String(n.type || "").toLowerCase() === "safety");
      const playTone = () => {
        const audio = new Audio("/rx_tune.wav");
        audio.volume = hasSafety ? 1.0 : 0.9;
        audio.play().catch(() => {});
      };
      playTone();
      if (hasSafety) {
        window.setTimeout(playTone, 900);
        const safetyNote = newUnheard.find((n) => String(n.type || "").toLowerCase() === "safety");
        if (window.speechSynthesis && safetyNote) {
          window.speechSynthesis.cancel();
          const text = `${safetyNote.title || ""} ${safetyNote.body || ""}`.toLowerCase();
          const prefix = text.includes("scheduler") ? "Scheduler agent alert." : "Safety alert.";
          const msg = new SpeechSynthesisUtterance(`${prefix} ${safetyNote.title || ""}. ${safetyNote.body || ""}`);
          msg.rate = 0.95;
          msg.pitch = 1.0;
          window.speechSynthesis.speak(msg);
        }
      }
    } catch (_) {}
  };

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
        if (audioUnlockedRef.current) {
          announceUnheard(newUnheard);
        } else {
          pendingAnnounceRef.current = [...pendingAnnounceRef.current, ...newUnheard].slice(-25);
        }
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
    pollRef.current = window.setInterval(fetchNotifications, 12000);
    const onFocus = () => fetchNotifications();
    const onVisibility = () => {
      if (document.visibilityState === "visible") fetchNotifications();
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [token, apiBase]);

  useEffect(() => {
    const unlock = () => {
      if (audioUnlockedRef.current) return;
      audioUnlockedRef.current = true;
      try {
        const beep = new Audio("/rx_tune.wav");
        beep.volume = 0.01;
        beep.play().then(() => {
          beep.pause();
          beep.currentTime = 0;
        }).catch(() => {});
      } catch (_) {}
      if (pendingAnnounceRef.current.length > 0) {
        announceUnheard(pendingAnnounceRef.current);
        pendingAnnounceRef.current = [];
      }
    };
    window.addEventListener("click", unlock, { passive: true });
    window.addEventListener("keydown", unlock, { passive: true });
    window.addEventListener("touchstart", unlock, { passive: true });
    return () => {
      window.removeEventListener("click", unlock);
      window.removeEventListener("keydown", unlock);
      window.removeEventListener("touchstart", unlock);
    };
  }, []);

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
