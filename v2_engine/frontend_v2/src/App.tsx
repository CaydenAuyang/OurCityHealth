/**
 * App — root component.
 *
 * Layout (desktop):
 *   ┌──────────┬──────────────────────────────┐
 *   │ Sidebar  │          Cesium Globe         │
 *   │  320 px  │       (fills remaining)       │
 *   │          │   ┌─── HudLayout overlay ──┐  │
 *   │          │   │ Brand    Info/Legend    │  │
 *   │          │   │         Details panel → │  │
 *   │          │   │  ── Time Scrubber ──   │  │
 *   │          │   └────────────────────────┘  │
 *   └──────────┴──────────────────────────────┘
 */

import { useEffect, useRef } from "react";
import { CesiumGlobe } from "./components/Globe/CesiumViewer";
import { HudLayout } from "./components/HUD/Layout";
import { TimeScrubber } from "./components/Timeline/TimeScrubber";
import { Sidebar } from "./components/Sidebar/Sidebar";
import { KeyboardShortcuts } from "./components/HUD/KeyboardShortcuts";
import Toast from "./components/HUD/Toast";
import { searchInputRef } from "./components/Sidebar/CitySearch";
import { useAppStore } from "./store/useAppStore";
import { useCities, useCityScores } from "./api/hooks";

const DEFAULT_DATE = "2023-01-15";

export default function App() {
  const { data: cities = [], isLoading: citiesLoading } = useCities();
  const selectedDate = useAppStore((s) => s.selectedDate);
  const { data: scores = [] } = useCityScores(selectedDate);

  // Build sorted list of city IDs that have scores for [ / ] cycling
  const scoredCityIdsRef = useRef<string[]>([]);
  useEffect(() => {
    scoredCityIdsRef.current = scores.map((s) => s.city_id).sort();
  }, [scores]);

  // ------- URL state: parse on mount ------- //
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const dateParam = params.get("date");
    const cityParam = params.get("city");
    if (dateParam) useAppStore.getState().setSelectedDate(dateParam);
    if (cityParam) useAppStore.getState().setSelectedCity(cityParam, "");
  }, []);

  // ------- URL state: sync on change ------- //
  const selectedCityId = useAppStore((s) => s.selectedCityId);
  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedCityId) params.set("city", selectedCityId);
    if (selectedDate !== DEFAULT_DATE) params.set("date", selectedDate);
    const str = params.toString();
    const url = str ? `?${str}` : window.location.pathname;
    window.history.replaceState({}, "", url);
  }, [selectedCityId, selectedDate]);

  // ------- Keyboard shortcuts ------- //
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      const inInput = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";

      const state = useAppStore.getState();

      if (e.key === "Escape") {
        e.preventDefault();
        if (state.showShortcuts) {
          state.toggleShortcuts();
        } else if (state.selectedCityId) {
          state.setSelectedCity(null);
        }
        return;
      }

      if (e.key === "?" && !inInput) {
        e.preventDefault();
        state.toggleShortcuts();
        return;
      }

      if (e.key === "/" && !inInput) {
        e.preventDefault();
        searchInputRef.current?.focus();
        return;
      }

      if ((e.key === "f" || e.key === "F") && !inInput) {
        state.toggleSidebar();
        return;
      }

      if (e.key === " " && !inInput) {
        e.preventDefault();
        state.setIsPlaying(!state.isPlaying);
        return;
      }

      if ((e.key === "[" || e.key === "]") && !inInput) {
        const ids = scoredCityIdsRef.current;
        if (ids.length === 0) return;
        const currentIdx = state.selectedCityId
          ? ids.indexOf(state.selectedCityId)
          : -1;
        let nextIdx: number;
        if (e.key === "]") {
          nextIdx = currentIdx < ids.length - 1 ? currentIdx + 1 : 0;
        } else {
          nextIdx = currentIdx > 0 ? currentIdx - 1 : ids.length - 1;
        }
        const nextId = ids[nextIdx];
        const city = cities.find((c) => c.id === nextId);
        state.setSelectedCity(nextId, city?.name ?? "");
        return;
      }
    };

    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [cities]);

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-black flex">
      <Sidebar />

      <div className="relative flex-1 h-full min-w-0">
        {/* 3D Globe */}
        <div className="absolute inset-0 z-0">
          <CesiumGlobe />
        </div>

        {/* Loading overlay */}
        {citiesLoading && (
          <div className="absolute inset-0 z-20 flex items-center justify-center pointer-events-none">
            <div
              className="px-6 py-4 rounded-xl font-mono text-sm text-slate-300 flex items-center gap-3"
              style={{
                background: "rgba(5,10,25,0.85)",
                backdropFilter: "blur(16px)",
                border: "1px solid rgba(0,200,255,0.15)",
              }}
            >
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-hud-accent animate-pulse" />
              Loading 1,000 cities…
            </div>
          </div>
        )}

        {/* HUD overlay */}
        <HudLayout scrubber={<TimeScrubber />} />
      </div>

      {/* Floating layers */}
      <KeyboardShortcuts />
      <Toast />
    </div>
  );
}
