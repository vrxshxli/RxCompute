import React, { useEffect, useState } from 'react';
import T from '../../utils/tokens';
import { Btn, PageHeader } from '../../components/shared';
import { MapPin, LocateFixed } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function AdminProfile() {
  const { token, apiBase, user, refreshUserFromProfile } = useAuth();
  const [form, setForm] = useState({
    name: "",
    email: "",
    location_text: "",
    location_lat: "",
    location_lng: "",
  });
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);
  const [msg, setMsg] = useState("");

  const load = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${apiBase}/users/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setForm({
        name: data.name || user?.name || "",
        email: data.email || "",
        location_text: data.location_text || "",
        location_lat: data.location_lat ?? "",
        location_lng: data.location_lng ?? "",
      });
    } catch (_) {}
  };

  useEffect(() => {
    load();
  }, [token, apiBase]);

  const autoFetchLocation = async () => {
    if (!navigator.geolocation) {
      setMsg("Geolocation not supported on this browser");
      return;
    }
    setLocating(true);
    setMsg("");
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        let label = "";
        try {
          const rev = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`);
          if (rev.ok) {
            const data = await rev.json();
            label = data?.display_name || "";
          }
        } catch (_) {}
        setForm((prev) => ({
          ...prev,
          location_lat: Number(lat).toFixed(6),
          location_lng: Number(lng).toFixed(6),
          location_text: label || prev.location_text,
        }));
        setLocating(false);
      },
      () => {
        setLocating(false);
        setMsg("Location permission denied");
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

  const saveProfile = async () => {
    if (!token) return;
    setSaving(true);
    setMsg("");
    try {
      const res = await fetch(`${apiBase}/users/me`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: form.name || null,
          email: form.email || null,
          location_text: form.location_text || null,
          location_lat: form.location_lat === "" ? null : Number(form.location_lat),
          location_lng: form.location_lng === "" ? null : Number(form.location_lng),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMsg(data?.detail || "Unable to save profile");
      } else {
        await refreshUserFromProfile();
        setMsg("Profile saved");
      }
    } catch (_) {
      setMsg("Network error while saving");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <PageHeader title="Admin Profile" subtitle="Manage your account and location" />
      <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 18, maxWidth: 900 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
          <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Email" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
          <input value={form.location_text} onChange={(e) => setForm({ ...form, location_text: e.target.value })} placeholder="Location address" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8, gridColumn: "span 2" }} />
          <input value={form.location_lat} onChange={(e) => setForm({ ...form, location_lat: e.target.value })} placeholder="Latitude" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
          <input value={form.location_lng} onChange={(e) => setForm({ ...form, location_lng: e.target.value })} placeholder="Longitude" style={{ padding: 10, border: `1px solid ${T.gray200}`, borderRadius: 8 }} />
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <Btn variant="secondary" size="sm" onClick={autoFetchLocation} disabled={locating}><LocateFixed size={14} />{locating ? "Fetching..." : "Auto Fetch Location"}</Btn>
          <Btn variant="primary" size="sm" onClick={saveProfile} disabled={saving}><MapPin size={14} />{saving ? "Saving..." : "Save Profile"}</Btn>
        </div>
        {msg ? <div style={{ marginTop: 8, fontSize: 12, color: msg === "Profile saved" ? T.green : T.red }}>{msg}</div> : null}
      </div>
    </div>
  );
}
