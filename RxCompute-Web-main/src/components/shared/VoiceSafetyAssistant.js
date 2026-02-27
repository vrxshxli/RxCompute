import React, { useMemo, useRef, useState } from "react";
import { Mic, MicOff, Volume2 } from "lucide-react";
import T from "../../utils/tokens";

function clean(text) {
  return (text || "").toLowerCase().trim();
}

export default function VoiceSafetyAssistant({ nav = [], onSelectPage, notifications = [], markAllRead, token, apiBase }) {
  const recRef = useRef(null);
  const [listening, setListening] = useState(false);
  const [lastHeard, setLastHeard] = useState("");
  const SpeechRecognition = typeof window !== "undefined" ? (window.SpeechRecognition || window.webkitSpeechRecognition) : null;

  const speak = (text) => {
    if (!text) return;
    try {
      if (!window.speechSynthesis) return;
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 0.95;
      u.pitch = 1.0;
      window.speechSynthesis.speak(u);
    } catch (_) {}
  };

  const navKeywords = useMemo(
    () => [
      ...nav.map((n) => ({ key: n.key, tokens: [clean(n.label), clean(n.key).replace(/-/g, " ")] })),
      { key: "safety-events", tokens: ["safety events", "safety event"] },
      { key: "orders", tokens: ["orders", "order list"] },
      { key: "inventory", tokens: ["inventory", "stocks", "stock"] },
      { key: "profile", tokens: ["profile", "my profile"] },
    ],
    [nav],
  );

  const runSafetyByVoice = async (medicineText, qty) => {
    if (!token || !apiBase) {
      speak("Please login first.");
      return;
    }
    try {
      const medRes = await fetch(`${apiBase}/medicines/?search=${encodeURIComponent(medicineText)}&limit=5`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const meds = medRes.ok ? await medRes.json() : [];
      const med = Array.isArray(meds) && meds.length ? meds[0] : null;
      if (!med) {
        speak(`I could not find ${medicineText} in inventory.`);
        return;
      }
      const safetyRes = await fetch(`${apiBase}/safety/check-single/${med.id}?quantity=${qty || 1}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const safety = await safetyRes.json();
      if (!safetyRes.ok) {
        speak(safety?.detail || "Safety check failed.");
        return;
      }
      const msg = safety?.safety_summary || (safety?.blocked ? "Order blocked by safety policy." : "Safety check completed.");
      speak(msg);
    } catch (_) {
      speak("Network error while running safety check.");
    }
  };

  const handleCommand = async (raw) => {
    const text = clean(raw);
    setLastHeard(raw);
    if (!text) return;

    if (text.includes("help")) {
      speak("You can say open orders, open safety events, mark all notifications, read latest safety alert, or check safety for paracetamol quantity two.");
      return;
    }

    if (text.includes("mark all notifications")) {
      markAllRead?.();
      speak("All notifications marked as read.");
      return;
    }

    if (text.includes("read latest safety")) {
      const safety = notifications.find((n) => clean(n.type) === "safety");
      if (!safety) {
        speak("No safety alerts found.");
      } else {
        speak(`${safety.title}. ${safety.body}`);
      }
      return;
    }

    const safetyCmd = text.match(/check safety for (.+?)(?: quantity (\d+)| qty (\d+)|$)/i);
    if (safetyCmd) {
      const medicineText = (safetyCmd[1] || "").trim();
      const qty = Number(safetyCmd[2] || safetyCmd[3] || 1);
      await runSafetyByVoice(medicineText, qty);
      return;
    }

    for (const item of navKeywords) {
      if (item.tokens.some((t) => text.includes(`open ${t}`) || text.includes(`go to ${t}`) || text === t)) {
        onSelectPage?.(item.key);
        speak(`Opening ${item.tokens[0]}.`);
        return;
      }
    }

    speak("Command not recognized. Say help for available commands.");
  };

  const startListening = () => {
    if (!SpeechRecognition) {
      speak("Voice recognition is not supported in this browser.");
      return;
    }
    try {
      const rec = new SpeechRecognition();
      rec.lang = "en-IN";
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      rec.onstart = () => setListening(true);
      rec.onend = () => setListening(false);
      rec.onerror = () => setListening(false);
      rec.onresult = (event) => {
        const transcript = event?.results?.[0]?.[0]?.transcript || "";
        handleCommand(transcript);
      };
      recRef.current = rec;
      rec.start();
    } catch (_) {
      setListening(false);
    }
  };

  const stopListening = () => {
    try {
      recRef.current?.stop();
    } catch (_) {}
    setListening(false);
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <button
        onClick={listening ? stopListening : startListening}
        title="Voice Safety Agent"
        style={{
          background: listening ? `${T.red}20` : "transparent",
          border: `1px solid ${listening ? T.red : T.navy600}`,
          color: listening ? T.red : T.white,
          width: 28,
          height: 28,
          borderRadius: 14,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {listening ? <MicOff size={14} /> : <Mic size={14} />}
      </button>
      <div style={{ display: "flex", alignItems: "center", gap: 4, color: T.gray300, fontSize: 10, maxWidth: 180, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
        <Volume2 size={12} />
        <span>{lastHeard ? `Heard: ${lastHeard}` : "Voice agent ready"}</span>
      </div>
    </div>
  );
}
