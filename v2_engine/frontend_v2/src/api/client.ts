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

/**
 * Fetch a static snapshot file shipped with the build. Returns null on 404
 * so callers can fall back to the live API. Network errors also return null
 * (rather than flipping the offline flag) because snapshots are best-effort.
 */
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
    // No backend configured (static-only deploy). Surface a clear error so
    // callers can decide whether to recover or show an empty state.
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

/** Try the snapshot first, fall back to the live API. */
async function snapshotOrApi<T>(
  snapshotFile: string,
  apiPath: string,
): Promise<T> {
  const snap = await snapshotFetch<T>(snapshotFile);
  if (snap !== null) return snap;
  return apiFetch<T>(apiPath);
}

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

  getCityScore(cityId: string, date: string): Promise<CityHealthScore> {
    return snapshotOrApi<CityHealthScore>(
      `score-${cityId}-${date}.json`,
      `/api/v2/score/${cityId}?date=${date}`,
    );
  },

  getCityHistory(
    cityId: string,
    start: string,
    end: string,
    limit = 365,
  ): Promise<DailyStatsRow[]> {
    return apiFetch(
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

  getSources(
    cityId: string,
    start: string,
    end: string,
  ): Promise<CitySourcesResponse> {
    return snapshotOrApi<CitySourcesResponse>(
      `sources-${cityId}-${date_to_anchor(end)}.json`,
      `/api/v2/sources/${cityId}?start=${start}&end=${end}`,
    );
  },
};

/**
 * The sources snapshot is keyed by the end-date (the "anchor" date the user
 * is viewing). The hooks pass start = end - 90 days, so we just use end.
 */
function date_to_anchor(end: string): string {
  return end;
}
