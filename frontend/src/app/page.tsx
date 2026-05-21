"use client";

import { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import Header from "@/components/Header";
import StatsBar from "@/components/StatsBar";
import EmergencyForm from "@/components/EmergencyForm";
import CallsTable from "@/components/CallsTable";
import TokenDialog from "@/components/TokenDialog";
import { fetchCalls, getStoredToken, type CallRecord, type EmergencyResponse } from "@/lib/api";

const CrisisMap = dynamic(() => import("@/components/CrisisMap"), { ssr: false });

export default function Dashboard() {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [showToken, setShowToken] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setShowToken(true);
    }
    setReady(true);
  }, []);

  const refreshCalls = useCallback(async () => {
    const data = await fetchCalls();
    setCalls(data);
  }, []);

  useEffect(() => {
    refreshCalls();
    const interval = setInterval(refreshCalls, 3000);
    return () => clearInterval(interval);
  }, [refreshCalls]);

  function handleResult(_result: EmergencyResponse) {
    refreshCalls();
  }

  if (!ready) return null;

  return (
    <>
      {showToken && <TokenDialog onSet={() => setShowToken(false)} />}
      <div className="max-w-[1400px] mx-auto px-4 py-6">
        <Header />
        <div className="mb-5">
          <StatsBar calls={calls} />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
          <CrisisMap calls={calls} />
          <EmergencyForm onResult={handleResult} />
        </div>
        <CallsTable calls={calls} />
      </div>
    </>
  );
}
