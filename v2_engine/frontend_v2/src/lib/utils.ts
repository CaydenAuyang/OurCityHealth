import { useState, useEffect } from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format an ISO date string (YYYY-MM-DD) to a human-readable label.
 *
 * `new Date("2023-01-15")` parses as UTC midnight, then `.toLocaleDateString`
 * converts to local time — in any timezone west of UTC that produces Jan 14.
 * Fix: construct explicitly in UTC and force the formatter to UTC as well.
 */
export function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  const d = new Date(Date.UTC(year, month - 1, day));
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

/**
 * Map a 0-100 stability score to a CSS colour string via continuous gradient.
 * Returns an `rgb()` string (compatible with Cesium's Color.fromCssColorString).
 * No-data → white so unscored dots render nearly invisible at low alpha.
 */
export function scoreToHex(score: number | null | undefined): string {
  if (score == null) return "#ffffff";

  const stops = [
    { score: 0, r: 220, g: 38, b: 38 },
    { score: 20, r: 249, g: 115, b: 22 },
    { score: 40, r: 234, g: 179, b: 8 },
    { score: 50, r: 132, g: 204, b: 22 },
    { score: 65, r: 34, g: 197, b: 94 },
    { score: 80, r: 16, g: 185, b: 129 },
    { score: 100, r: 6, g: 214, b: 160 },
  ];

  const clamped = Math.max(0, Math.min(100, score));

  let lower = stops[0];
  let upper = stops[stops.length - 1];
  for (let i = 0; i < stops.length - 1; i++) {
    if (clamped >= stops[i].score && clamped <= stops[i + 1].score) {
      lower = stops[i];
      upper = stops[i + 1];
      break;
    }
  }

  const t =
    upper.score === lower.score
      ? 0
      : (clamped - lower.score) / (upper.score - lower.score);
  const r = Math.round(lower.r + t * (upper.r - lower.r));
  const g = Math.round(lower.g + t * (upper.g - lower.g));
  const b = Math.round(lower.b + t * (upper.b - lower.b));

  return `rgb(${r},${g},${b})`;
}

/** Map a 0-100 stability score to a Tailwind text colour class. */
export function scoreToTextClass(score: number | null | undefined): string {
  if (score == null) return "text-slate-400";
  if (score >= 65) return "text-green-400";
  if (score >= 35) return "text-yellow-300";
  return "text-red-400";
}

/**
 * Convert a 2-letter ISO country code to a flag emoji.
 * Regional indicator symbols start at U+1F1E6 for 'A'.
 */
export function countryFlag(code: string): string {
  if (!code || code.length !== 2) return "";
  const upper = code.toUpperCase();
  return String.fromCodePoint(
    ...[...upper].map((c) => 0x1f1e6 + c.charCodeAt(0) - 65),
  );
}

/** Format a number with commas. */
export function formatPopulation(n: number): string {
  return n.toLocaleString("en-US");
}

/** Clamp a number between min and max. */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Convert a Date to YYYY-MM-DD using UTC components.
 *
 * `.toISOString().slice(0,10)` is already UTC, but using getUTC* methods
 * makes the intent explicit and avoids any future confusion.
 */
export function toIsoDate(d: Date): string {
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);
  useEffect(() => {
    const mql = window.matchMedia(query);
    setMatches(mql.matches);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [query]);
  return matches;
}
