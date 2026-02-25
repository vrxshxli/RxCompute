import React from 'react';
import T from '../../utils/tokens';

const STATUS_MAP = {
  delivered: { bg: `${T.green}18`, color: T.green, label: "Delivered" },
  confirmed: { bg: `${T.blue}18`, color: T.blue, label: "Confirmed" },
  pending: { bg: `${T.yellow}18`, color: T.yellow, label: "Pending" },
  cancelled: { bg: `${T.red}18`, color: T.red, label: "Cancelled" },
  dispatched: { bg: `${T.green}18`, color: T.green, label: "Dispatched" },
  packed: { bg: `${T.blue}18`, color: T.blue, label: "Packed" },
  picking: { bg: `${T.yellow}18`, color: T.yellow, label: "Picking" },
  pharmacy_verified: { bg: `${T.green}18`, color: T.green, label: "Verified" },
  high: { bg: `${T.red}18`, color: T.red, label: "High" },
  medium: { bg: `${T.yellow}18`, color: T.yellow, label: "Medium" },
  low: { bg: `${T.green}18`, color: T.green, label: "Low" },
  overdue: { bg: `${T.red}18`, color: T.red, label: "Overdue" },
  notified: { bg: `${T.blue}18`, color: T.blue, label: "Notified" },
  declined: { bg: `${T.gray400}18`, color: T.gray400, label: "Declined" },
  block: { bg: `${T.red}18`, color: T.red, label: "Block" },
  warn: { bg: `${T.yellow}18`, color: T.yellow, label: "Warn" },
  escalate: { bg: `${T.blue}18`, color: T.blue, label: "Escalate" },
  allow: { bg: `${T.green}18`, color: T.green, label: "Allow" },
};

export default function StatusPill({ status, size = "sm" }) {
  const m = STATUS_MAP[status] || { bg: `${T.gray400}18`, color: T.gray400, label: status };
  return (
    <span style={{
      background: m.bg, color: m.color,
      padding: size === "xs" ? "2px 7px" : "3px 10px",
      borderRadius: 4, fontSize: size === "xs" ? 10 : 11,
      fontWeight: 600, letterSpacing: 0.3,
      textTransform: "uppercase", whiteSpace: "nowrap",
    }}>
      {m.label}
    </span>
  );
}