/**
 * HUD Layout — absolute overlay that sits on top of the Cesium canvas.
 *
 * DOM layer order (z-index):
 *   0 – Cesium canvas  (position:fixed, inset-0 via Viewer full prop)
 *   10 – this overlay  (position:absolute, inset-0, pointer-events:none)
 *        ↳ individual interactive regions set pointer-events:auto
 *
 * Layout zones:
 *   Top-left    : Brand header
 *   Top-right   : Live stats + legend
 *   Right-center: City details panel (slides in on selection)
 *   Bottom      : Time scrubber
 */

import { AnimatePresence } from "framer-motion";
import { useQueryClient } from "@tanstack/react-query";
import { GlassPanel } from "./GlassPanel";
import { CityDetailsPanel } from "./CityDetailsPanel";
import { ComparisonPanel } from "./ComparisonPanel";
import { ScoreLegend } from "../Globe/CesiumViewer";
import { useAppStore } from "../../store/useAppStore";
import { useCities, useCityScores } from "../../api/hooks";
import { formatDate, useMediaQuery, cn } from "../../lib/utils";

// ------------------------------------------------------------------ //
// Top-left brand bar                                                   //
// ------------------------------------------------------------------ //

function BrandBar() {
  const apiOffline = useAppStore((s) => s.apiOffline);
  const queryClient = useQueryClient();

  return (
    <GlassPanel
      accent
      className="pointer-events-auto px-4 py-2.5 flex items-center gap-3"
    >
      {/* Animated indicator dot */}
      <span className="relative flex h-2 w-2">
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${apiOffline ? "bg-red-500" : "bg-hud-accent"} opacity-60`} />
        <span className={`relative inline-flex rounded-full h-2 w-2 ${apiOffline ? "bg-red-500" : "bg-hud-accent"}`} />
      </span>
      <span className="text-sm font-semibold tracking-wide text-slate-100">
        Our City Health
      </span>
      {apiOffline ? (
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ["cities"] })}
          className="text-[10px] text-red-400 font-mono uppercase hover:text-red-300 transition-colors"
        >
          API OFFLINE · Retry
        </button>
      ) : (
        <span className="text-[10px] text-slate-600 font-mono uppercase">
          v2 · Geospatial Intelligence
        </span>
      )}
    </GlassPanel>
  );
}

// ------------------------------------------------------------------ //
// Top-right info panel                                                 //
// ------------------------------------------------------------------ //

function InfoPanel() {
  const { selectedDate } = useAppStore();
  const { data: cities = [] } = useCities();
  const { data: scores = [], isLoading } = useCityScores(selectedDate);

  const coveredCount = scores.length;
  const totalCount = cities.length;

  return (
    <GlassPanel accent className="pointer-events-auto px-4 py-3 w-52">
      <p className="text-[9px] text-slate-600 uppercase tracking-widest mb-2">
        Globe status
      </p>
      <div className="space-y-1.5 mb-3">
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">Cities loaded</span>
          <span className="font-mono text-slate-200">{totalCount.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">With GDELT data</span>
          <span className="font-mono text-hud-accent">
            {isLoading ? "…" : coveredCount}
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">Viewing date</span>
          <span className="font-mono text-slate-300 text-[10px]">
            {formatDate(selectedDate)}
          </span>
        </div>
      </div>
      {/* Legend */}
      <div
        className="w-full h-px mb-3"
        style={{
          background:
            "linear-gradient(90deg, transparent, rgba(0,200,255,0.2), transparent)",
        }}
      />
      <ScoreLegend />
    </GlassPanel>
  );
}

// ------------------------------------------------------------------ //
// Main HUD overlay                                                     //
// ------------------------------------------------------------------ //

interface HudLayoutProps {
  /** TimeScrubber rendered as a child so Layout owns the bottom zone. */
  scrubber: React.ReactNode;
}

export function HudLayout({ scrubber }: HudLayoutProps) {
  const { selectedCityId, isCompareMode } = useAppStore();
  const isMobile = useMediaQuery("(max-width: 767px)");

  return (
    <div className="absolute inset-0 pointer-events-none z-10 flex flex-col">
      {/* ---- TOP ROW ---- */}
      <div className="flex items-start justify-between p-4 gap-3">
        <BrandBar />
        {!isMobile && <InfoPanel />}
      </div>

      {/* ---- MIDDLE ROW ---- */}
      <div
        className={cn(
          "flex-1 min-h-0 flex overflow-hidden",
          isMobile
            ? "items-end justify-center pb-2 px-2"
            : "items-start justify-end pr-4 py-2",
        )}
      >
        <AnimatePresence mode="wait">
          {isCompareMode ? (
            <ComparisonPanel key="compare" />
          ) : (
            selectedCityId && <CityDetailsPanel key={selectedCityId} />
          )}
        </AnimatePresence>
      </div>

      {/* ---- BOTTOM ROW (time scrubber) ---- */}
      <div className="p-4 pointer-events-auto">{scrubber}</div>
    </div>
  );
}
