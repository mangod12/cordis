"use client";
import { Component, type ReactNode } from "react";

interface Props { children: ReactNode; fallback?: ReactNode; label?: string; }
interface State { hasError: boolean; error: Error | null; }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-6 text-center">
          <p className="text-red-400 text-sm font-medium mb-1">{this.props.label || "Component"} failed to load</p>
          <p className="text-xs text-slate-600">{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-3 px-3 py-1 bg-slate-800 text-slate-300 text-xs rounded-lg hover:bg-slate-700">
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
