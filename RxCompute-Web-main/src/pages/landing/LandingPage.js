import React from 'react';
import { Sparkles, ArrowRight, MessageCircle, ShieldCheck, BellRing, Database, Activity, Layers, LayoutGrid, Building2, Warehouse } from 'lucide-react';
import { Logo } from '../../components/shared';
import T from '../../utils/tokens';

function Feature({ icon: Icon, title, desc }) {
  return (
    <div 
      style={{ 
        background: "rgba(255,255,255,0.08)", 
        backdropFilter: "blur(12px)", 
        borderRadius: 20, 
        padding: "32px 28px",
        border: "1px solid rgba(255,255,255,0.12)",
        transition: "all 0.35s ease",
        boxShadow: "0 8px 32px rgba(0,0,0,0.1)",
      }}
      onMouseEnter={e => { 
        e.currentTarget.style.transform = "translateY(-8px) scale(1.02)"; 
        e.currentTarget.style.boxShadow = "0 16px 48px rgba(0,0,0,0.18)";
      }}
      onMouseLeave={e => { 
        e.currentTarget.style.transform = "translateY(0) scale(1)"; 
        e.currentTarget.style.boxShadow = "0 8px 32px rgba(0,0,0,0.1)";
      }}
    >
      <div style={{ 
        width: 56, height: 56, borderRadius: 16, 
        background: "linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.08))", 
        display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 24,
        boxShadow: "inset 0 2px 8px rgba(0,0,0,0.15)"
      }}>
        <Icon size={28} color={T.white} strokeWidth={2.2} />
      </div>
      <h3 style={{ fontSize: 20, fontWeight: 700, color: T.white, marginBottom: 12, letterSpacing: -0.3 }}>{title}</h3>
      <p style={{ fontSize: 15, color: "rgba(255,255,255,0.78)", lineHeight: 1.65, margin: 0 }}>{desc}</p>
    </div>
  );
}

export default function LandingPage({ onGoToLogin }) {
  return (
    <div style={{ 
      minHeight: "100vh", 
      overflowX: "hidden", 
      background: T.white,
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    }}>
      <style>{`
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        section { animation: fadeIn 1.2s ease-out forwards; }
      `}</style>

      <nav style={{ 
        position: "fixed", top: 0, left: 0, right: 0,
        zIndex: 1000, 
        background: "rgba(255,255,255,0.96)", 
        backdropFilter: "blur(16px)", 
        borderBottom: `1px solid ${T.gray200}30`, 
        padding: "0 5vw", 
        height: 72, 
        display: "flex", 
        alignItems: "center", 
        justifyContent: "space-between"
      }}>
        <Logo size="md" />
        <div style={{ display: "flex", alignItems: "center", gap: "clamp(16px, 4vw, 48px)" }}>
          {["Features","Architecture","Team"].map(i => (
            <a key={i} href={"#"+i.toLowerCase()} style={{ 
              textDecoration: "none", color: T.gray700, fontSize: 15, fontWeight: 500,
              transition: "color 0.2s" 
            }}
            onMouseEnter={e=>e.currentTarget.style.color=T.blue}
            onMouseLeave={e=>e.currentTarget.style.color=T.gray700}
            >
              {i}
            </a>
          ))}
          <button 
            onClick={onGoToLogin} 
            style={{ 
              padding: "10px 28px", background: T.blue, color: T.white, border: "none", 
              borderRadius: 10, fontSize: 15, fontWeight: 600, cursor: "pointer",
              boxShadow: `0 4px 16px ${T.blue}40`,
              transition: "all 0.2s"
            }}
            onMouseEnter={e=>e.currentTarget.style.transform="scale(1.04)"}
            onMouseLeave={e=>e.currentTarget.style.transform="scale(1)"}
          >
            Sign In
          </button>
        </div>
      </nav>

      <section style={{ 
        position: "relative", 
        padding: "clamp(120px, 18vh, 160px) 5vw 100px", 
        minHeight: "90vh", 
        display: "flex", 
        alignItems: "center",
        background: T.white
      }}>
        <div style={{ 
          position: "relative", zIndex: 2, 
          maxWidth: 1280, margin: "0 auto", 
          width: "100%", 
          display: "grid", 
          gridTemplateColumns: "1fr minmax(auto, 520px)", 
          gap: "clamp(40px, 8vw, 80px)", 
          alignItems: "center"
        }}>
          {/* Hero left content */}
          <div style={{ animation: "fadeInUp 0.9s ease-out" }}>
            <div style={{ 
              display: "inline-flex", alignItems: "center", gap: 10, 
              background: `${T.blue}12`, border: `1px solid ${T.blue}30`, 
              borderRadius: 999, padding: "8px 20px", marginBottom: 32 
            }}>
              <Sparkles size={16} color={T.blue} />
              <span style={{ fontSize: 13, fontWeight: 700, color: T.blue, letterSpacing: 0.5 }}>HackFusion 3 — Team Corviknight</span>
            </div>

            <h1 style={{ 
              fontSize: "clamp(42px, 7vw, 64px)", fontWeight: 800, 
              color: T.blue, lineHeight: 1.05, marginBottom: 24, letterSpacing: -1.2 
            }}>
              AI-Powered Pharmacy<br/>Management —<br/><span style={{ color: T.orange }}>Safe. Smart. Instant.</span>
            </h1>

            <p style={{ fontSize: "clamp(18px, 2.4vw, 20px)", color: T.gray600, lineHeight: 1.6, maxWidth: 520, marginBottom: 40 }}>
              Conversational ordering, real-time drug safety, predictive refills, multi-agent coordination — built for pharmacies that never compromise.
            </p>

            <button 
              onClick={onGoToLogin} 
              style={{ 
                padding: "16px 40px", background: T.blue, color: T.white, border: "none", 
                borderRadius: 12, fontSize: 17, fontWeight: 700, cursor: "pointer",
                display: "inline-flex", alignItems: "center", gap: 12,
                boxShadow: `0 8px 32px ${T.blue}50`,
                transition: "all 0.25s"
              }}
              onMouseEnter={e=> {e.currentTarget.style.transform="translateY(-3px)"; e.currentTarget.style.boxShadow=`0 12px 40px ${T.blue}60`;}}
              onMouseLeave={e=> {e.currentTarget.style.transform="translateY(0)"; e.currentTarget.style.boxShadow=`0 8px 32px ${T.blue}50`;}}
            >
              Launch Dashboard <ArrowRight size={20} />
            </button>

            <div style={{ 
              display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", 
              gap: "clamp(16px, 4vw, 40px)", marginTop: 56, paddingTop: 40, 
              borderTop: `1px solid ${T.gray200}`
            }}>
              {[
                ["52+", "Medicines"],
                ["36+", "Patients"],
                ["6", "AI Agents"],
                ["<2s", "Avg Response"]
              ].map(([v, l]) => (
                <div key={l} style={{ textAlign: "center" }}>
                  <div style={{ fontSize: "clamp(36px, 6vw, 52px)", fontWeight: 800, color: T.orange, lineHeight: 1 }}>{v}</div>
                  <div style={{ fontSize: 15, color: T.gray500, marginTop: 6, fontWeight: 500 }}>{l}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Hero image */}
          <div style={{
            position: "relative",
            height: "clamp(380px, 55vw, 580px)",
            animation: "fadeInUp 1.1s ease-out 0.2s both",
            borderRadius: 24,
            overflow: "hidden",
            background: "#ffffff",
            boxShadow: "none"
          }}>
            <img
              src="/images/hero-ai-pharmacy.jpeg"
              alt="AI Pharmacy Dashboard"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: "center",
                borderRadius: 24,
              }}
            />
          </div>
        </div>
      </section>

      <section id="features" style={{ padding: "clamp(80px, 12vh, 120px) 5vw", background: `linear-gradient(135deg, ${T.blue}ee, ${T.blue}cc)` }}>
        <div style={{ maxWidth: 1280, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 72 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "rgba(255,255,255,0.9)", textTransform: "uppercase", letterSpacing: 2.5, marginBottom: 16 }}>
              Core Intelligence
            </div>
            <h2 style={{ fontSize: "clamp(32px, 6vw, 48px)", fontWeight: 800, color: T.white, marginBottom: 20, letterSpacing: -0.8 }}>
              Safe. Fast. Proactive.
            </h2>
            <p style={{ fontSize: 18, color: "rgba(255,255,255,0.85)", maxWidth: 620, margin: "0 auto", lineHeight: 1.6 }}>
              Real multi-agent AI, actual database writes, full observability — exceeding every hackathon requirement.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 28 }}>
            <Feature icon={MessageCircle} title="Natural Language Ordering" desc="Voice or text — NER-powered extraction turns requests into precise orders instantly." />
            <Feature icon={ShieldCheck} title="Real-Time Safety Engine" desc="Drug interactions, allergies, stock checks — zero unsafe dispensations." />
            <Feature icon={BellRing} title="Predictive Refills & Alerts" desc="Analyzes patterns, forecasts needs, sends proactive notifications." />
            <Feature icon={Database} title="Production-Grade Tools" desc="PostgreSQL writes, webhooks, inventory updates — real backend impact." />
            <Feature icon={Activity} title="Full Traceability" desc="Langfuse-powered observability — every agent step visible to judges." />
            <Feature icon={Layers} title="Distributed Pharmacy Network" desc="Virtual grid with intelligent routing and load balancing." />
          </div>
        </div>
      </section>

      <section id="architecture" style={{ padding: "clamp(80px, 12vh, 120px) 5vw", background: T.white }}>
        {/* ... architecture content unchanged ... */}
      </section>

      {/* ──────────────────────────────────────────────── */}
      {/*               MODIFIED TEAM SECTION               */}
      {/* ──────────────────────────────────────────────── */}
      <section 
        id="team" 
        style={{ 
          position: "relative",
          padding: "clamp(100px, 15vh, 160px) 5vw",
          background: T.gray50,
          overflow: "hidden",
          color: T.gray900,
        }}
      >
        {/* Background image – now fully visible */}
        <div style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `url(/images/team-corviknight-bg.png)`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          opacity: 0.35,                    // ← increased visibility (was 0.18)
          zIndex: 0,
        }} />

        {/* Removed the white overlay gradient completely */}

        <div style={{ 
          position: "relative", 
          zIndex: 2,
          maxWidth: 900, 
          margin: "0 auto", 
          textAlign: "center" 
        }}>
          <h2 style={{ 
            fontSize: "clamp(40px, 8vw, 58px)", 
            fontWeight: 800, 
            color: T.blue, 
            marginBottom: 32,
            letterSpacing: -1,
            textShadow: "0 1px 3px rgba(0,0,0,0.15)"   // subtle shadow for readability
          }}>
            Team Corviknight
          </h2>

          <p style={{ 
            fontSize: 19, 
            color: '#1f2937',                     // slightly darker gray for better contrast
            lineHeight: 1.7, 
            maxWidth: 680, 
            margin: "0 auto 56px",
            fontWeight: 500,
            textShadow: "0 1px 2px rgba(0,0,0,0.08)"
          }}>
            Building the future of intelligent, safe pharmacy operations — HackFusion 3.
          </p>

          <button 
            onClick={onGoToLogin} 
            style={{ 
              padding: "18px 56px", 
              background: T.blue, 
              color: T.white, 
              border: "none", 
              borderRadius: 14, 
              fontSize: 18, 
              fontWeight: 700, 
              cursor: "pointer",
              display: "inline-flex", 
              alignItems: "center", 
              gap: 14,
              boxShadow: `0 10px 40px ${T.blue}50`,
              transition: "all 0.28s ease",
            }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = "translateY(-4px)";
              e.currentTarget.style.boxShadow = `0 16px 56px ${T.blue}70`;
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = `0 10px 40px ${T.blue}50`;
            }}
          >
            Enter Dashboard <ArrowRight size={22} />
          </button>
        </div>
      </section>

      <footer style={{ 
        padding: "clamp(40px, 6vw, 64px) 5vw 32px", 
        borderTop: `1px solid ${T.gray200}`, 
        display: "flex", 
        flexDirection: "column", 
        alignItems: "center", 
        gap: 16,
        color: T.gray500,
        fontSize: 14,
        background: T.white,
      }}>
        <Logo size="sm" />
        <span>© 2026 Team Corviknight — HackFusion 3</span>
      </footer>
    </div>
  );
}