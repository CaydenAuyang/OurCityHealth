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

async function apiFetch<T>(path: string): Promise<T> {
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

export const apiClient = {
  getCities(): Promise<City[]> {
    return apiFetch("/api/v2/cities");
  },

  getCityScores(date: string, windowDays = 30): Promise<CityScoreRow[]> {
    return apiFetch(`/api/v2/cities/scores?date=${date}&window_days=${windowDays}`);
  },

  getCityScore(cityId: string, date: string): Promise<CityHealthScore> {
    return apiFetch(`/api/v2/score/${cityId}?date=${date}`);
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
    return apiFetch("/api/v2/data-coverage");
  },

  getDistricts(cityId: string): Promise<DistrictFeatureCollection> {
    return apiFetch(`/api/v2/cities/${cityId}/districts`);
  },

  getSources(
    cityId: string,
    start: string,
    end: string,
  ): Promise<CitySourcesResponse> {
    return apiFetch(
      `/api/v2/sources/${cityId}?start=${start}&end=${end}`,
    );
  },
};
