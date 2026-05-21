export function StatsSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-4 animate-pulse">
          <div className="h-3 w-16 bg-slate-800 rounded mb-3" />
          <div className="h-7 w-12 bg-slate-800 rounded" />
        </div>
      ))}
    </div>
  );
}

export function MapSkeleton() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="h-4 w-20 bg-slate-800 rounded mb-3 animate-pulse" />
      <div className="h-[380px] rounded-lg bg-slate-800/50 animate-pulse flex items-center justify-center">
        <span className="text-slate-700 text-sm">Loading map...</span>
      </div>
    </div>
  );
}

export function TableSkeleton() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden animate-pulse">
      <div className="h-10 bg-slate-800/70" />
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="h-12 border-t border-slate-800/50 flex items-center px-4 gap-4">
          <div className="h-3 w-16 bg-slate-800 rounded" />
          <div className="h-3 w-48 bg-slate-800 rounded" />
          <div className="h-3 w-12 bg-slate-800 rounded" />
        </div>
      ))}
    </div>
  );
}
