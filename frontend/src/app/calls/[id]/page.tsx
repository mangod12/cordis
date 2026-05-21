"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Clock, AlertTriangle, Radio, User, Activity } from "lucide-react";
import { getStoredToken, API_BASE } from "@/lib/api";
import { SEVERITY_COLORS } from "@/lib/constants";

interface CallDetail {
  call_id: string;
  transcript: string;
  intent: string;
  intent_confidence: number;
  emotion: string;
  severity: "critical" | "high" | "medium" | "low";
  responder: string;
  latency_ms: number;
  caller_id: string | null;
  timestamp?: string;
}

export default function CallDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [call, setCall] = useState<CallDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token || !params.id) { setLoading(false); return; }

    fetch(`${API_BASE}/api/v1/calls/live?limit=100`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => {
        const found = (data.calls || []).find((c: CallDetail) => c.call_id === params.id);
        setCall(found || null);
      })
      .catch(() => setCall(null))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 bg-slate-800 rounded" />
          <div className="h-64 bg-slate-900 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!call) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <p className="text-slate-500 text-lg mb-4">Call not found</p>
        <button onClick={() => router.push("/")} className="text-cyan-400 text-sm hover:underline">
          Back to dashboard
        </button>
      </div>
    );
  }

  const sev = SEVERITY_COLORS[call.severity] || SEVERITY_COLORS.low;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <button onClick={() => router.push("/")} className="flex items-center gap-1 text-slate-500 text-sm hover:text-slate-300 mb-6 transition-colors">
        <ArrowLeft size={14} /> Back to dashboard
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Emergency Call</h1>
          <p className="font-mono text-xs text-slate-500">{call.call_id}</p>
        </div>
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-bold ${sev.bg} ${sev.border} ${sev.text} border`}>
          <span className={`w-2 h-2 rounded-full ${sev.dot}`} />
          {call.severity.toUpperCase()}
        </span>
      </div>

      {/* Transcript */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-4">
        <h2 className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-3">Transcript</h2>
        <p className="text-slate-200 leading-relaxed">{call.transcript}</p>
      </div>

      {/* Agent Decisions Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={14} className="text-amber-400" />
            <span className="text-xs text-slate-500 uppercase font-semibold">Intent</span>
          </div>
          <p className="text-lg font-bold text-white">{call.intent}</p>
          <p className="text-xs text-slate-500 mt-1">{(call.intent_confidence * 100).toFixed(1)}% confidence</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={14} className="text-violet-400" />
            <span className="text-xs text-slate-500 uppercase font-semibold">Emotion</span>
          </div>
          <p className="text-lg font-bold text-white">{call.emotion}</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Radio size={14} className="text-cyan-400" />
            <span className="text-xs text-slate-500 uppercase font-semibold">Responder</span>
          </div>
          <p className="text-lg font-bold text-white">{call.responder}</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock size={14} className="text-cyan-400" />
            <span className="text-xs text-slate-500 uppercase font-semibold">Latency</span>
          </div>
          <p className="text-lg font-bold text-cyan-400">{call.latency_ms}ms</p>
        </div>

        {call.caller_id && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <User size={14} className="text-slate-400" />
              <span className="text-xs text-slate-500 uppercase font-semibold">Caller ID</span>
            </div>
            <p className="text-sm font-mono text-white">{call.caller_id}</p>
          </div>
        )}
      </div>

      {/* Pipeline Trace */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-3">Agent Pipeline Trace</h2>
        <div className="space-y-3">
          {[
            { step: "Speech-to-Text", result: "Transcript captured", time: "~" + Math.round(call.latency_ms * 0.3) + "ms" },
            { step: "Intent Classification", result: call.intent + " (" + (call.intent_confidence * 100).toFixed(0) + "%)", time: "~" + Math.round(call.latency_ms * 0.2) + "ms" },
            { step: "Emotion Detection", result: call.emotion, time: "~" + Math.round(call.latency_ms * 0.2) + "ms" },
            { step: "Severity Assessment", result: call.severity.toUpperCase(), time: "~" + Math.round(call.latency_ms * 0.15) + "ms" },
            { step: "Dispatch Routing", result: call.responder, time: "~" + Math.round(call.latency_ms * 0.15) + "ms" },
          ].map((trace, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-6 h-6 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 text-xs font-bold shrink-0">
                {i + 1}
              </div>
              <div className="flex-1">
                <p className="text-sm text-white font-medium">{trace.step}</p>
                <p className="text-xs text-slate-500">{trace.result}</p>
              </div>
              <span className="text-xs text-slate-600 font-mono">{trace.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
