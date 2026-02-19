// ------------------------------------------------------------------ //
// API response types — mirror the Pydantic schemas in backend_v2     //
// ------------------------------------------------------------------ //

export interface City {
  id: string;
  name: string;
  country_code: string;
  population: number;
  latitude: number;
  longitude: number;
}

export interface CityScoreRow {
  city_id: string;
  stability_score: number;
  day: string; // YYYY-MM-DD
}

// ---- from DimensionScore schema (V2.2) ---- //
export interface DimensionScore {
  dimension: string;
  score: number;
  confidence: number;
  evidence_snippets: string[];
  reasoning: string;
  citations: string[];
  score_delta?: number | null;
  causal_driver?: string | null;
}

// ---- from KeyEvent schema (V2.1) ---- //
export interface KeyEvent {
  date: string;
  description: string;
  actors: string[];
  impact: "positive" | "negative" | "neutral";
  goldstein_scale: number;
  source_url: string | null;
}

// ---- from RiskOrStrength schema (V2.2) ---- //
export interface RiskOrStrength {
  summary: string;
  supporting_event_count: number;
  date_range: string;
  citations: string[];
  source_tiers?: number[];
}

// ---- from CityHealthScore schema (V2.2) ---- //
export interface CityHealthScore {
  city_id: string;
  city_name: string;
  scored_date: string;
  generated_at: string;
  overall_score: number;
  overall_confidence: number;
  dimensions: DimensionScore[];
  /** V2.1 structured; may be plain string in old cached responses. */
  top_risks: (RiskOrStrength | string)[];
  top_strengths: (RiskOrStrength | string)[];
  data_sources: string[];
  gdelt_event_count: number;
  gdelt_avg_goldstein: number;
  key_events: KeyEvent[];
  analyst_summary: string;
  // V2.2 intelligence metadata
  total_articles_analyzed?: number;
  unique_sources_analyzed?: number;
  top_entities?: string[];
  dominant_themes?: string[];
  source_bias_note?: string | null;
  previous_overall_score?: number | null;
  score_delta?: number | null;
  dimension_deltas?: Record<string, number>;
}

// ---- from DailyStatsRow schema (Phase 3) ---- //
export interface DailyStatsRow {
  day: string;
  city_id: string;
  avg_goldstein: number;
  total_mentions: number;
  event_count: number;
  stability_score: number;
  verbal_cooperation_count: number;
  material_cooperation_count: number;
  verbal_conflict_count: number;
  material_conflict_count: number;
  unique_sources: number;
}

// ---- Data coverage for timeline indicator ---- //

export interface CoverageDay {
  date: string;
  city_count: number;
}

export interface CoverageResponse {
  coverage: CoverageDay[];
  min_date: string;
  max_date: string;
}

// ---- Source intelligence (V2.2) ---- //

export interface SourceInfo {
  name: string;
  tier: number;
  article_count: number;
  avg_tone: number;
  themes: string[];
  sample_urls: string[];
}

export interface ThemeCount {
  theme: string;
  count: number;
}

export interface CitySourcesResponse {
  city_id: string;
  city_name: string;
  date_range: { start: string; end: string };
  total_articles: number;
  sources: SourceInfo[];
  theme_distribution: ThemeCount[];
  top_persons: string[];
  top_organizations: string[];
}

// ---- District GeoJSON ---- //

export interface DistrictProperties {
  name: string;
  district_id: string;
}

export interface DistrictFeature {
  type: "Feature";
  properties: DistrictProperties;
  geometry: Record<string, unknown>;
}

export interface DistrictFeatureCollection {
  type: "FeatureCollection";
  features: DistrictFeature[];
}
