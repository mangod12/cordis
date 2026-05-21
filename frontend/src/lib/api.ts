const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("cordis_token") || "";
}

function headers(extra: Record<string, string> = {}): Record<string, string> {
  const token = getToken();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

export interface EmergencyResponse {
  call_id: string;
  transcript: string;
  intent: string;
  intent_confidence: number;
  emotion: string;
  severity: "critical" | "high" | "medium" | "low";
  responder: string;
  latency_ms: number;
  caller_id: string | null;
}

export interface CallRecord {
  call_id: string;
  timestamp: string;
  transcript: string;
  intent: string;
  intent_confidence: number;
  emotion: string;
  severity: "critical" | "high" | "medium" | "low";
  responder: string;
  fallback_used: boolean;
  intent_fallback: boolean;
  emotion_fallback: boolean;
  latency_ms: number;
  tenant_id: string;
}

export interface HealthResponse {
  status: string;
  project: string;
  version: string;
  logistics_enabled: boolean;
  dependencies: {
    database: string;
    redis: string;
    whisper_stt: string;
    intent_model: string;
  };
}

export async function submitEmergency(transcript: string): Promise<EmergencyResponse> {
  const resp = await fetch(`${API_BASE}/process-emergency`, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ transcript }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || resp.statusText);
  }
  return resp.json();
}

export async function submitAudio(file: File): Promise<EmergencyResponse> {
  const formData = new FormData();
  formData.append("audio_file", file);
  const resp = await fetch(`${API_BASE}/process-emergency`, {
    method: "POST",
    headers: headers(),
    body: formData,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || resp.statusText);
  }
  return resp.json();
}

export async function fetchCalls(limit = 50): Promise<CallRecord[]> {
  const token = getToken();
  if (!token) return []; // Don't attempt API call without token
  try {
    const resp = await fetch(`${API_BASE}/api/v1/calls/live?limit=${limit}`, {
      headers: headers(),
    });
    if (!resp.ok) return [];
    const data = await resp.json();
    return data.calls || [];
  } catch {
    return [];
  }
}

export async function fetchHealth(): Promise<HealthResponse | null> {
  try {
    const resp = await fetch(`${API_BASE}/health`);
    if (!resp.ok) return null;
    return resp.json();
  } catch {
    return null;
  }
}

export function setToken(token: string) {
  localStorage.setItem("cordis_token", token);
}

export function getStoredToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("cordis_token") || "";
}

export { API_BASE };
