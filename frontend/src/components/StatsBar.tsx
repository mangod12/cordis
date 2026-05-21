"use client";

import type { CallRecord } from "@/lib/api";

interface StatsBarProps {
  calls: CallRecord[];
}

export default function StatsBar({ calls }: StatsBarProps) {
  const critical = calls.filter((c) => c.severity === "critical").length;
  const high = calls.filter((c) => c.severity === "high").length;
  const avgLatency = calls.length
    ? Math.round(calls.reduce((s, c) => s + (c.latency_ms || 0), 0) / calls.length)
    : 0;
  const fallbackRate = calls.length
    ? Math.round((calls.filter((c) => c.fallback_used).length / calls.length) * 100)
    : 0;

  const stats = [
    { label: "Total Calls", value: calls.length, color: "text-white" },
    { label: "Critical", value: critical, color: "text-red-400" },
    { label: "High", value: high, color: "text-amber-400" },
    { label: "Avg Latency", value: avgLatency ? `${avgLatency} ms` : "— ms", color: "text-cyan-400" },
    { label: "Fallback Rate", value: `${fallbackRate}%`, color: "text-violet-400" },
  ];

  return (
    <div role="region" aria-label="Emergency statistics" className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {stats.map((s) => (
        <div key={s.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <p className="text-[11px] text-slate-500 uppercase tracking-wider font-medium">{s.label}</p>
          <p className={`text-2xl font-bold mt-1 ${s.color}`}>{s.value}</p>
        </div>
      ))}
    </div>
  );
}
