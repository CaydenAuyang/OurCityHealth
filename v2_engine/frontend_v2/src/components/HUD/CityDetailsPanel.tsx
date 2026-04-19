/**
 * CityDetailsPanel — slides in from the right when a city is selected.
 *
 * Section order:
 *   1.  Header (name, date, close)
 *   2.  Score badges (Stability, Goldstein, Events) + overall delta
 *   3.  Intelligence metadata bar  [V2.2]
 *   4.  Analyst Summary
 *   5.  Entity tags  [V2.2]
 *   6.  Theme distribution  [V2.2]
 *   7.  Stability sparkline
 *   8.  Civic Dimensions (expandable bars, with per-dim delta + causal driver)
 *   9.  Top Risks (with tier badges)
 *  10.  Top Strengths (with tier badges)
 *  11.  Key Events
 *  12.  Media Landscape (collapsible)  [V2.2]
 */

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useQueryClient } from "@tanstack/react-query";
import { GlassPanel, HudDivider, StatBadge } from "./GlassPanel";
import { SourceBadge, TierCounts, extractDomain } from "./SourceBadge";
import { useCityHistory, useCityScore, useSources } from "../../api/hooks";
import { useAppStore } from "../../store/useAppStore";
import { scoreToHex, scoreToTextClass, formatDate, cn, toIsoDate } from "../../lib/utils";
import type { DimensionScore, KeyEvent, RiskOrStrength } from "../../api/types";

// ------------------------------------------------------------------ //
// URL parsing helpers                                                  //
// ------------------------------------------------------------------ //

function parseTextWithCitation(raw: string): { text: string; urls: string[] } {
  const urls: string[] = [];
  const cleaned = raw.replace(/\s*\[?(https?:\/\/[^\]\s]+)\]?\s*/g, (_, url) => {
    urls.push(url);
    return " ";
  });
  return { text: cleaned.replace(/\s+/g, " ").trim(), urls };
}

function SourceLinks({ urls }: { urls: string[] }) {
  if (urls.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2 pl-4">
      {urls.map((url, i) => (
        <a
          key={i}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[9px] text-hud-accent hover:underline"
        >
          {urls.length > 1 ? `Source ${i + 1} →` : "Source →"}
        </a>
      ))}
    </div>
  );
}

// ------------------------------------------------------------------ //
// Delta arrow helper                                                   //
// ------------------------------------------------------------------ //

function DeltaArrow({
  delta,
  size = "sm",
}: {
  delta: number | null | undefined;
  size?: "sm" | "lg";
}) {
  if (delta == null || delta === 0) return null;
  const positive = delta > 0;
  const color = positive ? "#4ADE80" : "#F87171";
  const arrow = positive ? "▲" : "▼";
  const sign = positive ? "+" : "";
  const fontSize = size === "lg" ? "0.8rem" : "0.7rem";
  return (
    <span className="font-mono whitespace-nowrap" style={{ color, fontSize }}>
      {arrow}{sign}{delta.toFixed(1)}
    </span>
  );
}

// ------------------------------------------------------------------ //
// Theme color heuristic                                                //
// ------------------------------------------------------------------ //

const THEME_COLORS: [RegExp, string][] = [
  [/secur|crime|terror|conflict|violen|weapon|military|war|rebel/i, "#EF4444"],
  [/econom|trade|financ|currenc|market|bank|gdp|inflat|debt|poverty/i, "#22C55E"],
  [/govern|polic|law|elect|regulat|corrupt|censor|legislat|reform/i, "#3B82F6"],
  [/environ|climat|pollut|green|water|deforest|ocean/i, "#14B8A6"],
  [/health|pandemic|disease|vaccin|ebola|sars|epidemic|mental/i, "#EAB308"],
  [/tech|ai|cyber|block|biotech|space|ict/i, "#A855F7"],
];

function themeColor(theme: string): string {
  for (const [re, color] of THEME_COLORS) {
    if (re.test(theme)) return color;
  }
  return "#6B7280";
}

// ------------------------------------------------------------------ //
// Sparkline tooltip                                                    //
// ------------------------------------------------------------------ //

function SparkTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-panel px-2 py-1 text-[10px] font-mono">
      <div className="text-hud-accent">{label}</div>
      <div className="text-slate-200">
        Stability:{" "}
        <span className="text-hud-accent">{payload[0].value.toFixed(1)}</span>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ //
// Skeleton bars                                                        //
// ------------------------------------------------------------------ //

function SkeletonBars() {
  return (
    <div className="space-y-2 animate-pulse">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="w-24 h-2 bg-white/5 rounded" />
          <div className="flex-1 h-1 bg-white/5 rounded-full" />
          <div className="w-7 h-2 bg-white/5 rounded" />
        </div>
      ))}
    </div>
  );
}

// ------------------------------------------------------------------ //
// Expandable dimension bar row  (V2.2: delta, causal driver)           //
// ------------------------------------------------------------------ //

function DimensionBar({
  d,
  expanded,
  onToggle,
}: {
  d: DimensionScore;
  expanded: boolean;
  onToggle: () => void;
}) {
  const color = scoreToHex(d.score);
  const label = d.dimension.replace(/_/g, " ");

  return (
    <div className="rounded overflow-hidden">
      <button
        onClick={onToggle}
        className="flex items-center gap-2 w-full text-left group py-0.5"
      >
        <span className="text-[10px] text-slate-500 w-24 capitalize shrink-0 group-hover:text-slate-300 transition-colors">
          {label}
        </span>
        <div className="flex-1 bg-white/5 rounded-full h-1">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${d.score}%`, background: color }}
          />
        </div>
        <span
          className="text-[10px] font-mono w-7 text-right shrink-0"
          style={{ color }}
        >
          {d.score}
        </span>
        <DeltaArrow delta={d.score_delta} />
        <svg
          className={cn(
            "w-2.5 h-2.5 text-slate-600 shrink-0 transition-transform",
            expanded && "rotate-180",
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="detail"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="pl-2 pr-1 pb-2 pt-1 space-y-2 border-l-2 border-hud-accent/20 ml-1 mt-1">
              <div>
                <span className="inline-block text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-slate-500 border border-white/10">
                  {Math.round(d.confidence * 100)}% confident
                </span>
              </div>

              {/* V2.2: Causal driver callout */}
              {d.causal_driver && (
                <div
                  className="pl-2 py-1.5 rounded-r"
                  style={{
                    background: "rgba(251, 191, 36, 0.1)",
                    borderLeft: "2px solid #F59E0B",
                  }}
                >
                  <p className="text-[0.75rem] text-amber-200/80 italic leading-snug">
                    {d.causal_driver}
                  </p>
                </div>
              )}

              {d.reasoning && (
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  {d.reasoning}
                </p>
              )}

              {d.evidence_snippets.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[9px] text-slate-600 uppercase tracking-widest">
                    Evidence
                  </p>
                  <ul className="space-y-1.5">
                    {d.evidence_snippets.map((raw, i) => {
                      const { text, urls } = parseTextWithCitation(raw);
                      return (
                        <li key={i} className="flex flex-col gap-0.5">
                          <div className="flex gap-1.5">
                            <span className="text-hud-accent/50 shrink-0 text-[9px]">▸</span>
                            <span className="text-[10px] text-slate-500 leading-snug">
                              {text}
                            </span>
                          </div>
                          <SourceLinks urls={urls} />
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}

              {d.citations && d.citations.length > 0 && (
                <SourceLinks urls={d.citations} />
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ------------------------------------------------------------------ //
// Analyst Summary                                                      //
// ------------------------------------------------------------------ //

function AnalystSummary({ summary }: { summary: string }) {
  if (!summary) return null;
  return (
    <div className="px-4 pb-3">
      <p className="text-[9px] text-slate-600 uppercase tracking-widest mb-2">
        AI Analyst Assessment
      </p>
      <div className="border-l-2 border-hud-accent/40 pl-3">
        <p className="text-[11px] text-slate-300 italic leading-relaxed">
          {summary}
        </p>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ //
// Entity Tags  [V2.2]                                                  //
// ------------------------------------------------------------------ //

function EntityTags({ entities }: { entities: string[] }) {
  if (!entities || entities.length === 0) return null;
  return (
    <div className="px-4 pb-3">
      <p className="text-[9px] uppercase tracking-widest mb-2" style={{ color: "rgba(255,255,255,0.4)" }}>
        Key Entities
      </p>
      <div className="flex flex-wrap gap-1.5">
        {entities.slice(0, 10).map((entity, i) => (
          <span
            key={i}
            className="rounded-full px-2 py-0.5"
            style={{
              fontSize: "0.7rem",
              border: "1px solid rgba(255,255,255,0.2)",
              color: i < 5 ? "#60A5FA" : "#34D399",
            }}
          >
            {entity}
          </span>
        ))}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ //
// Theme Distribution Bar  [V2.2]                                       //
// ------------------------------------------------------------------ //

const THEME_WEIGHTS = [0.3, 0.25, 0.2, 0.15, 0.1];

function ThemeBar({ themes }: { themes: string[] }) {
  if (!themes || themes.length === 0) return null;
  const top5 = themes.slice(0, 5);
  return (
    <div className="px-4 pb-3">
      <p className="text-[9px] uppercase tracking-widest mb-2" style={{ color: "rgba(255,255,255,0.4)" }}>
        Dominant Themes
      </p>
      <div className="flex w-full h-2 rounded-full overflow-hidden">
        {top5.map((theme, i) => (
          <div
            key={i}
            title={theme}
            className="h-full transition-all"
            style={{
              width: `${(THEME_WEIGHTS[i] ?? 0.1) * 100}%`,
              background: themeColor(theme),
            }}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
        {top5.map((theme, i) => (
          <span key={i} className="inline-flex items-center gap-1 text-[0.65rem] text-slate-400">
            <span
              className="inline-block w-1.5 h-1.5 rounded-full shrink-0"
              style={{ background: themeColor(theme) }}
            />
            {theme}
          </span>
        ))}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ //
// Key Events / Intelligence Feed                                       //
// ------------------------------------------------------------------ //

function ImpactDot({ impact }: { impact: KeyEvent["impact"] }) {
  const color =
    impact === "positive"
      ? "#48bb78"
      : impact === "negative"
      ? "#fc8181"
      : "#4a5568";
  return (
    <span
      className="inline-block w-1.5 rounded-full self-stretch shrink-0"
      style={{ background: color }}
    />
  );
}

function KeyEventCard({ ev }: { ev: KeyEvent }) {
  const goldColor =
    ev.goldstein_scale > 0 ? "#48bb78" : ev.goldstein_scale < 0 ? "#fc8181" : "#94a3b8";
  const goldSign = ev.goldstein_scale > 0 ? "+" : "";

  return (
    <div className="flex gap-2">
      <ImpactDot impact={ev.impact} />
      <div className="flex-1 min-w-0 space-y-0.5">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[9px] font-mono text-slate-500 shrink-0">
            {ev.date}
          </span>
          <span className="text-[9px] font-mono shrink-0" style={{ color: goldColor }}>
            {goldSign}{ev.goldstein_scale.toFixed(1)}
          </span>
        </div>
        <p className="text-[10px] text-slate-300 leading-snug">{ev.description}</p>
        {ev.actors.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-0.5">
            {ev.actors.map((a, i) => (
              <span
                key={i}
                className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-slate-500"
              >
                {a}
              </span>
            ))}
          </div>
        )}
        {ev.source_url && <SourceLinks urls={[ev.source_url]} />}
      </div>
    </div>
  );
}

function KeyEventsSection({ events }: { events: KeyEvent[] }) {
  if (!events || events.length === 0) return null;
  const shown = events.slice(0, 5);
  return (
    <div className="px-4 pb-3">
      <p className="text-[9px] text-slate-600 uppercase tracking-widest mb-2">
        Key Events
      </p>
      <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
        {shown.map((ev, i) => (
          <KeyEventCard key={i} ev={ev} />
        ))}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ //
// Risk / Strength list — V2.2: source tier badges on citations         //
// ------------------------------------------------------------------ //

function TieredSourceLinks({
  urls,
  tiers,
  accent,
}: {
  urls: string[];
  tiers?: number[];
  accent: "red" | "green";
}) {
  if (urls.length === 0) return null;
  const linkColor = accent === "red" ? "text-red-400/70" : "text-hud-accent";
  return (
    <div className="flex flex-wrap gap-2 pl-4">
      {urls.map((url, i) => {
        const tier = tiers?.[i] ?? 4;
        const domain = extractDomain(url);
        return (
          <a
            key={i}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className={cn("inline-flex items-center gap-0.5 text-[9px] hover:underline", linkColor)}
          >
            <SourceBadge tier={tier} showName={false} />
            <span>{domain}</span>
          </a>
        );
      })}
    </div>
  );
}

function RiskStrengthCard({
  item,
  accent,
}: {
  item: RiskOrStrength | string;
  accent: "red" | "green";
}) {
  const dotColor = accent === "red" ? "text-red-500/60" : "text-green-500/60";

  if (typeof item === "string") {
    const { text, urls } = parseTextWithCitation(item);
    return (
      <li className="flex flex-col gap-0.5">
        <div className="flex gap-1.5">
          <span className={cn("shrink-0", dotColor)}>▸</span>
          <span className="text-[10px] text-slate-400 leading-snug">{text}</span>
        </div>
        <SourceLinks urls={urls} />
      </li>
    );
  }

  return (
    <li className="flex flex-col gap-1">
      <div className="flex gap-1.5">
        <span className={cn("shrink-0 mt-0.5", dotColor)}>▸</span>
        <span className="text-[11px] text-slate-300 leading-snug">{item.summary}</span>
      </div>
      <div className="pl-4 flex flex-col gap-0.5">
        <span className="text-[9px] text-slate-500 font-mono">
          Based on {item.supporting_event_count} event{item.supporting_event_count !== 1 ? "s" : ""} · {item.date_range}
        </span>
        <TieredSourceLinks
          urls={item.citations}
          tiers={item.source_tiers}
          accent={accent}
        />
      </div>
    </li>
  );
}

function RiskStrengthList({
  items,
  accent,
}: {
  items: (RiskOrStrength | string)[];
  accent: "red" | "green";
}) {
  if (!items || items.length === 0) return null;
  const headColor =
    accent === "red" ? "text-red-500/70" : "text-green-500/70";
  const label = accent === "red" ? "Top Risks" : "Top Strengths";

  return (
    <>
      <HudDivider />
      <p className={cn("text-[9px] uppercase tracking-widest mb-1.5", headColor)}>
        {label}
      </p>
      <ul className="space-y-3">
        {items.slice(0, 5).map((item, i) => (
          <RiskStrengthCard key={i} item={item} accent={accent} />
        ))}
      </ul>
    </>
  );
}

// ------------------------------------------------------------------ //
// Intelligence Metadata Bar  [V2.2]                                    //
// ------------------------------------------------------------------ //

function IntelMetadataBar({
  totalArticles,
  uniqueSources,
  biasNote,
  sources,
}: {
  totalArticles: number;
  uniqueSources: number;
  biasNote?: string | null;
  sources?: { tier: number }[];
}) {
  if (!totalArticles) return null;
  return (
    <div className="px-4 pb-2">
      <div className="flex items-center justify-between gap-2" style={{ fontSize: "0.7rem", color: "rgba(255,255,255,0.5)" }}>
        <span>
          Based on {totalArticles} article{totalArticles !== 1 ? "s" : ""} from{" "}
          {uniqueSources} outlet{uniqueSources !== 1 ? "s" : ""}
        </span>
        {sources && sources.length > 0 && <TierCounts sources={sources} />}
      </div>
      {biasNote && (
        <p className="mt-1 text-[0.65rem] text-amber-400/80 leading-snug">
          ⚠️ {biasNote}
        </p>
      )}
    </div>
  );
}

// ------------------------------------------------------------------ //
// Media Landscape (collapsible)  [V2.2]                                //
// ------------------------------------------------------------------ //

function ToneIndicator({ tone }: { tone: number }) {
  const color = tone < -1 ? "#F87171" : tone > 1 ? "#4ADE80" : "#6B7280";
  return (
    <span
      className="inline-block w-2 h-2 rounded-full shrink-0"
      style={{ background: color }}
      title={`Avg tone: ${tone.toFixed(2)}`}
    />
  );
}

function MediaLandscape({
  cityId,
  selectedDate,
}: {
  cityId: string;
  selectedDate: string;
}) {
  const [open, setOpen] = useState(false);

  const startDate = useMemo(() => {
    const d = new Date(selectedDate);
    d.setUTCDate(d.getUTCDate() - 90);
    return toIsoDate(d);
  }, [selectedDate]);

  const { data: sourcesData } = useSources(cityId, startDate, selectedDate);

  if (!sourcesData || sourcesData.total_articles === 0) return null;

  const top5 = sourcesData.sources.slice(0, 5);
  const maxArticles = top5.length > 0 ? top5[0].article_count : 1;

  return (
    <div className="px-4 pb-3">
      <button
        onClick={() => setOpen((p) => !p)}
        className="w-full flex items-center justify-between text-left group"
      >
        <p className="text-[9px] uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.4)" }}>
          Media Landscape
        </p>
        <span className="text-[0.65rem] text-slate-500">
          {sourcesData.total_articles} articles · {sourcesData.sources.length} outlets
          <svg
            className={cn(
              "inline-block w-2.5 h-2.5 ml-1 text-slate-600 transition-transform",
              open && "rotate-180",
            )}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2.5}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="media"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-2">
              {top5.map((src, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-28 shrink-0 truncate">
                    <SourceBadge sourceName={src.name} tier={src.tier} />
                  </div>
                  <div className="flex-1 bg-white/5 rounded-full h-1.5">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${(src.article_count / maxArticles) * 100}%`,
                        background: "rgba(0, 212, 255, 0.5)",
                      }}
                    />
                  </div>
                  <span className="text-[0.65rem] text-slate-500 font-mono w-16 text-right shrink-0">
                    {src.article_count} art.
                  </span>
                  <ToneIndicator tone={src.avg_tone} />
                </div>
              ))}
              <p className="text-[0.65rem] text-slate-600 pt-1">
                Higher tier sources (★) indicate more reliable intelligence
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ------------------------------------------------------------------ //
// Main panel                                                           //
// ------------------------------------------------------------------ //

export function CityDetailsPanel() {
  const { selectedCityId, selectedCityName, selectedDate, setSelectedCity, addToCompare, showToast } =
    useAppStore();
  const queryClient = useQueryClient();

  const { data: history, isLoading: histLoading } = useCityHistory(
    selectedCityId,
    selectedDate,
  );
  const { data: fullScore, isLoading: scoreLoading, isError: scoreError } = useCityScore(
    selectedCityId,
    selectedDate,
  );

  const sourcesStart = useMemo(() => {
    const d = new Date(selectedDate);
    d.setUTCDate(d.getUTCDate() - 90);
    return toIsoDate(d);
  }, [selectedDate]);

  const { data: sourcesData } = useSources(
    selectedCityId,
    sourcesStart,
    selectedDate,
  );

  const [expandedDim, setExpandedDim] = useState<string | null>(null);

  if (!selectedCityId) return null;

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href).then(
      () => showToast("Link copied!"),
      () => showToast("Failed to copy link"),
    );
  };

  const handleCompare = () => {
    addToCompare(selectedCityId);
  };

  const handleRetryScore = () => {
    queryClient.invalidateQueries({ queryKey: ["city-score", selectedCityId, selectedDate] });
  };

  const latestRow = history?.[history.length - 1];
  const stabilityScore =
    latestRow?.stability_score ?? fullScore?.overall_score ?? null;
  const avgGoldstein =
    latestRow?.avg_goldstein ?? fullScore?.gdelt_avg_goldstein ?? null;
  const eventCount = history
    ? history.reduce((s, r) => s + r.event_count, 0)
    : fullScore?.gdelt_event_count ?? 0;

  const chartData = (history ?? []).map((r) => ({
    day: r.day.slice(5),
    stability_score: Math.round(r.stability_score * 10) / 10,
  }));

  function toggleDim(dim: string) {
    setExpandedDim((prev) => (prev === dim ? null : dim));
  }

  return (
    <motion.div
      key={selectedCityId}
      initial={{ x: 40, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 40, opacity: 0 }}
      transition={{ type: "spring", stiffness: 320, damping: 30 }}
      className="pointer-events-auto w-80 lg:w-80 md:w-[350px] h-full flex flex-col"
    >
      <GlassPanel accent className="flex flex-col h-full overflow-hidden">
        {/* ---- 1. Header ---- */}
        <div className="px-4 pt-4 pb-3 flex items-start justify-between shrink-0">
          <div>
            <h2 className="text-base font-semibold text-slate-100 leading-tight">
              {selectedCityName ?? "City"}
            </h2>
            <p className="text-[10px] text-slate-500 font-mono mt-0.5">
              {formatDate(selectedDate)}
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleCompare}
              className="text-slate-600 hover:text-hud-accent transition-colors text-xs leading-none"
              aria-label="Compare city"
              title="Add to comparison"
            >
              ⚖
            </button>
            <button
              onClick={handleCopyLink}
              className="text-slate-600 hover:text-hud-accent transition-colors text-xs leading-none"
              aria-label="Copy link"
              title="Copy link to clipboard"
            >
              📋
            </button>
            <button
              onClick={() => setSelectedCity(null)}
              className="text-slate-600 hover:text-slate-300 transition-colors text-lg leading-none"
              aria-label="Close panel"
            >
              ×
            </button>
          </div>
        </div>

        {/* ---- 2. Score badges + overall delta ---- */}
        <div className="px-4 pb-3 flex items-end gap-6 shrink-0">
          <div className="flex items-end gap-2">
            <StatBadge
              label="Stability"
              value={stabilityScore != null ? stabilityScore.toFixed(1) : "—"}
              colorClass={scoreToTextClass(stabilityScore)}
            />
            <DeltaArrow delta={fullScore?.score_delta} size="lg" />
          </div>
          <StatBadge
            label="Goldstein"
            value={
              avgGoldstein != null
                ? `${avgGoldstein > 0 ? "+" : ""}${avgGoldstein.toFixed(2)}`
                : "—"
            }
            colorClass={
              avgGoldstein == null
                ? "text-slate-400"
                : avgGoldstein >= 0
                ? "text-green-400"
                : "text-red-400"
            }
          />
          <StatBadge
            label="Events (90d)"
            value={eventCount > 0 ? eventCount.toLocaleString() : "—"}
            colorClass="text-slate-300"
          />
        </div>

        <HudDivider />

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 min-h-0">
          {/* ---- 3. Intelligence metadata bar ---- */}
          {fullScore && (
            <IntelMetadataBar
              totalArticles={fullScore.total_articles_analyzed ?? 0}
              uniqueSources={fullScore.unique_sources_analyzed ?? 0}
              biasNote={fullScore.source_bias_note}
              sources={sourcesData?.sources}
            />
          )}

          {/* ---- 4. Analyst Summary ---- */}
          {fullScore?.analyst_summary && (
            <>
              <AnalystSummary summary={fullScore.analyst_summary} />
              <HudDivider />
            </>
          )}

          {/* ---- 5. Entity Tags ---- */}
          {fullScore?.top_entities && fullScore.top_entities.length > 0 && (
            <EntityTags entities={fullScore.top_entities} />
          )}

          {/* ---- 6. Theme Distribution ---- */}
          {fullScore?.dominant_themes && fullScore.dominant_themes.length > 0 && (
            <>
              <ThemeBar themes={fullScore.dominant_themes} />
              <HudDivider />
            </>
          )}

          {/* ---- 7. Stability sparkline ---- */}
          <div className="px-3 pb-1">
            <p className="text-[9px] text-slate-600 uppercase tracking-widest mb-1 px-1">
              Stability trend (90 days)
            </p>
            {histLoading ? (
              <div className="h-16 flex items-center justify-center">
                <span className="text-[10px] text-slate-600 animate-pulse">
                  Loading GDELT data…
                </span>
              </div>
            ) : chartData.length === 0 ? (
              <div className="h-16 flex items-center justify-center">
                <span className="text-[10px] text-slate-600">
                  No GDELT data for this city/date
                </span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={72}>
                <AreaChart
                  data={chartData}
                  margin={{ top: 4, right: 4, left: -32, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="stabGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="day"
                    tick={{ fontSize: 8, fill: "#4a5568" }}
                    tickLine={false}
                    axisLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 8, fill: "#4a5568" }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip content={<SparkTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="stability_score"
                    stroke="#00d4ff"
                    strokeWidth={1.5}
                    fill="url(#stabGrad)"
                    dot={false}
                    activeDot={{ r: 3, fill: "#00d4ff" }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* ---- 8. Civic Dimensions ---- */}
          <HudDivider />
          <div className="px-4 pb-4">
            <p className="text-[9px] text-slate-600 uppercase tracking-widest mb-2">
              Civic dimensions{" "}
              <span className="text-slate-700 normal-case">
                — tap to expand
              </span>
            </p>

            {scoreError ? (
              <div className="py-3 px-3 rounded-md border border-amber-400/20 bg-amber-400/5">
                <p className="text-[11px] text-amber-200/90 leading-relaxed">
                  No AI evaluation has been pre-computed for this city in the
                  public demo build.
                </p>
                <p className="text-[10px] text-slate-500 mt-1.5 leading-relaxed">
                  Detailed analyses are available for Hong Kong, Shanghai,
                  Shenzhen, Singapore, Tokyo, London, and New York. Click the{" "}
                  <span className="text-amber-300/80">Demo build · why</span>{" "}
                  badge in the top bar for context.
                </p>
                <button
                  onClick={handleRetryScore}
                  className="mt-2 text-[10px] text-slate-500 hover:text-hud-accent transition-colors font-mono uppercase tracking-wider"
                >
                  Retry
                </button>
              </div>
            ) : scoreLoading ? (
              <SkeletonBars />
            ) : fullScore ? (
              <div className="space-y-0.5">
                {fullScore.dimensions.map((d) => (
                  <DimensionBar
                    key={d.dimension}
                    d={d}
                    expanded={expandedDim === d.dimension}
                    onToggle={() => toggleDim(d.dimension)}
                  />
                ))}
              </div>
            ) : (
              <p className="text-[10px] text-slate-600 italic">
                LLM score not available — add OPENAI_API_KEY to .env to enable.
              </p>
            )}

            {/* ---- 9 & 10. Risks + Strengths ---- */}
            {fullScore && (
              <>
                <RiskStrengthList items={fullScore.top_risks} accent="red" />
                <RiskStrengthList items={fullScore.top_strengths} accent="green" />
              </>
            )}
          </div>

          {/* ---- 11. Key Events ---- */}
          {fullScore?.key_events && fullScore.key_events.length > 0 && (
            <>
              <HudDivider />
              <KeyEventsSection events={fullScore.key_events} />
            </>
          )}

          {/* ---- 12. Media Landscape ---- */}
          {selectedCityId && (
            <>
              <HudDivider />
              <MediaLandscape cityId={selectedCityId} selectedDate={selectedDate} />
            </>
          )}

          <div className="h-4 shrink-0" />
        </div>
      </GlassPanel>
    </motion.div>
  );
}
