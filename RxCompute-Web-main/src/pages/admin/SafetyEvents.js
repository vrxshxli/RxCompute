import React, { useEffect, useMemo, useState } from "react";
import T from "../../utils/tokens";
import { Btn, PageHeader, SearchInput, StatusPill } from "../../components/shared";
import { useAuth } from "../../context/AuthContext";

export default function AdminSafetyEvents() {
  const { token, apiBase } = useAuth();
  const [severity, setSeverity] = useState("all");
  const [search, setSearch] = useState("");
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const qs = new URLSearchParams();
      qs.set("severity", severity);
      if (search.trim()) qs.set("search", search.trim());
      qs.set("limit", "200");
      const res = await fetch(`${apiBase}/notifications/safety-events?${qs.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.detail || "Unable to load safety events");
      } else {
        setEvents(Array.isArray(data) ? data : []);
      }
    } catch (_) {
      setError("Network error while loading safety events");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [token, apiBase, severity]);

  const counts = useMemo(() => {
    const blocked = events.filter((e) => e.severity === "blocked").length;
    const warning = events.filter((e) => e.severity === "warning").length;
    return { blocked, warning, total: events.length };
  }, [events]);

  return (
    <div>
      <PageHeader
        title="Safety Events"
        badge={`${counts.total} events`}
        actions={<Btn variant="secondary" size="sm" onClick={load}>{loading ? "Refreshing..." : "Refresh"}</Btn>}
      />
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12, flexWrap: "wrap" }}>
        <SearchInput value={search} onChange={setSearch} placeholder="Search title/body/user..." />
        <Btn variant="secondary" size="sm" onClick={load}>Apply</Btn>
        <div style={{ display: "flex", gap: 8 }}>
          {["all", "blocked", "warning"].map((s) => (
            <button
              key={s}
              onClick={() => setSeverity(s)}
              style={{
                padding: "7px 12px",
                borderRadius: 8,
                border: `1px solid ${severity === s ? T.blue : T.gray200}`,
                background: severity === s ? `${T.blue}10` : T.white,
                color: severity === s ? T.blue : T.gray600,
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              {s === "all" ? "All" : s === "blocked" ? `Blocked (${counts.blocked})` : `Warning (${counts.warning})`}
            </button>
          ))}
        </div>
      </div>
      {error ? <div style={{ color: T.red, fontSize: 12, marginBottom: 10 }}>{error}</div> : null}
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {events.length === 0 ? (
          <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 10, padding: 14, color: T.gray500, fontSize: 12 }}>
            No safety events found for selected filter.
          </div>
        ) : (
          events.map((e) => (
            <div key={e.id} style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 10, padding: 14, borderLeft: `4px solid ${e.severity === "blocked" ? T.red : e.severity === "warning" ? T.yellow : T.blue}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, marginBottom: 6, alignItems: "center" }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: T.gray900 }}>{e.title}</div>
                <StatusPill status={e.severity === "blocked" ? "cancelled" : e.severity === "warning" ? "pending" : "verified"} size="xs" />
              </div>
              <div style={{ fontSize: 12, color: T.gray700, marginBottom: 8 }}>{e.body}</div>
              <div style={{ fontSize: 11, color: T.gray500 }}>
                User: {(e.user_name || e.user_email || `User #${e.user_id}`)} · Role: {e.user_role || "-"} · {new Date(e.created_at).toLocaleString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
