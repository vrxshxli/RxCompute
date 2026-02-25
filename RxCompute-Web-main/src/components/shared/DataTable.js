import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, Database } from 'lucide-react';
import T from '../../utils/tokens';

export default function DataTable({ columns, data, onRowClick, highlightFn }) {
  const [sortCol, setSortCol] = useState(null);
  const [sortDir, setSortDir] = useState("asc");

  const sorted = useMemo(() => {
    if (!sortCol) return data;
    return [...data].sort((a, b) => {
      const av = a[sortCol], bv = b[sortCol];
      if (typeof av === "number") return sortDir === "asc" ? av - bv : bv - av;
      return sortDir === "asc" ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
  }, [data, sortCol, sortDir]);

  const toggleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortCol(col); setSortDir("asc"); }
  };

  return (
    <div style={{ background: T.white, border: `1px solid ${T.gray200}`, borderRadius: 10, overflow: "hidden" }}>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: T.gray50 }}>
              {columns.map(col => (
                <th key={col.key} onClick={() => col.sortable !== false && toggleSort(col.key)}
                  style={{
                    padding: "11px 16px", textAlign: col.align || "left",
                    color: T.gray600, fontSize: 11, fontWeight: 600,
                    textTransform: "uppercase", letterSpacing: 0.6,
                    borderBottom: `1px solid ${T.gray200}`,
                    cursor: col.sortable !== false ? "pointer" : "default",
                    whiteSpace: "nowrap", userSelect: "none",
                  }}>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                    {col.label}
                    {sortCol === col.key && (sortDir === "asc" ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <tr key={i} onClick={() => onRowClick?.(row)}
                style={{
                  cursor: onRowClick ? "pointer" : "default",
                  borderLeft: highlightFn?.(row) ? `3px solid ${T.red}` : "3px solid transparent",
                  transition: "background 0.1s",
                }}
                onMouseEnter={e => e.currentTarget.style.background = T.gray50}
                onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                {columns.map(col => (
                  <td key={col.key} style={{ padding: "11px 16px", borderBottom: `1px solid ${T.gray100}`, color: T.gray700, textAlign: col.align || "left" }}>
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {sorted.length === 0 && (
        <div style={{ textAlign: "center", padding: "60px 20px", color: T.gray400 }}>
          <Database size={48} strokeWidth={1} />
          <div style={{ fontSize: 16, fontWeight: 600, color: T.gray600, marginTop: 16 }}>No data found</div>
        </div>
      )}
    </div>
  );
}