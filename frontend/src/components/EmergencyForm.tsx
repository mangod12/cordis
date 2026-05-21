"use client";

import { useState, useRef } from "react";
import { Mic, Upload, Send, Loader2 } from "lucide-react";
import { submitEmergency, submitAudio, type EmergencyResponse } from "@/lib/api";
import PipelineViz from "./PipelineViz";

interface EmergencyFormProps {
  onResult: (result: EmergencyResponse) => void;
}

type StepState = "idle" | "active" | "done" | "error";

export default function EmergencyForm({ onResult }: EmergencyFormProps) {
  const [transcript, setTranscript] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EmergencyResponse | null>(null);
  const [steps, setSteps] = useState<Record<string, StepState>>({
    stt: "idle", intent: "idle", emotion: "idle", severity: "idle", dispatch: "idle",
  });
  const [stepValues, setStepValues] = useState<Record<string, string>>({});
  const [showPipeline, setShowPipeline] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleSubmit() {
    const file = fileRef.current?.files?.[0];
    if (!transcript.trim() && !file) {
      setError("Provide audio or text transcript.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setShowPipeline(true);
    setSteps({ stt: "active", intent: "idle", emotion: "idle", severity: "idle", dispatch: "idle" });
    setStepValues({});

    try {
      let data: EmergencyResponse;
      if (file) {
        data = await submitAudio(file);
      } else {
        setSteps((s) => ({ ...s, stt: "done" }));
        setStepValues((v) => ({ ...v, stt: "text" }));
        data = await submitEmergency(transcript);
      }

      // Animate pipeline steps
      setSteps((s) => ({ ...s, stt: "done" }));
      setStepValues((v) => ({ ...v, stt: "done" }));

      await delay(100);
      setSteps((s) => ({ ...s, intent: "done" }));
      setStepValues((v) => ({ ...v, intent: data.intent }));

      await delay(100);
      setSteps((s) => ({ ...s, emotion: "done" }));
      setStepValues((v) => ({ ...v, emotion: data.emotion }));

      await delay(100);
      setSteps((s) => ({ ...s, severity: "done" }));
      setStepValues((v) => ({ ...v, severity: data.severity }));

      await delay(100);
      setSteps((s) => ({ ...s, dispatch: "done" }));
      setStepValues((v) => ({ ...v, dispatch: data.responder }));

      setResult(data);
      onResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      setSteps((s) => ({ ...s, stt: "error" }));
    } finally {
      setLoading(false);
    }
  }

  const severityColor: Record<string, string> = {
    critical: "text-red-400", high: "text-amber-400", medium: "text-yellow-400", low: "text-emerald-400",
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <h2 className="text-sm font-semibold text-slate-400 mb-4">Submit Emergency</h2>

      {/* Audio Upload */}
      <div className="mb-3">
        <label className="text-xs text-slate-500 mb-1 block">Audio File (optional)</label>
        <div className="flex items-center gap-2">
          <button
            onClick={() => fileRef.current?.click()}
            className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs text-slate-300 transition-colors"
          >
            <Upload size={14} /> Choose File
          </button>
          <input ref={fileRef} type="file" accept="audio/*" className="hidden" />
          <span className="text-xs text-slate-600">
            {fileRef.current?.files?.[0]?.name || "No file chosen"}
          </span>
        </div>
      </div>

      {/* Transcript */}
      <div className="mb-4">
        <label className="text-xs text-slate-500 mb-1 block">Or type transcript</label>
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          rows={3}
          placeholder="There is a massive fire at the warehouse on 5th street..."
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20 outline-none resize-none transition-colors"
        />
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-semibold text-sm rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        {loading ? "Processing..." : "Process Emergency"}
      </button>

      {/* Error */}
      {error && (
        <div className="mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs">
          {error}
        </div>
      )}

      {/* Pipeline Visualization */}
      {showPipeline && <PipelineViz steps={steps} values={stepValues} />}

      {/* Result Card */}
      {result && (
        <div className="mt-3 p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
          <div className="flex justify-between items-center mb-2">
            <span className={`text-sm font-bold ${severityColor[result.severity] || "text-white"}`}>
              {result.severity.toUpperCase()} — {result.intent}
            </span>
            <span className="text-xs text-slate-500">{result.latency_ms}ms</span>
          </div>
          <p className="text-xs text-slate-400">
            Dispatched: <span className="text-slate-300">{result.responder}</span> · Call ID: <span className="font-mono text-slate-500">{result.call_id}</span>
          </p>
        </div>
      )}
    </div>
  );
}

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
