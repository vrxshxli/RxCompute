import React, { useEffect, useMemo, useState } from 'react';
import T from '../../utils/tokens';
import { StatCard, PageHeader } from '../../components/shared';
import { ShoppingCart, Zap, Shield, AlertTriangle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
export default function PharmacyAnalytics() {
  const { token, apiBase } = useAuth();
  const [orders, setOrders] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [forecast, setForecast] = useState({ critical: 0, high: 0, reorder_alerts: [] });
  const [forecastError, setForecastError] = useState("");
  useEffect(() => {
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}` };
    const load = async () => {
      try {
        const [ordersRes, medsRes, forecastRes] = await Promise.all([
          fetch(`${apiBase}/orders/`, { headers }),
          fetch(`${apiBase}/medicines/?limit=500`, { headers }),
          fetch(`${apiBase}/demand-forecast/reorder-alerts?days=14`, { headers }),
        ]);
        if (ordersRes.ok) {
          const data = await ordersRes.json();
          setOrders(Array.isArray(data) ? data : []);
        }
        if (medsRes.ok) {
          const data = await medsRes.json();
          setMedicines(Array.isArray(data) ? data : []);
        }
        if (forecastRes.ok) {
          const data = await forecastRes.json();
          setForecast({
            critical: Number(data?.critical || 0),
            high: Number(data?.high || 0),
            reorder_alerts: Array.isArray(data?.reorder_alerts) ? data.reorder_alerts : [],
          });
          setForecastError("");
        } else {
          const err = await forecastRes.text();
          setForecastError(err || "Unable to load demand forecast");
        }
      } catch (_) {}
    };
    load();
  }, [token, apiBase]);
  const rxVerified = orders.filter((o) => ["verified", "confirmed", "dispatched", "delivered"].includes(o.status)).length;
  const blocked = orders.filter((o) => o.status === "cancelled").length;
  const top = useMemo(() => medicines.slice(0, 6), [medicines]);
  return (<div><PageHeader title="Analytics" subtitle="PH-001"/>
  <div style={{display:"flex",gap:16,marginBottom:24,flexWrap:"wrap"}}><StatCard icon={ShoppingCart} label="Orders" value={String(orders.length)} color={T.blue}/><StatCard icon={Zap} label="AI Assist" value="96%" color={T.purple}/><StatCard icon={Shield} label="Rx Verified" value={String(rxVerified)} color={T.orange}/><StatCard icon={AlertTriangle} label="Demand Alerts" value={String((forecast.critical || 0) + (forecast.high || 0))} color={T.red}/></div>
  {forecastError ? <div style={{fontSize:12,color:T.red,background:`${T.red}12`,border:`1px solid ${T.red}33`,borderRadius:8,padding:"8px 12px",marginBottom:12}}>{forecastError}</div> : null}
  <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
    <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:20}}><div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:16}}>Orders — 7 Days</div><div style={{display:"flex",alignItems:"flex-end",gap:8,height:160}}>{[18,22,15,28,32,25,23].map((v,i)=><div key={i} style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",gap:4}}><span style={{fontSize:10,color:T.gray500,fontWeight:600}}>{v}</span><div style={{width:"100%",height:(v/35)*140+"px",borderRadius:6,background:i===6?T.blue:T.blue+"30"}}/><span style={{fontSize:9,color:T.gray400}}>{["M","T","W","T","F","S","S"][i]}</span></div>)}</div></div>
    <div style={{background:T.white,border:"1px solid "+T.gray200,borderRadius:12,padding:20}}><div style={{fontWeight:600,fontSize:14,color:T.gray900,marginBottom:16}}>Top Dispensed / Forecast Risk</div>{(forecast.reorder_alerts.length ? forecast.reorder_alerts.slice(0,6).map((m,i)=><div key={i} style={{display:"flex",alignItems:"center",gap:12,marginBottom:12}}><span style={{width:24,height:24,borderRadius:6,background:T.orange+"15",display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:700,color:T.orange}}>{i+1}</span><span style={{fontSize:13,color:T.gray700,flex:1,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{m.name}</span><div style={{fontSize:11,color:T.red,fontWeight:700,textTransform:"uppercase"}}>{m.risk || "high"}</div></div>) : top.map((m,i)=><div key={i} style={{display:"flex",alignItems:"center",gap:12,marginBottom:12}}><span style={{width:24,height:24,borderRadius:6,background:T.orange+"15",display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:700,color:T.orange}}>{i+1}</span><span style={{fontSize:13,color:T.gray700,flex:1,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{m.name}</span><div style={{width:80,height:6,borderRadius:3,background:T.gray100,overflow:"hidden"}}><div style={{height:"100%",borderRadius:3,width:(70-i*10)+"%",background:T.orange}}/></div></div>))}</div>
  </div></div>);
}