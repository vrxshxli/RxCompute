import React, { useState } from 'react';
import T from '../../utils/tokens';
import { StatusPill, AgentBadge } from '../../components/shared';
import {
  ShoppingCart, Bell, Package, Zap, Activity,
  ArrowUpRight, Shield, TrendingUp, Clock,
  CheckCircle, AlertTriangle, ExternalLink, Users
} from 'lucide-react';
import { ORDERS, MEDICINES, REFILL_ALERTS, AGENT_LOGS } from '../../data/mockData';
import { useAuth } from '../../context/AuthContext';

export default function AdminDashboard() {
  const { user } = useAuth();
  const firstName = user?.name?.split(' ')[0] || 'Admin';
  const pendingAlerts = REFILL_ALERTS.filter(a => a.status === 'pending').length;
  const lowStock = MEDICINES.filter(m => m.stock <= 30).length;
  const criticalStock = MEDICINES.filter(m => m.stock <= 10).length;
  const healthyPct = Math.round((MEDICINES.filter(m => m.stock > 30).length / MEDICINES.length) * 100);
  const blockedCount = AGENT_LOGS.filter(l => l.action.includes('BLOCKED')).length;

  /* palette — strictly blue + orange + white */
  const B = '#1A6BB5';   /* brand blue */
  const O = '#E8572A';   /* brand orange */

  return (
    <div style={{
      padding: 0, margin: -24, minHeight: '100vh',
      background: 'linear-gradient(135deg, #EBF4FC 0%, #F0F4FF 40%, #FFF5F0 100%)',
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    }}>
      <style>{`
        @keyframes pulse2 { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(1.4)} }
        @keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
        .glass {
          background: rgba(255,255,255,0.65);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border: 1px solid rgba(255,255,255,0.8);
          border-radius: 20px;
          transition: transform 0.25s ease, box-shadow 0.25s ease;
        }
        .glass:hover {
          transform: translateY(-3px);
          box-shadow: 0 12px 40px rgba(26,107,181,0.08);
        }
        .glass-static {
          background: rgba(255,255,255,0.65);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border: 1px solid rgba(255,255,255,0.8);
          border-radius: 20px;
        }
      `}</style>

      <div style={{ padding: 'clamp(24px,4vw,40px)' }}>

        {/* ─── WELCOME HEADER ─── */}
        <div style={{ marginBottom: 36, animation: 'fadeUp .5s ease both' }}>
          <p style={{ fontSize: 16, color: B, fontWeight: 500, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
            Welcome back, {firstName} <span style={{ fontSize: 20 }}>👋</span>
          </p>
          <h1 style={{ fontSize: 'clamp(32px,5vw,44px)', fontWeight: 800, color: '#111827', letterSpacing: -0.5, margin: 0 }}>
            Dashboard
          </h1>
        </div>

        {/* ─── TOP ROW: Next Action Card + Agent Stats ─── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 24, marginBottom: 24, animation: 'fadeUp .5s ease .1s both' }}>

          {/* Next action card (like "Next game") */}
          <div className="glass" style={{ padding: 28, position: 'relative', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <span style={{ fontSize: 18, fontWeight: 700, color: '#111827' }}>Priority Actions</span>
              <span style={{ fontSize: 13, color: B, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>View all <ArrowUpRight size={14} /></span>
            </div>

            <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
              {/* Urgent alert */}
              <div style={{ flex: 1, background: `${O}08`, border: `1px solid ${O}20`, borderRadius: 14, padding: 18, display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ width: 48, height: 48, borderRadius: '50%', background: `${O}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <AlertTriangle size={22} color={O} />
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>{pendingAlerts} Refill Alerts</div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>Patients need medication refills</div>
                </div>
              </div>

              {/* Low stock */}
              <div style={{ flex: 1, background: `${B}06`, border: `1px solid ${B}15`, borderRadius: 14, padding: 18, display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ width: 48, height: 48, borderRadius: '50%', background: `${B}12`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Package size={22} color={B} />
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>{criticalStock} Critical Stock</div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>{lowStock} items running low</div>
                </div>
              </div>
            </div>
          </div>

          {/* Agent statistic card (like "Games statistic") */}
          <div className="glass" style={{ padding: 28 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <span style={{ fontSize: 18, fontWeight: 700, color: '#111827' }}>Agent Statistics</span>
              <span style={{ fontSize: 13, color: B, fontWeight: 600, cursor: 'pointer' }}>View all</span>
            </div>

            {/* Progress bar */}
            <div style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', height: 10, borderRadius: 5, overflow: 'hidden', background: '#e5e7eb' }}>
                <div style={{ width: '70%', background: B, borderRadius: 5 }} />
                <div style={{ width: '15%', background: O }} />
                <div style={{ width: '15%', background: '#e5e7eb' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
                <span style={{ fontSize: 11, color: B, fontWeight: 600 }}>● Approved 70%</span>
                <span style={{ fontSize: 11, color: O, fontWeight: 600 }}>● Blocked 15%</span>
                <span style={{ fontSize: 11, color: '#9ca3af', fontWeight: 600 }}>● Pending 15%</span>
              </div>
            </div>

            {/* Stat numbers row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, textAlign: 'center' }}>
              {[
                { l: 'TOTAL', v: AGENT_LOGS.length },
                { l: 'APPROVED', v: AGENT_LOGS.length - blockedCount - 4 },
                { l: 'BLOCKED', v: blockedCount },
                { l: 'PENDING', v: 4 },
              ].map(s => (
                <div key={s.l} style={{ borderRight: s.l !== 'PENDING' ? '1px solid #e5e7eb' : 'none', padding: '4px 0' }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: '#9ca3af', letterSpacing: 0.5, marginBottom: 4 }}>{s.l}</div>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#111827' }}>{s.v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ─── MIDDLE ROW: Orders list + 4 stat circles ─── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 24, marginBottom: 24, animation: 'fadeUp .5s ease .2s both' }}>

          {/* Recent Orders (like "Standings") */}
          <div className="glass-static" style={{ overflow: 'hidden' }}>
            <div style={{ padding: '20px 28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 18, fontWeight: 700, color: '#111827' }}>Recent Orders</span>
              <span style={{ fontSize: 13, color: B, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>View all <ArrowUpRight size={14} /></span>
            </div>

            {/* Column headers */}
            <div style={{ display: 'grid', gridTemplateColumns: '28px 1.2fr 0.8fr 0.6fr 0.5fr 0.6fr', gap: 8, padding: '10px 28px', fontSize: 11, fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: 0.5, borderBottom: '1px solid #e5e7eb' }}>
              <span>#</span><span>PATIENT</span><span>ITEMS</span><span>TOTAL</span><span>NODE</span><span>STATUS</span>
            </div>

            {/* Order rows */}
            {ORDERS.slice(0, 8).map((o, i) => (
              <div key={o.order_id} style={{
                display: 'grid', gridTemplateColumns: '28px 1.2fr 0.8fr 0.6fr 0.5fr 0.6fr',
                gap: 8, padding: '14px 28px', alignItems: 'center',
                borderBottom: i < 7 ? '1px solid rgba(0,0,0,0.04)' : 'none',
                transition: 'background .15s',
                cursor: 'pointer',
              }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(26,107,181,0.03)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <span style={{ fontSize: 14, fontWeight: 700, color: '#9ca3af' }}>{i + 1}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ width: 32, height: 32, borderRadius: '50%', background: `${B}12`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: B, flexShrink: 0 }}>
                    {o.patient_name?.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: '#111827' }}>{o.patient_name}</div>
                    <div style={{ fontSize: 11, color: '#9ca3af', fontFamily: 'monospace' }}>{o.order_id.slice(-7)}</div>
                  </div>
                </div>
                <span style={{ fontSize: 13, color: '#6b7280' }}>{o.items.length} item{o.items.length > 1 ? 's' : ''}</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>€{o.total_price.toFixed(0)}</span>
                <span style={{ fontSize: 12, color: '#9ca3af', fontFamily: 'monospace' }}>{o.pharmacy_node}</span>
                <StatusPill status={o.status} size="xs" />
              </div>
            ))}
          </div>

          {/* Right column: 4 circular stat cards + CTA */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* 2x2 stat grid (like Possession, Overall Price, etc.) */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {[
                { icon: ShoppingCart, label: 'ORDERS TODAY', value: '47', sub: '+12.3%', color: B, bg: `${B}08` },
                { icon: TrendingUp, label: 'INVENTORY HEALTH', value: `${healthyPct}%`, sub: `${52 - lowStock}/52 stocked`, color: O, bg: `${O}06` },
                { icon: Users, label: 'ACTIVE PATIENTS', value: '36', sub: 'All registered', color: B, bg: `${B}08` },
                { icon: Zap, label: 'AGENT ACTIONS', value: String(AGENT_LOGS.length), sub: 'Last 24 hours', color: O, bg: `${O}06` },
              ].map(s => (
                <div key={s.label} className="glass" style={{ padding: 22, textAlign: 'center' }}>
                  <div style={{ width: 52, height: 52, borderRadius: '50%', background: s.bg, border: `2px solid ${s.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
                    <s.icon size={22} color={s.color} />
                  </div>
                  <div style={{ fontSize: 10, fontWeight: 700, color: '#9ca3af', letterSpacing: 0.8, textTransform: 'uppercase', marginBottom: 4 }}>{s.label}</div>
                  <div style={{ fontSize: 28, fontWeight: 800, color: '#111827', lineHeight: 1 }}>{s.value}</div>
                  <div style={{ fontSize: 12, color: s.color, fontWeight: 500, marginTop: 4 }}>{s.sub}</div>
                </div>
              ))}
            </div>

            {/* CTA Banner (like "Setup training for next week") */}
            <div style={{
              background: `linear-gradient(135deg, ${B}, ${B}dd)`,
              borderRadius: 20, padding: 28, color: 'white', position: 'relative', overflow: 'hidden', flex: 1,
              display: 'flex', flexDirection: 'column', justifyContent: 'center',
            }}>
              {/* Decorative circles */}
              <div style={{ position: 'absolute', top: -20, right: -20, width: 100, height: 100, borderRadius: '50%', background: 'rgba(255,255,255,0.1)' }} />
              <div style={{ position: 'absolute', bottom: -30, right: 40, width: 70, height: 70, borderRadius: '50%', background: 'rgba(255,255,255,0.08)' }} />
              <div style={{ position: 'absolute', top: 20, right: 60, width: 40, height: 40, borderRadius: '50%', background: `${O}40` }} />

              <div style={{ position: 'relative', zIndex: 1 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.7)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Don't Forget</div>
                <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1.3, marginBottom: 16 }}>
                  Review Langfuse<br />agent traces
                </div>
                <button style={{
                  display: 'inline-flex', alignItems: 'center', gap: 8,
                  background: 'rgba(255,255,255,0.2)', backdropFilter: 'blur(8px)',
                  border: '1px solid rgba(255,255,255,0.3)', borderRadius: 10,
                  padding: '10px 20px', color: 'white', fontSize: 13, fontWeight: 600,
                  cursor: 'pointer',
                }}>
                  <ExternalLink size={14} /> Open Langfuse
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ─── BOTTOM: Live Agent Activity ─── */}
        <div className="glass-static" style={{ overflow: 'hidden', animation: 'fadeUp .5s ease .3s both' }}>
          <div style={{ padding: '20px 28px', display: 'flex', alignItems: 'center', gap: 12 }}>
            <Activity size={18} color={B} />
            <span style={{ fontSize: 18, fontWeight: 700, color: '#111827' }}>Live Agent Activity</span>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981', animation: 'pulse2 2.4s infinite', boxShadow: '0 0 0 4px rgba(16,185,129,0.15)' }} />
            <span style={{ fontSize: 12, color: '#9ca3af', marginLeft: 'auto' }}>Auto-updating</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 12, padding: '8px 28px 24px' }}>
            {AGENT_LOGS.slice(0, 9).map(log => {
              const isBlocked = log.action.includes('BLOCKED');
              const isCreated = log.action.includes('Created');
              const dotColor = isBlocked ? '#dc2626' : isCreated ? '#10b981' : B;

              return (
                <div key={log.id} style={{
                  display: 'flex', gap: 14, padding: 16,
                  background: isBlocked ? 'rgba(220,38,38,0.03)' : 'rgba(255,255,255,0.5)',
                  borderRadius: 14, border: `1px solid ${isBlocked ? 'rgba(220,38,38,0.12)' : 'rgba(0,0,0,0.04)'}`,
                  alignItems: 'flex-start',
                }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: dotColor, marginTop: 5, flexShrink: 0, boxShadow: `0 0 0 3px ${dotColor}20` }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <AgentBadge agent={log.agent_name} />
                      <span style={{ fontSize: 11, color: '#9ca3af', fontFamily: 'monospace', marginLeft: 'auto', flexShrink: 0 }}>
                        {new Date(log.created_at).toLocaleTimeString('en-GB', { hour12: false })}
                      </span>
                    </div>
                    <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.5, fontWeight: 500 }}>{log.action}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}