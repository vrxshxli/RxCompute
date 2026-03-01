import React, { useEffect, useMemo, useState } from "react";
import T from "../../utils/tokens";
import { Btn, PageHeader, SearchInput, StatusPill } from "../../components/shared";
import { useAuth } from "../../context/AuthContext";

const ORDER_UID_RE = /\b(?:ORD|RFL)-\d{8}-[A-Z0-9]+\b/i;

function _toText(value, fallback = "") {
  if (value == null) return fallback;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    const parts = value.map((v) => _toText(v, "")).filter(Boolean);
    return parts.length ? parts.join(" | ") : fallback;
  }
  if (typeof value === "object") {
    if (value.msg) return String(value.msg);
    try {
      return JSON.stringify(value);
    } catch (_) {
      return fallback;
    }
  }
  return fallback;
}

function _deriveStatus(title, body, phase) {
  const txt = `${_toText(title)} ${_toText(body)} ${_toText(phase)}`.toLowerCase();
  if (txt.includes("blocked") || txt.includes("rejected") || txt.includes("cancelled")) return "blocked";
  if (txt.includes("warning") || txt.includes("review") || txt.includes("hold")) return "warning";
  if (txt.includes("delivered") || txt.includes("complete") || txt.includes("verified")) return "success";
  return "running";
}

function _extractOrderUid(row) {
  const meta = row?.metadata || {};
  const explicit = _toText(meta.order_uid).trim();
  if (explicit) return explicit;
  const hit = `${_toText(row?.title)} ${_toText(row?.body)}`.match(ORDER_UID_RE);
  return hit ? hit[0] : "";
}

export default function AdminSafetyEvents() {
  const { token, apiBase } = useAuth();
  const [search, setSearch] = useState("");
  const [agentFilter, setAgentFilter] = useState("all");
  const [traceRows, setTraceRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [onlyOpen, setOnlyOpen] = useState(false);
  const [agentOptions, setAgentOptions] = useState([]);

  const load = async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const allItems = [];
      const discovered = new Set();
      const maxPages = 12;
      for (let page = 1; page <= maxPages; page += 1) {
        const qs = new URLSearchParams();
        qs.set("page", String(page));
        qs.set("page_size", "100");
        if (agentFilter && agentFilter !== "all") qs.set("agent_name", agentFilter);
        if (search.trim()) qs.set("search", search.trim());
        const res = await fetch(`${apiBase}/notifications/agent-traces?${qs.toString()}`, { headers });
        const data = await res.json();
        if (!res.ok) {
          setTraceRows([]);
          setAgentOptions([]);
          setError(_toText(data?.detail, "Unable to load agent workflow"));
          return;
        }
        const items = Array.isArray(data?.items) ? data.items : [];
        for (const it of items) allItems.push(it);
        const opts = Array.isArray(data?.agent_options) ? data.agent_options : [];
        for (const opt of opts) discovered.add(_toText(opt));
        if (!data?.has_next || items.length === 0) break;
      }
      setTraceRows(allItems);
      setAgentOptions(Array.from(discovered).filter(Boolean));
    } catch (_) {
      setTraceRows([]);
      setAgentOptions([]);
      setError("Network error while loading workflow");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [token, apiBase, agentFilter]);

  useEffect(() => {
    const id = setInterval(() => load(), 10000);
    return () => clearInterval(id);
  }, [token, apiBase, agentFilter]);

  const workflows = useMemo(() => {
    const byTask = new Map();
    for (const r of traceRows) {
      const meta = r?.metadata || {};
      const orderUid = _extractOrderUid(r);
      const userId = meta.target_user_id || r.target_user_id || "unknown";
      const taskKey = orderUid || `TASK-U${userId}`;
      const step = {
        id: r.id,
        created_at: r.created_at,
        agent_name: _toText(r.agent_name || meta.agent_name, "agent"),
        phase: _toText(meta.phase, "step"),
        title: _toText(r.title),
        body: _toText(r.body),
        status: _deriveStatus(r.title, r.body, meta.phase),
        data_fetch_from: Array.isArray(meta.data_fetch_from) ? meta.data_fetch_from : [],
        data_passed_to: Array.isArray(meta.data_passed_to) ? meta.data_passed_to : [],
        langfuse_trace: meta.langfuse_trace || null,
      };
      const row = byTask.get(taskKey) || {
        key: taskKey,
        order_uid: orderUid,
        target_user_id: userId,
        target_user_name: _toText(r.target_user_name || r.target_user_email, userId !== "unknown" ? `User #${userId}` : "-"),
        steps: [],
      };
      row.steps.push(step);
      byTask.set(taskKey, row);
    }

    const arr = Array.from(byTask.values()).map((w) => {
      w.steps.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      const latest = w.steps[w.steps.length - 1];
      w.latest_status = latest?.status || "running";
      w.last_at = latest?.created_at;
      return w;
    });
    arr.sort((a, b) => new Date(b.last_at || 0) - new Date(a.last_at || 0));
    return onlyOpen ? arr.filter((w) => !["success", "blocked"].includes(w.latest_status)) : arr;
  }, [traceRows, onlyOpen]);

  const counts = useMemo(() => {
    const blocked = workflows.filter((w) => w.latest_status === "blocked").length;
    const running = workflows.filter((w) => w.latest_status === "running").length;
    const warning = workflows.filter((w) => w.latest_status === "warning").length;
    const success = workflows.filter((w) => w.latest_status === "success").length;
    return { blocked, running, warning, success, total: workflows.length };
  }, [workflows]);

  return (
    <div>
      <PageHeader
        title="Agent Workflow"
        subtitle="Order/task-wise execution timeline as agents run"
        badge={`${counts.total} tasks`}
        actions={<Btn variant="secondary" size="sm" onClick={load}>{loading ? "Refreshing..." : "Refresh"}</Btn>}
      />
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12, flexWrap: "wrap" }}>
        <SearchInput value={search} onChange={setSearch} placeholder="Search by order id / user / trace text..." />
        <Btn variant="secondary" size="sm" onClick={load}>Apply</Btn>
        <select
          value={agentFilter}
          onChange={(e) => setAgentFilter(e.target.value)}
          style={{ padding: "8px 10px", border: `1px solid ${T.gray200}`, borderRadius: 8, fontSize: 12 }}
        >
          <option value="all">All agents</option>
          {agentOptions.map((a, idx) => {
            const txt = _toText(a, "");
            if (!txt) return null;
            return <option key={`${txt}-${idx}`} value={txt}>{txt}</option>;
          })}
        </select>
        <button
          onClick={() => setOnlyOpen((v) => !v)}
          style={{
            padding: "7px 12px",
            borderRadius: 8,
            border: `1px solid ${onlyOpen ? T.blue : T.gray200}`,
            background: onlyOpen ? `${T.blue}10` : T.white,
            color: onlyOpen ? T.blue : T.gray600,
            fontSize: 12,
            cursor: "pointer",
          }}
        >
          {onlyOpen ? "Showing Open Only" : "Show Open Only"}
        </button>
        <div style={{ display: "flex", gap: 8, marginLeft: "auto", flexWrap: "wrap" }}>
          <span style={{ fontSize: 11, color: T.gray500 }}>Running {counts.running}</span>
          <span style={{ fontSize: 11, color: T.yellow }}>Warning {counts.warning}</span>
          <span style={{ fontSize: 11, color: T.green }}>Done {counts.success}</span>
          <span style={{ fontSize: 11, color: T.red }}>Blocked {counts.blocked}</span>
        </div>
      </div>
      {error ? <div style={{ color: T.red, fontSize: 12, marginBottom: 10 }}>{error}</div> : null}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {workflows.length === 0 ? (
          <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 10, padding: 14, color: T.gray500, fontSize: 12 }}>
            No workflow entries found yet. Trigger an order/refill/safety flow first.
          </div>
        ) : (
          workflows.map((w) => (
            <div key={w.key} style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 12, padding: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, marginBottom: 10 }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: T.gray900 }}>
                    {w.order_uid || w.key}
                  </div>
                  <div style={{ fontSize: 11, color: T.gray500 }}>
                    Target: {w.target_user_name}
                  </div>
                </div>
                <StatusPill
                  status={
                    w.latest_status === "blocked"
                      ? "cancelled"
                      : w.latest_status === "warning"
                          ? "pending"
                          : w.latest_status === "success"
                              ? "delivered"
                              : "picking"
                  }
                  size="xs"
                />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {w.steps.map((s, idx) => {
                  const dot =
                    s.status === "blocked" ? T.red : s.status === "warning" ? T.yellow : s.status === "success" ? T.green : T.blue;
                  return (
                    <div key={s.id} style={{ display: "grid", gridTemplateColumns: "18px 1fr auto", gap: 10, alignItems: "start" }}>
                      <div style={{ marginTop: 3 }}>
                        <div style={{ width: 10, height: 10, borderRadius: 99, background: dot }} />
                        {idx < w.steps.length - 1 ? <div style={{ width: 2, height: 22, background: T.gray200, margin: "4px 0 0 4px" }} /> : null}
                      </div>
                      <div>
                        <div style={{ fontSize: 12, color: T.gray900, fontWeight: 600 }}>
                          {s.agent_name} · {s.phase}
                        </div>
                        <div style={{ fontSize: 11, color: T.gray600, marginTop: 2 }}>
                          {s.title} — {s.body}
                        </div>
                        {(s.data_fetch_from.length || s.data_passed_to.length) ? (
                          <div style={{ fontSize: 10, color: T.gray500, marginTop: 4, lineHeight: 1.5 }}>
                            Fetch: {s.data_fetch_from.length ? s.data_fetch_from.join(" · ") : "-"}<br />
                            Pass: {s.data_passed_to.length ? s.data_passed_to.join(" · ") : "-"}<br />
                            Langfuse: {s.langfuse_trace?.enabled ? "Enabled" : "Metadata-only"}{s.langfuse_trace?.span_entry ? ` (${s.langfuse_trace.span_entry})` : ""}
                          </div>
                        ) : null}
                      </div>
                      <div style={{ fontSize: 10, color: T.gray400, fontFamily: "monospace" }}>
                        {new Date(s.created_at).toLocaleTimeString()}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
