"use client";

import { useState } from "react";
import { Key } from "lucide-react";
import { setToken } from "@/lib/api";

interface TokenDialogProps {
  onSet: () => void;
}

export default function TokenDialog({ onSet }: TokenDialogProps) {
  const [value, setValue] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (value.trim()) {
      setToken(value.trim());
      onSet();
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-cyan-500/10 rounded-lg">
            <Key size={20} className="text-cyan-400" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Authentication</h2>
            <p className="text-xs text-slate-500">Enter your JWT token to access the API</p>
          </div>
        </div>
        <form onSubmit={handleSubmit}>
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="eyJhbGciOiJIUzI1NiIs..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/20 outline-none mb-3 font-mono"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              className="flex-1 py-2 bg-gradient-to-r from-cyan-600 to-indigo-600 text-white font-semibold text-sm rounded-lg hover:from-cyan-500 hover:to-indigo-500 transition-all"
            >
              Connect
            </button>
            <button
              type="button"
              onClick={onSet}
              className="px-4 py-2 bg-slate-800 text-slate-400 text-sm rounded-lg hover:bg-slate-700 transition-colors"
            >
              Demo Mode
            </button>
          </div>
        </form>
        <p className="text-[10px] text-slate-600 mt-3">
          Generate a token: <code className="bg-slate-800 px-1 py-0.5 rounded">make token</code> or use the /api/v1/auth/login endpoint
        </p>
      </div>
    </div>
  );
}
