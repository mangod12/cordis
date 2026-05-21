"use client";

import Link from "next/link";
import type { CallRecord } from "@/lib/api";
import { SEVERITY_COLORS } from "@/lib/constants";

interface CallsTableProps {
  calls: CallRecord[];
}

export default function CallsTable({ calls }: CallsTableProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <table aria-label="Emergency calls" className="w-full text-sm">
        <thead>
          <tr className="bg-slate-800/70">
            {["Call ID", "Transcript", "Intent", "Emotion", "Severity", "Responder", "Latency"].map((h) => (
              <th key={h} className="px-4 py-3 text-left text-[11px] text-slate-500 uppercase tracking-wider font-semibold">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/50">
          {calls.length === 0 ? (
            <tr>
              <td colSpan={7} className="px-4 py-12 text-center text-slate-600 text-sm">
                Waiting for calls...
              </td>
            </tr>
          ) : (
            calls.map((c) => {
              const sev = SEVERITY_COLORS[c.severity] || SEVERITY_COLORS.low;
              return (
                <tr key={c.call_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3"><Link href={`/calls/${c.call_id}`} className="font-mono text-xs text-cyan-400 hover:underline">{c.call_id}</Link></td>
                  <td className="px-4 py-3 text-slate-300 max-w-xs truncate">{c.transcript?.slice(0, 80)}</td>
                  <td className="px-4 py-3 text-slate-300">
                    {c.intent} <span className="text-slate-600">({(c.intent_confidence * 100).toFixed(0)}%)</span>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{c.emotion}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold ${sev.bg} ${sev.border} ${sev.text} border`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${sev.dot}`} />
                      {c.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-300">{c.responder}</td>
                  <td className="px-4 py-3 text-cyan-400 font-mono text-xs">{c.latency_ms}ms</td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
