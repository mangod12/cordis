"use client";

import { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import Header from "@/components/Header";
import StatsBar from "@/components/StatsBar";
import EmergencyForm from "@/components/EmergencyForm";
import CallsTable from "@/components/CallsTable";
import TokenDialog from "@/components/TokenDialog";
import { fetchCalls, fetchHealth, getStoredToken, type CallRecord, type EmergencyResponse } from "@/lib/api";
import ErrorBoundary from "@/components/ErrorBoundary";
import { StatsSkeleton, MapSkeleton, TableSkeleton } from "@/components/Skeleton";

const CrisisMap = dynamic(() => import("@/components/CrisisMap"), { ssr: false });

export default function Dashboard() {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [showToken, setShowToken] = useState(false);
  const [ready, setReady] = useState(false);
  const [backendOnline, setBackendOnline] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setShowToken(true);
    }
    setReady(true);
  }, []);

  useEffect(() => {
    const check = async () => {
      const h = await fetchHealth();
      setBackendOnline(h?.status === "ok");
    };
    check();
    const interval = setInterval(check, 5000);
    return () => clearInterval(interval);
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

  if (!ready) return (
    <div className="max-w-[1400px] mx-auto px-4 py-6">
      <div className="h-16 mb-6" />
      <div className="mb-5"><StatsSkeleton /></div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
        <MapSkeleton />
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 animate-pulse">
          <div className="h-4 w-32 bg-slate-800 rounded mb-4" />
          <div className="h-24 bg-slate-800/50 rounded-lg mb-4" />
          <div className="h-10 bg-slate-800 rounded-lg" />
        </div>
      </div>
      <TableSkeleton />
    </div>
  );

  return (
    <>
      {showToken && <TokenDialog onSet={() => setShowToken(false)} />}
      <div className="max-w-[1400px] mx-auto px-4 py-6">
        <Header />
        <div className="mb-5">
          <StatsBar calls={calls} />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
          <ErrorBoundary label="Crisis Map">
            <CrisisMap calls={calls} />
          </ErrorBoundary>
          <ErrorBoundary label="Emergency Form">
            <EmergencyForm onResult={handleResult} backendOnline={backendOnline} />
          </ErrorBoundary>
        </div>
        <ErrorBoundary label="Calls Table">
          <CallsTable calls={calls} />
        </ErrorBoundary>
      </div>
    </>
  );
}
