import { useState, useMemo, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

import { GlassPanel } from "../HUD/GlassPanel";
import { HudDivider } from "../HUD/GlassPanel";
import { CitySearch } from "./CitySearch";
import { CityList } from "./CityList";
import { FilterControls, type SortKey, type PopFilter } from "./FilterControls";
import { useCities, useCityScores } from "../../api/hooks";
import { useAppStore } from "../../store/useAppStore";
import { useMediaQuery } from "../../lib/utils";
import type { City } from "../../api/types";

const POP_THRESHOLDS: Record<PopFilter, number> = {
  all: 0,
  "10m": 10_000_000,
  "5m": 5_000_000,
  "1m": 1_000_000,
};

export function Sidebar() {
  const { selectedDate, selectedCityId, sidebarOpen, toggleSidebar, setSelectedCity } =
    useAppStore();
  const { data: cities = [] } = useCities();
  const { data: scores = [] } = useCityScores(selectedDate);

  const scoresMap = useMemo(() => {
    const map: Record<string, number> = {};
    scores.forEach((s) => {
      map[s.city_id] = s.stability_score;
    });
    return map;
  }, [scores]);

  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("pop-desc");
  const [popFilter, setPopFilter] = useState<PopFilter>("all");
  const [dataOnly, setDataOnly] = useState(false);

  // Height measurement for the virtualized list.
  //
  // BUG-HISTORY: Originally used `useRef` + `useEffect([])`. Because the
  // sidebar's inner div is wrapped in `<AnimatePresence>`, every close
  // unmounts the ref target and every reopen mounts a *new* one. The
  // observer was only attached on first mount so the new node was never
  // measured, and `listHeight` stayed at the minimum (100px), which fits
  // exactly two rows at the 52px row height. Result: only Shanghai +
  // Beijing showed up after reopening the sidebar.
  //
  // Fixed by using a callback ref, which fires on every node change so we
  // can re-attach the observer. We also gate small heights observed during
  // the close animation, so the dying node can't write a tiny value.
  const [listContainer, setListContainer] = useState<HTMLDivElement | null>(null);
  const [listHeight, setListHeight] = useState(400);

  useEffect(() => {
    if (!listContainer) return;
    const measure = () => {
      const h = listContainer.getBoundingClientRect().height;
      if (h > 100) setListHeight(h);
    };
    measure(); // initial size before any resize event fires
    const observer = new ResizeObserver(() => measure());
    observer.observe(listContainer);
    return () => observer.disconnect();
  }, [listContainer]);

  const filteredCities = useMemo(() => {
    const lowerQ = query.toLowerCase().trim();
    const threshold = POP_THRESHOLDS[popFilter];

    let result: City[] = cities;

    if (lowerQ) {
      result = result.filter(
        (c) =>
          c.name.toLowerCase().includes(lowerQ) ||
          c.country_code.toLowerCase().includes(lowerQ),
      );
    }
    if (threshold > 0) {
      result = result.filter((c) => c.population >= threshold);
    }
    if (dataOnly) {
      result = result.filter((c) => scoresMap[c.id] != null);
    }

    result = [...result];
    switch (sortKey) {
      case "name-asc":
        result.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case "name-desc":
        result.sort((a, b) => b.name.localeCompare(a.name));
        break;
      case "pop-desc":
        result.sort((a, b) => b.population - a.population);
        break;
      case "pop-asc":
        result.sort((a, b) => a.population - b.population);
        break;
      case "score-desc":
        result.sort(
          (a, b) => (scoresMap[b.id] ?? -1) - (scoresMap[a.id] ?? -1),
        );
        break;
      case "score-asc":
        result.sort(
          (a, b) => (scoresMap[a.id] ?? 999) - (scoresMap[b.id] ?? 999),
        );
        break;
    }

    return result;
  }, [cities, query, sortKey, popFilter, dataOnly, scoresMap]);

  const handleSelect = useCallback(
    (id: string, name: string) => {
      setSelectedCity(id, name);
    },
    [setSelectedCity],
  );

  const isMobile = useMediaQuery("(max-width: 767px)");

  return (
    <>
      {/* Collapsed toggle tab */}
      {!sidebarOpen && !isMobile && (
        <button
          onClick={toggleSidebar}
          className="fixed left-0 top-1/2 -translate-y-1/2 z-20
                     glass-panel rounded-r-lg rounded-l-none px-1.5 py-4
                     text-slate-500 hover:text-hud-accent transition-colors
                     pointer-events-auto"
          aria-label="Open sidebar"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Mobile collapsed bar */}
      {!sidebarOpen && isMobile && (
        <button
          onClick={toggleSidebar}
          className="fixed bottom-0 left-0 right-0 z-30
                     glass-panel rounded-t-lg rounded-b-none px-4 py-2
                     text-slate-500 hover:text-hud-accent transition-colors
                     pointer-events-auto flex items-center justify-center gap-2"
          aria-label="Open city list"
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
          </svg>
          <span className="text-[10px] font-mono uppercase tracking-wider">
            {filteredCities.length.toLocaleString()} cities
          </span>
        </button>
      )}

      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={isMobile ? { y: "100%", opacity: 0 } : { x: -320, opacity: 0 }}
            animate={isMobile ? { y: 0, opacity: 1 } : { x: 0, opacity: 1 }}
            exit={isMobile ? { y: "100%", opacity: 0 } : { x: -320, opacity: 0 }}
            transition={{ type: "spring", stiffness: 350, damping: 35 }}
            className={
              isMobile
                ? "fixed bottom-0 left-0 right-0 z-30 h-[50vh] pointer-events-auto"
                : "relative z-20 w-[260px] lg:w-80 h-full shrink-0 pointer-events-auto"
            }
          >
            <GlassPanel
              accent
              className={`h-full flex flex-col overflow-hidden ${isMobile ? "rounded-t-lg rounded-b-none" : "rounded-l-none"}`}
            >
              {/* Header */}
              <div className="px-4 pt-3.5 pb-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <svg
                    className="w-3.5 h-3.5 text-hud-accent"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"
                    />
                  </svg>
                  <span className="text-[9px] text-slate-500 uppercase tracking-widest font-mono">
                    City Explorer
                  </span>
                </div>
                <button
                  onClick={toggleSidebar}
                  className="text-slate-600 hover:text-slate-300 transition-colors"
                  aria-label="Close sidebar"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M15 19l-7-7 7-7"
                    />
                  </svg>
                </button>
              </div>

              {/* Search */}
              <div className="px-3 pb-2">
                <CitySearch value={query} onChange={setQuery} />
              </div>

              {/* Filters */}
              <div className="px-4 pb-2">
                <FilterControls
                  sortKey={sortKey}
                  onSortChange={setSortKey}
                  popFilter={popFilter}
                  onPopFilterChange={setPopFilter}
                  dataOnly={dataOnly}
                  onDataOnlyChange={setDataOnly}
                />
              </div>

              <HudDivider />

              {/* Result count */}
              <div className="px-4 pb-1.5">
                <span className="text-[10px] text-slate-600 font-mono">
                  {filteredCities.length.toLocaleString()} cities
                </span>
              </div>

              {/* Virtualized city list */}
              <div ref={setListContainer} className="flex-1 min-h-0">
                <CityList
                  cities={filteredCities}
                  scoresMap={scoresMap}
                  selectedCityId={selectedCityId}
                  onSelect={handleSelect}
                  height={listHeight}
                />
              </div>
            </GlassPanel>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
