/* ═══════════════════════════════════════════════════════════
   Mock Data — Medicines, Patients, Orders, Alerts, etc.
   In production, replace with API calls via src/services/
   ═══════════════════════════════════════════════════════════ */

const MEDICINE_NAMES = [
  "NORSAN Omega-3 Total","Panthenol Spray 46.3mg/g","Mucosolvan Capsules 75mg",
  "Paracetamol AL 500mg","Ibuprofen STADA 400mg","Amoxicillin Ratiopharm 1000mg",
  "Aspirin Plus C","Voltaren Schmerzgel forte","Bepanthen Wound Cream",
  "ACC akut 600mg","Nasenspray AL 0.1%","Loperamid akut Heumann",
  "Cetirizin HEXAL","Omeprazol-ratiopharm 20mg","Metformin Lich 500mg",
  "Ramipril HEXAL 5mg","Simvastatin AbZ 20mg","L-Thyroxin Henning 50",
  "Bisoprolol-ratiopharm 5mg","Amlodipine STADA 5mg","Diclofenac Sodium 75mg",
  "Prednisolone 5mg GALEN","Doxycyclin AL 100","Ciprofloxacin Basics 250mg",
  "Tamsulosin BASICS 0.4mg","Pantoprazol-1A 40mg","Torasemid AL 10mg",
  "Candesartan Cilexetil 8mg","Gabapentin Aurobindo 300mg","Clopidogrel Zentiva 75mg",
  "Levothyroxine 100mcg","Atorvastatin AbZ 40mg","Esomeprazol TAD 20mg",
  "Metoprolol Succinat 47.5mg","Valsartan-ratiopharm 160mg","Hydrochlorothiazid AL 25mg",
  "Mirtazapin Heumann 15mg","Sertralin BASICS 50mg","Duloxetin Lilly 30mg",
  "Pregabalin Pfizer 75mg","Rivaroxaban Bayer 20mg","Apixaban BMS 5mg",
  "Empagliflozin Jardiance 10mg","Sitagliptin MSD 100mg","Insulin Lantus SoloStar",
  "Formoterol-ratiopharm 12mcg","Salbutamol AL Inhalation","Budesonid-ratiopharm 0.5mg",
  "Montelukast Aurobindo 10mg","Xarelto 15mg","Eliquis 2.5mg","Jardiance 25mg",
];

const PATIENT_NAMES = [
  "Deepak Sharma","Priya Patel","Amit Kumar","Sonal Gupta","Rajesh Mehta",
  "Ananya Singh","Vikram Joshi","Meera Reddy","Karan Malhotra","Nisha Verma",
  "Arjun Nair","Divya Kapoor","Suresh Iyer","Pooja Deshmukh","Ravi Kulkarni",
  "Isha Rao","Nikhil Banerjee","Kavita Choudhury","Manoj Thakur","Sneha Pillai",
  "Arun Bhat","Ritika Saxena","Harsh Agarwal","Tanya Mishra","Gaurav Pandey",
  "Swati Jain","Rohit Sinha","Pallavi Shah","Yash Tiwari","Aditi Mukherjee",
  "Sanjay Dubey","Leena Bhatt","Pranav Goyal","Rekha Menon","Vivek Chopra","Shruti Das",
];

export const MEDICINES = Array.from({ length: 52 }, (_, i) => ({
  id: i + 1,
  name: MEDICINE_NAMES[i] || `Medicine Product ${i + 1}`,
  pzn: `${13400000 + i * 137}`,
  price: parseFloat((Math.random() * 80 + 5).toFixed(2)),
  package_size: ["60 st","200 ml","130 g","30 st","100 ml","20 st","50 st","10 st"][i % 8],
  stock: Math.floor(Math.random() * 300),
  rx: i % 7 === 2 || i % 7 === 5,
  category: ["Pain Relief","Respiratory","Cardiovascular","Diabetes","GI","Antibiotics","Dermatology","CNS"][i % 8],
}));

export const PATIENTS = Array.from({ length: 36 }, (_, i) => ({
  pid: `PAT${String(i + 1).padStart(3, "0")}`,
  name: PATIENT_NAMES[i],
  age: Math.floor(Math.random() * 55) + 20,
  gender: ["M", "F"][i % 2],
  email: `patient${i + 1}@example.com`,
  phone: `+91 98${Math.floor(Math.random() * 9e7 + 1e7)}`,
}));

export const ORDERS = Array.from({ length: 25 }, (_, i) => {
  const statuses = ["pending","confirmed","pharmacy_verified","picking","packed","dispatched","delivered","cancelled"];
  const patient = PATIENTS[Math.floor(Math.random() * 36)];
  const items = Array.from({ length: Math.floor(Math.random() * 3) + 1 }, () => {
    const m = MEDICINES[Math.floor(Math.random() * 52)];
    return { product_id: m.id, product_name: m.name, quantity: Math.floor(Math.random() * 3) + 1, unit_price: m.price };
  });
  const d = new Date(2026, 1, Math.floor(Math.random() * 20) + 1, Math.floor(Math.random() * 24), Math.floor(Math.random() * 60));
  return {
    order_id: `ORD-${d.toISOString().slice(0, 10).replace(/-/g, "")}-${String(i + 1).padStart(3, "0")}`,
    patient_id: patient.pid,
    patient_name: patient.name,
    status: statuses[Math.floor(Math.random() * statuses.length)],
    total_price: parseFloat(items.reduce((a, x) => a + x.unit_price * x.quantity, 0).toFixed(2)),
    pharmacy_node: `PH-00${(i % 3) + 1}`,
    items,
    created_at: d.toISOString(),
  };
});

export const REFILL_ALERTS = Array.from({ length: 40 }, (_, i) => {
  const p = PATIENTS[i % 36];
  const m = MEDICINES[Math.floor(Math.random() * 52)];
  const days_remaining = Math.floor(Math.random() * 60) - 30;
  return {
    id: i + 1,
    patient_id: p.pid,
    patient_age: p.age,
    medicine: m.name,
    last_purchase: new Date(2025, 11, Math.floor(Math.random() * 28) + 1).toISOString().slice(0, 10),
    dosage: ["Once daily","Twice daily","Three times daily","As needed"][i % 4],
    predicted_runout: new Date(2026, 1, Math.floor(Math.random() * 28) + 1).toISOString().slice(0, 10),
    days_remaining,
    risk_level: days_remaining < -7 ? "overdue" : days_remaining < 0 ? "high" : days_remaining < 7 ? "medium" : "low",
    status: ["pending","notified","confirmed","declined"][Math.floor(Math.random() * 4)],
  };
});

export const SAFETY_RULES = [
  { id: 1, name: "Prescription Check", condition: { field: "prescription_required", operator: "equals", value: true }, action: "block", message: "This medicine requires a valid prescription. Please upload to proceed.", active: true },
  { id: 2, name: "Out of Stock Block", condition: { field: "stock_level", operator: "equals", value: 0 }, action: "block", message: "This medicine is currently out of stock.", active: true },
  { id: 3, name: "Low Stock Warning", condition: { field: "stock_level", operator: "less_than", value: 10 }, action: "warn", message: "Low stock alert: only a few units remaining.", active: true },
  { id: 4, name: "High Quantity Alert", condition: { field: "quantity", operator: "greater_than", value: 5 }, action: "escalate", message: "Orders exceeding 5 units require pharmacist verification.", active: true },
  { id: 5, name: "Controlled Substance", condition: { field: "is_controlled", operator: "equals", value: true }, action: "escalate", message: "Controlled substance requires pharmacist approval.", active: false },
];

export const AGENT_LOGS = Array.from({ length: 30 }, (_, i) => {
  const agents = ["conversation_agent","safety_agent","inventory_agent","scheduler_agent","order_agent","prediction_agent"];
  const actions = [
    "Extracted: NORSAN Omega-3 Total, qty 1. Confidence: 0.96",
    "BLOCKED order ORD-042. Mucosolvan requires prescription.",
    "Checked stock for 3 items. All available.",
    "Routed ORD-043 to PH-002. Reason: closest with stock.",
    "Created order ORD-044. Total: €54.00",
    "Generated 12 refill predictions. 3 overdue.",
    "Extracted: Paracetamol 500mg, Ibuprofen 400mg. Confidence: 0.92",
    "WARNING: Low stock on Aspirin Plus C (3 units).",
    "Approved order ORD-045 after safety verification.",
    "Predicted refill needed for PAT008 — Omega-3 in 5 days.",
  ];
  const t = new Date(2026, 1, 20, 14, Math.floor(Math.random() * 60), Math.floor(Math.random() * 60));
  return {
    id: i + 1,
    trace_id: `tr-${Math.random().toString(36).slice(2, 10)}`,
    agent_name: agents[Math.floor(Math.random() * 6)],
    action: actions[Math.floor(Math.random() * 10)],
    created_at: t.toISOString(),
    confidence: parseFloat((Math.random() * 0.3 + 0.7).toFixed(2)),
  };
});

export const WEBHOOK_LOGS = Array.from({ length: 20 }, (_, i) => {
  const events = ["order_confirmed","fulfillment_request","notification_sent","stock_alert"];
  const ev = events[Math.floor(Math.random() * 4)];
  const t = new Date(2026, 1, 20, Math.floor(Math.random() * 24), Math.floor(Math.random() * 60));
  return {
    id: i + 1,
    event_type: ev,
    target_url: `http://localhost:5000/api/webhooks/${ev.includes("order") ? "fulfillment" : "notification"}`,
    response_status: Math.random() > 0.15 ? 200 : 500,
    payload: { order_id: `ORD-20260220-${String(i).padStart(3, "0")}`, patient_id: `PAT${String((i % 36) + 1).padStart(3, "0")}` },
    created_at: t.toISOString(),
  };
});

export const PHARMACY_NODES = [
  { node_id: "PH-001", name: "Central Pharmacy", location: "Mumbai Central", active: true, load: 35, stock_count: 48 },
  { node_id: "PH-002", name: "East Pharmacy", location: "Andheri East", active: true, load: 62, stock_count: 44 },
  { node_id: "PH-003", name: "South Pharmacy", location: "Colaba", active: false, load: 0, stock_count: 41 },
];