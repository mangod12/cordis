"use client";

import { useState, useEffect } from "react";
import { Activity, Settings, Shield } from "lucide-react";
import { fetchHealth, type HealthResponse } from "@/lib/api";

export default function Header() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [time, setTime] = useState("");

  useEffect(() => {
    fetchHealth().then(setHealth);
    const interval = setInterval(() => {
      fetchHealth().then(setHealth);
      setTime(new Date().toLocaleTimeString());
    }, 5000);
    setTime(new Date().toLocaleTimeString());
    return () => clearInterval(interval);
  }, []);

  const isOk = health?.status === "ok";

  return (
    <header className="flex items-center justify-between mb-6">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">
          Cordis
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          AI Crisis Coordination — from distress call to resource dispatch
        </p>
      </div>

      <div className="flex items-center gap-4">
        {health && (
          <div className="hidden md:flex items-center gap-3 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <Shield size={12} /> v{health.version}
            </span>
            <span className="flex items-center gap-1">
              <Settings size={12} /> {health.logistics_enabled ? "Logistics ON" : "Logistics OFF"}
            </span>
          </div>
        )}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${isOk ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-red-500/10 text-red-400 border border-red-500/20"}`}>
          <Activity size={12} className={isOk ? "animate-pulse" : ""} />
          {isOk ? "System Active" : "Degraded"}
        </div>
        <span className="text-xs text-slate-600">{time}</span>
      </div>
    </header>
  );
}
