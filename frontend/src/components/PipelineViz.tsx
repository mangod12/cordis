"use client";

import { PIPELINE_STEPS, STEP_LABELS } from "@/lib/constants";
import { ChevronRight } from "lucide-react";

interface PipelineVizProps {
  steps: Record<string, string>;
  values: Record<string, string>;
}

const stateStyles: Record<string, string> = {
  idle: "border-slate-700 bg-slate-800/30",
  active: "border-cyan-500/50 bg-cyan-500/5 animate-pulse",
  done: "border-emerald-500/50 bg-emerald-500/5",
  error: "border-red-500/50 bg-red-500/5",
};

const valueStyles: Record<string, string> = {
  idle: "text-slate-600",
  active: "text-cyan-400",
  done: "text-emerald-400",
  error: "text-red-400",
};

export default function PipelineViz({ steps, values }: PipelineVizProps) {
  return (
    <div className="mt-4">
      <p className="text-[10px] text-slate-600 uppercase tracking-widest font-semibold mb-2">Agent Pipeline</p>
      <div className="flex items-center gap-1">
        {PIPELINE_STEPS.map((step, i) => (
          <div key={step} className="flex items-center gap-1 flex-1">
            <div className={`flex-1 border rounded-lg p-2 text-center transition-all duration-300 ${stateStyles[steps[step] || "idle"]}`}>
              <p className="text-[10px] text-slate-500 font-medium">{STEP_LABELS[step]}</p>
              <p className={`text-xs font-mono mt-0.5 ${valueStyles[steps[step] || "idle"]}`}>
                {values[step] || "—"}
              </p>
            </div>
            {i < PIPELINE_STEPS.length - 1 && (
              <ChevronRight size={12} className="text-slate-700 shrink-0" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
