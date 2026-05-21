"use client";

import { useEffect, useRef } from "react";
import type { CallRecord } from "@/lib/api";
import { CITIES, SEVERITY_HEX } from "@/lib/constants";

interface CrisisMapProps {
  calls: CallRecord[];
}

export default function CrisisMap({ calls }: CrisisMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<Map<string, L.CircleMarker>>(new Map());

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    import("leaflet").then((L) => {
      const map = L.map(mapRef.current!, { zoomControl: false }).setView([20.5, 82.0], 5);
      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: "&copy; CARTO",
        maxZoom: 18,
      }).addTo(map);
      L.control.zoom({ position: "bottomright" }).addTo(map);
      mapInstanceRef.current = map;
    });

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current.clear();
      mapInstanceRef.current?.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapInstanceRef.current) return;

    import("leaflet").then((L) => {
      const currentIds = new Set(calls.map((c) => c.call_id));

      // Remove markers for calls no longer present
      for (const [id, marker] of markersRef.current) {
        if (!currentIds.has(id)) {
          marker.remove();
          markersRef.current.delete(id);
        }
      }

      // Add markers for new calls only
      calls.forEach((c) => {
        if (markersRef.current.has(c.call_id)) return;

        const text = (c.transcript || "").toLowerCase();
        for (const [city, coords] of Object.entries(CITIES)) {
          if (text.includes(city)) {
            const color = SEVERITY_HEX[c.severity] || "#94a3b8";
            const radius = c.severity === "critical" ? 12 : c.severity === "high" ? 9 : 6;
            const marker = L.circleMarker(coords, {
              radius, fillColor: color, color, weight: 2, opacity: 0.9, fillOpacity: 0.4,
            }).addTo(mapInstanceRef.current!);
            marker.bindPopup(
              `<div style="font-family:system-ui;font-size:13px;">
                <strong style="color:${color}">${(c.severity || "").toUpperCase()}</strong><br/>
                <span style="color:#94a3b8">${c.intent}</span><br/>
                <span style="color:#64748b;font-size:11px">${(c.transcript || "").slice(0, 100)}</span>
              </div>`
            );
            markersRef.current.set(c.call_id, marker);
            break;
          }
        }
      });
    });
  }, [calls]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <h2 className="text-sm font-semibold text-slate-400 mb-3">Crisis Map</h2>
      <div ref={mapRef} className="h-[380px] rounded-lg border border-slate-800 relative z-0" />
    </div>
  );
}
