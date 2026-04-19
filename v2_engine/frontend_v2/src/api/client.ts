import { useAppStore } from "../store/useAppStore";
import type {
  City,
  CityScoreRow,
  CityHealthScore,
  DailyStatsRow,
  CoverageResponse,
  DistrictFeatureCollection,
  CitySourcesResponse,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "";
const SNAPSHOT_BASE = `${import.meta.env.BASE_URL}snapshot`;

// --------------------------------------------------------------------- //
// Snapshot manifest — loaded once, used to resolve nearest-date lookups
// --------------------------------------------------------------------- //

interface SnapshotManifest {
  generated_at: string;
  city_count: number;
  color_dates: string[];
  scored_pairs: { city_id: string; date: string }[];
  scored_dates_by_city: Record<string, string[]>;
  history_city_ids: string[];
}

let _manifestPromise: Promise<SnapshotManifest | null> | null = null;

function loadManifest(): Promise<SnapshotManifest | null> {
  if (_manifestPromise) return _manifestPromise;
  _manifestPromise = fetch(`${SNAPSHOT_BASE}/manifest.json`)
    .then((r) => (r.ok ? (r.json() as Promise<SnapshotManifest>) : null))
    .catch(() => null);
  return _manifestPromise;
}

/** Pick the date in `available` closest to `target`. Returns null if none. */
function nearestDate(target: string, available: string[]): string | null {
  if (available.length === 0) return null;
  const t = new Date(target).getTime();
  let best = available[0];
  let bestDiff = Math.abs(new Date(best).getTime() - t);
  for (let i = 1; i < available.length; i++) {
    const diff = Math.abs(new Date(available[i]).getTime() - t);
    if (diff < bestDiff) {
      best = available[i];
      bestDiff = diff;
    }
  }
  return best;
}

// --------------------------------------------------------------------- //
// Low-level fetchers
// --------------------------------------------------------------------- //

async function snapshotFetch<T>(filename: string): Promise<T | null> {
  try {
    const res = await fetch(`${SNAPSHOT_BASE}/${filename}`);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

async function apiFetch<T>(path: string): Promise<T> {
  if (!BASE) {
    throw new Error(`No API base configured; ${path} unavailable in static demo mode`);
  }
  try {
    const res = await fetch(`${BASE}${path}`);
    useAppStore.getState().setApiOffline(false);
    if (!res.ok) {
      const body = await res.text().catch(() => res.statusText);
      throw new Error(`API ${path} → ${res.status}: ${body}`);
    }
    return res.json() as Promise<T>;
  } catch (err) {
    if (err instanceof TypeError) {
      useAppStore.getState().setApiOffline(true);
    }
    throw err;
  }
}

async function snapshotOrApi<T>(snapshotFile: string, apiPath: string): Promise<T> {
  const snap = await snapshotFetch<T>(snapshotFile);
  if (snap !== null) return snap;
  return apiFetch<T>(apiPath);
}

// --------------------------------------------------------------------- //
// Cached history (sliced client-side from per-city full history file)
// --------------------------------------------------------------------- //

const _historyCache = new Map<string, DailyStatsRow[] | null>();

async function loadCityHistory(cityId: string): Promise<DailyStatsRow[] | null> {
  if (_historyCache.has(cityId)) return _historyCache.get(cityId) ?? null;
  const data = await snapshotFetch<DailyStatsRow[]>(`history-${cityId}.json`);
  _historyCache.set(cityId, data);
  return data;
}

// --------------------------------------------------------------------- //
// Public client
// --------------------------------------------------------------------- //

export const apiClient = {
  getCities(): Promise<City[]> {
    return snapshotOrApi<City[]>("cities.json", "/api/v2/cities");
  },

  getCityScores(date: string, windowDays = 30): Promise<CityScoreRow[]> {
    return snapshotOrApi<CityScoreRow[]>(
      `cities-scores-${date}.json`,
      `/api/v2/cities/scores?date=${date}&window_days=${windowDays}`,
    );
  },

  /**
   * LLM-evaluated city score. If we don't have an exact (city,date) snapshot,
   * fall back to the nearest scored date for this city — far more useful than
   * a "Score unavailable" error in static demo mode.
   */
  async getCityScore(cityId: string, date: string): Promise<CityHealthScore> {
    const exact = await snapshotFetch<CityHealthScore>(
      `score-${cityId}-${date}.json`,
    );
    if (exact !== null) return exact;

    const manifest = await loadManifest();
    const available = manifest?.scored_dates_by_city?.[cityId] ?? [];
    const nearest = nearestDate(date, available);
    if (nearest && nearest !== date) {
      const fallback = await snapshotFetch<CityHealthScore>(
        `score-${cityId}-${nearest}.json`,
      );
      if (fallback !== null) return fallback;
    }

    // Last resort: live API (will throw in static-only mode)
    return apiFetch<CityHealthScore>(
      `/api/v2/score/${cityId}?date=${date}`,
    );
  },

  /**
   * 90-day sparkline. The snapshot ships full per-city history (5-year window);
   * we slice to the requested range client-side. This means the sparkline works
   * for any date the user picks, not just snapshotted ones.
   */
  async getCityHistory(
    cityId: string,
    start: string,
    end: string,
    limit = 365,
  ): Promise<DailyStatsRow[]> {
    const all = await loadCityHistory(cityId);
    if (all !== null) {
      const filtered = all.filter((r) => r.day >= start && r.day <= end);
      return filtered.slice(-limit);
    }
    return apiFetch<DailyStatsRow[]>(
      `/api/v2/score/${cityId}/history?start=${start}&end=${end}&limit=${limit}`,
    );
  },

  getDataCoverage(): Promise<CoverageResponse> {
    return snapshotOrApi<CoverageResponse>(
      "data-coverage.json",
      "/api/v2/data-coverage",
    );
  },

  getDistricts(cityId: string): Promise<DistrictFeatureCollection> {
    return apiFetch(`/api/v2/cities/${cityId}/districts`);
  },

  /**
   * Source breakdown. Snapshots are keyed by the end-date (the date the user
   * is viewing). Falls back to the nearest scored date for the city.
   */
  async getSources(
    cityId: string,
    start: string,
    end: string,
  ): Promise<CitySourcesResponse> {
    const exact = await snapshotFetch<CitySourcesResponse>(
      `sources-${cityId}-${end}.json`,
    );
    if (exact !== null) return exact;

    const manifest = await loadManifest();
    const available = manifest?.scored_dates_by_city?.[cityId] ?? [];
    const nearest = nearestDate(end, available);
    if (nearest && nearest !== end) {
      const fallback = await snapshotFetch<CitySourcesResponse>(
        `sources-${cityId}-${nearest}.json`,
      );
      if (fallback !== null) return fallback;
    }

    return apiFetch<CitySourcesResponse>(
      `/api/v2/sources/${cityId}?start=${start}&end=${end}`,
    );
  },
};
