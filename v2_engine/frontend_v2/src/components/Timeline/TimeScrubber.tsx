/**
 * TimeScrubber — horizontal date slider at the bottom of the HUD.
 *
 * Features:
 *   - Data-coverage bar behind the slider track (cyan where data exists)
 *   - Play/pause auto-advance with configurable speed (1x/2x/5x)
 *   - Debounced date commit to Zustand (300 ms)
 */

import { useCallback, useRef, useState, useEffect, useMemo } from "react";
import { GlassPanel } from "../HUD/GlassPanel";
import { useAppStore } from "../../store/useAppStore";
import { useDataCoverage } from "../../api/hooks";
import { toIsoDate, formatDate, clamp, useMediaQuery } from "../../lib/utils";

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

  const [localValue, setLocalValue] = useState(() => daysFromDate(selectedDate));

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

          <span className="text-xs font-mono text-hud-accent">
            {formatDate(selectedDate)}
          </span>
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
