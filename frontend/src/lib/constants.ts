export const SEVERITY_COLORS = {
  critical: { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400", dot: "bg-red-500" },
  high: { bg: "bg-amber-500/10", border: "border-amber-500/30", text: "text-amber-400", dot: "bg-amber-500" },
  medium: { bg: "bg-yellow-500/10", border: "border-yellow-500/30", text: "text-yellow-400", dot: "bg-yellow-500" },
  low: { bg: "bg-emerald-500/10", border: "border-emerald-500/30", text: "text-emerald-400", dot: "bg-emerald-500" },
} as const;

export const SEVERITY_HEX = {
  critical: "#ef4444",
  high: "#f59e0b",
  medium: "#eab308",
  low: "#22c55e",
} as const;

export const CITIES: Record<string, [number, number]> = {
  bhubaneswar: [20.30, 85.82], kolkata: [22.57, 88.36], chennai: [13.08, 80.27],
  mumbai: [19.08, 72.88], delhi: [28.61, 77.21], bangalore: [12.97, 77.59],
  hyderabad: [17.39, 78.49], ahmedabad: [23.02, 72.57], jaipur: [26.91, 75.79],
  patna: [25.61, 85.14], guwahati: [26.14, 91.74], pune: [18.52, 73.86],
  lucknow: [26.85, 80.95], puri: [19.81, 85.83], cuttack: [20.46, 85.88],
  odisha: [20.50, 84.00], bihar: [25.60, 85.10], kerala: [10.85, 76.27],
  kochi: [9.97, 76.27], surat: [21.17, 72.83], visakhapatnam: [17.69, 83.22],
  uttarakhand: [30.32, 78.03], shimla: [31.10, 77.17], raipur: [21.25, 81.63],
  nagpur: [21.15, 79.09], indore: [22.72, 75.86], bhopal: [23.26, 77.41],
  ranchi: [23.34, 85.31], varanasi: [25.32, 83.01], agra: [27.18, 78.02],
  chandigarh: [30.73, 76.77], goa: [15.30, 74.12],
};

export const PIPELINE_STEPS = ["stt", "intent", "emotion", "severity", "dispatch"] as const;
export type PipelineStep = typeof PIPELINE_STEPS[number];

export const STEP_LABELS: Record<PipelineStep, string> = {
  stt: "STT",
  intent: "Intent",
  emotion: "Emotion",
  severity: "Severity",
  dispatch: "Dispatch",
};
