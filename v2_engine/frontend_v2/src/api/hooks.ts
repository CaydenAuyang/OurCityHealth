import { useQuery } from "@tanstack/react-query";
import { apiClient } from "./client";

/** All 1,000+ cities — fetched once, stale-forever (cities don't move). */
export function useCities() {
  return useQuery({
    queryKey: ["cities"],
    queryFn: () => apiClient.getCities(),
    staleTime: Infinity,
    gcTime: Infinity,
  });
}

/**
 * Stability scores for all cities near `date`.
 * Refetches whenever `date` changes (powers the time-machine globe).
 */
export function useCityScores(date: string) {
  return useQuery({
    queryKey: ["city-scores", date],
    queryFn: () => apiClient.getCityScores(date),
    staleTime: 5 * 60 * 1000,
    enabled: !!date,
  });
}

/**
 * Full LLM health score for one city.
 * Only enabled when a city is selected (cityId !== null).
 */
export function useCityScore(cityId: string | null, date: string) {
  return useQuery({
    queryKey: ["city-score", cityId, date],
    queryFn: () => apiClient.getCityScore(cityId!, date),
    enabled: !!cityId,
    staleTime: 6 * 60 * 60 * 1000, // matches Redis 6h TTL
    retry: 1,
  });
}

/** Data coverage — fetched once (dates don't change mid-session). */
export function useDataCoverage() {
  return useQuery({
    queryKey: ["data-coverage"],
    queryFn: () => apiClient.getDataCoverage(),
    staleTime: Infinity,
    gcTime: Infinity,
  });
}

/** District boundaries for a city — only fetches when enabled. */
export function useDistricts(cityId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["districts", cityId],
    queryFn: () => apiClient.getDistricts(cityId!),
    enabled: !!cityId && enabled,
    staleTime: Infinity,
    gcTime: Infinity,
  });
}

/** Source breakdown for a city — GKG articles, tiers, themes, entities. */
export function useSources(
  cityId: string | null,
  start: string,
  end: string,
) {
  return useQuery({
    queryKey: ["sources", cityId, start, end],
    queryFn: () => apiClient.getSources(cityId!, start, end),
    enabled: !!cityId && !!start && !!end,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * GDELT daily stats history for sparklines.
 * Fetches 90 days ending at `endDate`.
 */
export function useCityHistory(cityId: string | null, endDate: string) {
  const start = endDate
    ? new Date(new Date(endDate).getTime() - 90 * 24 * 60 * 60 * 1000)
        .toISOString()
        .slice(0, 10)
    : "";

  return useQuery({
    queryKey: ["city-history", cityId, endDate],
    queryFn: () => apiClient.getCityHistory(cityId!, start, endDate),
    enabled: !!cityId && !!endDate,
    staleTime: 5 * 60 * 1000,
    retry: false, // 404 = no data, don't retry
  });
}
