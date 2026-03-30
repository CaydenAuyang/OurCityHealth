/**
 * TimeScrubber — horizontal date slider at the bottom of the HUD.
 *
 * Features:
 *   - Data-coverage bar behind the slider track (cyan where data exists)
 *   - Play/pause auto-advance with configurable speed (1x/2x/5x)
 *   - Debounced date commit to Zustand (300 ms)
 *   - Calendar popup for exact date selection (click date label)
 */

import { useCallback, useRef, useState, useEffect, useMemo } from "react";
import { GlassPanel } from "../HUD/GlassPanel";
import { useAppStore } from "../../store/useAppStore";
import { useDataCoverage } from "../../api/hooks";
import { toIsoDate, formatDate, clamp, useMediaQuery } from "../../lib/utils";

const MONTH_NAMES = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December",
];
const DAY_NAMES = ["Su","Mo","Tu","We","Th","Fr","Sa"];

// ------------------------------------------------------------------ //
// Date math helpers                                                    //
// ------------------------------------------------------------------ //

const START = new Date("2020-01-01T00:00:00Z");

function totalDays(): number {
  return Math.floor((Date.now() - START.getTime()) / 86_400_000);
}

function daysFromDate(iso: string): number {
  const d = new Date(iso + "T00:00:00Z");
  return Math.max(0, Math.floor((d.getTime() - START.getTime()) / 86_400_000));
}

function dateFromDays(days: number): string {
  return toIsoDate(
    new Date(START.getTime() + clamp(days, 0, totalDays()) * 86_400_000),
  );
}

function yearTicks(): { label: string; pct: number }[] {
  const total = totalDays();
  const ticks: { label: string; pct: number }[] = [];
  const startYear = 2020;
  const endYear = new Date().getFullYear();
  for (let y = startYear; y <= endYear; y++) {
    const d = Math.floor(
      (new Date(`${y}-01-01T00:00:00Z`).getTime() - START.getTime()) /
        86_400_000,
    );
    if (d >= 0 && d <= total) {
      ticks.push({ label: String(y), pct: (d / total) * 100 });
    }
  }
  return ticks;
}

// ------------------------------------------------------------------ //
// Speed presets                                                        //
// ------------------------------------------------------------------ //

const SPEED_OPTIONS: { value: 1 | 2 | 5; label: string; ms: number }[] = [
  { value: 1, label: "1×", ms: 500 },
  { value: 2, label: "2×", ms: 250 },
  { value: 5, label: "5×", ms: 100 },
];

// ------------------------------------------------------------------ //
// Component                                                            //
// ------------------------------------------------------------------ //

export function TimeScrubber() {
  const {
    selectedDate,
    setSelectedDate,
    isPlaying,
    setIsPlaying,
    playbackSpeed,
    setPlaybackSpeed,
  } = useAppStore();
  const isMobile = useMediaQuery("(max-width: 767px)");
  const max = totalDays();

  const inputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();
  const intervalRef = useRef<ReturnType<typeof setInterval>>();
  const calRef = useRef<HTMLDivElement>(null);

  const [localValue, setLocalValue] = useState(() => daysFromDate(selectedDate));

  // ---- Calendar state ---- //
  const [showCalendar, setShowCalendar] = useState(false);
  const [calViewYear, setCalViewYear] = useState(() =>
    new Date(selectedDate + "T00:00:00Z").getUTCFullYear(),
  );
  const [calViewMonth, setCalViewMonth] = useState(() =>
    new Date(selectedDate + "T00:00:00Z").getUTCMonth(),
  );
  const [typedDate, setTypedDate] = useState(selectedDate);
  const [typeError, setTypeError] = useState(false);

  // Close calendar on outside click
  useEffect(() => {
    if (!showCalendar) return;
    const handler = (e: MouseEvent) => {
      if (calRef.current && !calRef.current.contains(e.target as Node)) {
        setShowCalendar(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [showCalendar]);

  const openCalendar = useCallback(() => {
    const d = new Date(selectedDate + "T00:00:00Z");
    setCalViewYear(d.getUTCFullYear());
    setCalViewMonth(d.getUTCMonth());
    setTypedDate(selectedDate);
    setTypeError(false);
    setShowCalendar((v) => !v);
  }, [selectedDate]);

  const commitCalendarDate = useCallback(
    (iso: string) => {
      setIsPlaying(false);
      clearTimeout(timerRef.current);
      setSelectedDate(iso);
      const days = daysFromDate(iso);
      setLocalValue(days);
      if (inputRef.current) {
        inputRef.current.style.setProperty("--progress", `${(days / max) * 100}%`);
      }
      setShowCalendar(false);
    },
    [setIsPlaying, setSelectedDate, max],
  );

  const handleTypedDate = useCallback(
    (val: string) => {
      setTypedDate(val);
      setTypeError(false);
      if (/^\d{4}-\d{2}-\d{2}$/.test(val)) {
        const d = new Date(val + "T00:00:00Z");
        if (!isNaN(d.getTime()) && d >= START && d.getTime() <= Date.now()) {
          setCalViewYear(d.getUTCFullYear());
          setCalViewMonth(d.getUTCMonth());
        } else {
          setTypeError(true);
        }
      }
    },
    [],
  );

  const handleTypedDateCommit = useCallback(() => {
    if (/^\d{4}-\d{2}-\d{2}$/.test(typedDate)) {
      const d = new Date(typedDate + "T00:00:00Z");
      if (!isNaN(d.getTime()) && d >= START && d.getTime() <= Date.now()) {
        commitCalendarDate(typedDate);
        return;
      }
    }
    setTypeError(true);
  }, [typedDate, commitCalendarDate]);

  const prevMonth = useCallback(() => {
    setCalViewMonth((m) => {
      if (m === 0) { setCalViewYear((y) => y - 1); return 11; }
      return m - 1;
    });
  }, []);

  const nextMonth = useCallback(() => {
    setCalViewMonth((m) => {
      if (m === 11) { setCalViewYear((y) => y + 1); return 0; }
      return m + 1;
    });
  }, []);

  // Coverage data for the track visualization
  const { data: coverageData } = useDataCoverage();
  const coverageSet = useMemo(() => {
    if (!coverageData?.coverage) return new Set<number>();
    const s = new Set<number>();
    for (const c of coverageData.coverage) {
      s.add(daysFromDate(c.date));
    }
    return s;
  }, [coverageData]);

  // Sorted coverage days for playback stepping
  const coverageDays = useMemo(() => {
    return Array.from(coverageSet).sort((a, b) => a - b);
  }, [coverageSet]);

  // Sync slider thumb when selectedDate changes externally
  useEffect(() => {
    setLocalValue(daysFromDate(selectedDate));
  }, [selectedDate]);

  // ---- Playback interval ---- //
  useEffect(() => {
    if (!isPlaying) {
      clearInterval(intervalRef.current);
      return;
    }

    const ms = SPEED_OPTIONS.find((s) => s.value === playbackSpeed)?.ms ?? 500;

    intervalRef.current = setInterval(() => {
      setLocalValue((prev) => {
        // Find next coverage day after current position
        const next = coverageDays.find((d) => d > prev);
        if (next == null) {
          // Reached end of coverage — pause
          setIsPlaying(false);
          return prev;
        }
        const iso = dateFromDays(next);
        setSelectedDate(iso);
        return next;
      });
    }, ms);

    return () => clearInterval(intervalRef.current);
  }, [isPlaying, playbackSpeed, coverageDays, setSelectedDate, setIsPlaying]);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const days = parseInt(e.target.value, 10);

      // Manual drag pauses playback
      if (isPlaying) setIsPlaying(false);

      setLocalValue(days);
      if (inputRef.current) {
        inputRef.current.style.setProperty(
          "--progress",
          `${(days / max) * 100}%`,
        );
      }

      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        setSelectedDate(dateFromDays(days));
      }, 300);
    },
    [max, setSelectedDate, isPlaying, setIsPlaying],
  );

  const togglePlay = useCallback(() => {
    setIsPlaying(!isPlaying);
  }, [isPlaying, setIsPlaying]);

  const localPct = max > 0 ? (localValue / max) * 100 : 0;
  const ticks = yearTicks();

  // Build coverage bar segments as CSS gradient
  const coverageGradient = useMemo(() => {
    if (coverageSet.size === 0 || max === 0) return "transparent";
    // Create a pixel-accurate gradient: cyan where data exists, transparent elsewhere
    const segments: string[] = [];
    let inCoverage = false;
    let startPct = 0;

    for (let d = 0; d <= max; d++) {
      const hasCoverage = coverageSet.has(d);
      if (hasCoverage && !inCoverage) {
        startPct = (d / max) * 100;
        inCoverage = true;
      } else if (!hasCoverage && inCoverage) {
        const endPct = (d / max) * 100;
        segments.push(
          `transparent ${startPct}%, rgba(0,212,255,0.3) ${startPct}%, rgba(0,212,255,0.3) ${endPct}%, transparent ${endPct}%`,
        );
        inCoverage = false;
      }
    }
    if (inCoverage) {
      const endPct = 100;
      segments.push(
        `transparent ${startPct}%, rgba(0,212,255,0.3) ${startPct}%, rgba(0,212,255,0.3) ${endPct}%, transparent ${endPct}%`,
      );
    }

    return segments.length > 0
      ? `linear-gradient(to right, ${segments.join(", ")})`
      : "transparent";
  }, [coverageSet, max]);

  return (
    <GlassPanel accent className="px-5 py-3.5">
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {/* Play/Pause button */}
          <button
            onClick={togglePlay}
            className="w-6 h-6 flex items-center justify-center rounded border border-white/10 hover:border-hud-accent/50 text-slate-500 hover:text-hud-accent transition-colors"
            aria-label={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? (
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16" />
                <rect x="14" y="4" width="4" height="16" />
              </svg>
            ) : (
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

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
              d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z"
            />
          </svg>
          <span className="text-[9px] text-slate-500 uppercase tracking-widest">
            Time machine
          </span>

          {isPlaying && (
            <span className="text-[9px] text-hud-accent font-mono animate-pulse">
              ▶ PLAYING
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Speed controls */}
          <div className="flex gap-0.5">
            {SPEED_OPTIONS.map((s) => (
              <button
                key={s.value}
                onClick={() => setPlaybackSpeed(s.value)}
                className={`text-[9px] font-mono px-1 py-0.5 rounded border transition-colors ${
                  playbackSpeed === s.value
                    ? "border-hud-accent/60 text-hud-accent bg-hud-accent/10"
                    : "border-white/10 text-slate-600 hover:text-slate-400"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>

          {/* Date display — click to open calendar */}
          <div className="relative" ref={calRef}>
            <button
              onClick={openCalendar}
              className={`text-xs font-mono px-2 py-0.5 rounded border transition-colors ${
                showCalendar
                  ? "text-hud-accent border-hud-accent/50 bg-hud-accent/10"
                  : "text-hud-accent border-white/10 hover:border-hud-accent/40"
              }`}
              title="Click to pick exact date"
            >
              {formatDate(selectedDate)}
              <span className="ml-1 text-[8px] opacity-50">▲</span>
            </button>

            {/* Calendar popup */}
            {showCalendar && (() => {
              const daysInMonth = new Date(Date.UTC(calViewYear, calViewMonth + 1, 0)).getUTCDate();
              const firstDow = new Date(Date.UTC(calViewYear, calViewMonth, 1)).getUTCDay();
              const selD = new Date(selectedDate + "T00:00:00Z");
              const todayIso = toIsoDate(new Date());
              const maxDate = new Date();

              const cells: (number | null)[] = [
                ...Array(firstDow).fill(null),
                ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
              ];
              // pad to full weeks
              while (cells.length % 7 !== 0) cells.push(null);

              return (
                <div
                  style={{
                    position: "absolute",
                    bottom: "calc(100% + 8px)",
                    right: 0,
                    width: "224px",
                    background: "rgba(8,13,26,0.97)",
                    border: "1px solid rgba(0,212,170,0.2)",
                    borderRadius: "12px",
                    backdropFilter: "blur(24px)",
                    padding: "12px",
                    zIndex: 100,
                    boxShadow: "0 -8px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(0,212,170,0.05)",
                  }}
                >
                  {/* Text input */}
                  <div style={{ marginBottom: "10px" }}>
                    <div style={{ fontSize: "0.55rem", fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)", marginBottom: "4px" }}>
                      TYPE DATE
                    </div>
                    <div style={{ display: "flex", gap: "6px" }}>
                      <input
                        type="text"
                        value={typedDate}
                        onChange={(e) => handleTypedDate(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleTypedDateCommit();
                          if (e.key === "Escape") setShowCalendar(false);
                        }}
                        placeholder="YYYY-MM-DD"
                        style={{
                          flex: 1,
                          background: "rgba(255,255,255,0.05)",
                          border: `1px solid ${typeError ? "rgba(239,68,68,0.5)" : "rgba(255,255,255,0.1)"}`,
                          borderRadius: "6px",
                          padding: "5px 8px",
                          fontSize: "0.65rem",
                          fontFamily: "monospace",
                          color: typeError ? "#EF4444" : "#00D4AA",
                          outline: "none",
                          width: "100%",
                        }}
                      />
                      <button
                        onClick={handleTypedDateCommit}
                        style={{
                          background: "rgba(0,212,170,0.15)",
                          border: "1px solid rgba(0,212,170,0.3)",
                          borderRadius: "6px",
                          padding: "5px 8px",
                          fontSize: "0.6rem",
                          color: "#00D4AA",
                          cursor: "pointer",
                          whiteSpace: "nowrap",
                        }}
                      >
                        Go
                      </button>
                    </div>
                    {typeError && (
                      <div style={{ fontSize: "0.52rem", color: "rgba(239,68,68,0.7)", marginTop: "3px" }}>
                        Invalid date — use YYYY-MM-DD
                      </div>
                    )}
                  </div>

                  {/* Divider */}
                  <div style={{ height: "1px", background: "rgba(255,255,255,0.07)", marginBottom: "10px" }} />

                  {/* Month navigation */}
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                    <button
                      onClick={prevMonth}
                      style={{ background: "none", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: "0.85rem", padding: "2px 6px", borderRadius: "4px" }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "#00D4AA")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.4)")}
                    >‹</button>
                    <span style={{ fontSize: "0.62rem", fontWeight: 700, color: "#fff", letterSpacing: "0.05em" }}>
                      {MONTH_NAMES[calViewMonth]} {calViewYear}
                    </span>
                    <button
                      onClick={nextMonth}
                      disabled={calViewYear > maxDate.getFullYear() || (calViewYear === maxDate.getFullYear() && calViewMonth >= maxDate.getMonth())}
                      style={{ background: "none", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: "0.85rem", padding: "2px 6px", borderRadius: "4px", opacity: (calViewYear > maxDate.getFullYear() || (calViewYear === maxDate.getFullYear() && calViewMonth >= maxDate.getMonth())) ? 0.2 : 1 }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "#00D4AA")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.4)")}
                    >›</button>
                  </div>

                  {/* Day name headers */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "2px", marginBottom: "4px" }}>
                    {DAY_NAMES.map((d) => (
                      <div key={d} style={{ textAlign: "center", fontSize: "0.5rem", fontWeight: 700, color: "rgba(255,255,255,0.25)", padding: "2px 0" }}>
                        {d}
                      </div>
                    ))}
                  </div>

                  {/* Day cells */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "2px" }}>
                    {cells.map((day, idx) => {
                      if (day === null) return <div key={idx} />;
                      const iso = `${calViewYear}-${String(calViewMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
                      const isSelected = iso === selectedDate;
                      const isToday = iso === todayIso;
                      const isFuture = new Date(iso + "T00:00:00Z") > maxDate;
                      const hasCov = coverageSet.has(daysFromDate(iso));

                      return (
                        <button
                          key={idx}
                          disabled={isFuture}
                          onClick={() => !isFuture && commitCalendarDate(iso)}
                          style={{
                            position: "relative",
                            textAlign: "center",
                            fontSize: "0.58rem",
                            padding: "4px 0",
                            borderRadius: "5px",
                            border: isToday ? "1px solid rgba(245,158,11,0.4)" : "1px solid transparent",
                            background: isSelected ? "rgba(0,212,170,0.25)" : "transparent",
                            color: isSelected ? "#00D4AA" : isFuture ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.7)",
                            cursor: isFuture ? "default" : "pointer",
                            fontWeight: isSelected ? 700 : 400,
                            transition: "background 0.1s, color 0.1s",
                          }}
                          onMouseEnter={(e) => { if (!isFuture && !isSelected) e.currentTarget.style.background = "rgba(0,212,170,0.1)"; }}
                          onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.background = "transparent"; }}
                        >
                          {day}
                          {hasCov && (
                            <span style={{ position: "absolute", bottom: "1px", left: "50%", transform: "translateX(-50%)", width: "3px", height: "3px", borderRadius: "50%", background: "#00D4AA", opacity: isSelected ? 1 : 0.5 }} />
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {/* Quick jumps */}
                  <div style={{ marginTop: "10px", display: "flex", gap: "4px", justifyContent: "flex-end" }}>
                    <button
                      onClick={() => commitCalendarDate(todayIso)}
                      style={{ fontSize: "0.5rem", padding: "3px 8px", borderRadius: "5px", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.5)", cursor: "pointer" }}
                    >Today</button>
                    <button
                      onClick={() => commitCalendarDate("2024-01-15")}
                      style={{ fontSize: "0.5rem", padding: "3px 8px", borderRadius: "5px", background: "rgba(0,212,170,0.08)", border: "1px solid rgba(0,212,170,0.15)", color: "rgba(0,212,170,0.7)", cursor: "pointer" }}
                    >Jan 2024</button>
                  </div>
                </div>
              );
            })()}
          </div>

          <button
            onClick={() => {
              clearTimeout(timerRef.current);
              setIsPlaying(false);
              setSelectedDate(toIsoDate(new Date()));
            }}
            className="text-[9px] text-slate-600 hover:text-hud-accent transition-colors border border-white/10 hover:border-hud-accent/40 rounded px-1.5 py-0.5 font-mono"
          >
            today
          </button>
        </div>
      </div>

      {/* Slider with coverage bar */}
      <div className="relative">
        {/* Coverage indicator — thin bar behind the slider */}
        <div
          className="absolute left-0 right-0 h-1 rounded-full"
          style={{
            top: "50%",
            transform: "translateY(-50%)",
            background: coverageGradient,
            pointerEvents: "none",
          }}
        />

        <input
          ref={inputRef}
          type="range"
          className="hud-slider w-full relative z-10"
          min={0}
          max={max}
          value={localValue}
          onChange={handleChange}
          style={{ "--progress": `${localPct}%` } as React.CSSProperties}
          aria-label="Select date"
        />

        {/* Year tick labels — hidden on mobile */}
        {!isMobile && (
          <div className="relative h-4 mt-1">
            {ticks.map(({ label, pct: p }) => (
              <span
                key={label}
                className="absolute text-[9px] text-slate-600 -translate-x-1/2 select-none"
                style={{ left: `${p}%` }}
              >
                {label}
              </span>
            ))}
          </div>
        )}
      </div>
    </GlassPanel>
  );
}
