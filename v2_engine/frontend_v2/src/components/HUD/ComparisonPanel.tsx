/**
 * ComparisonPanel — side-by-side city comparison with RadarChart overlay.
 * Renders when isCompareMode is true and at least 1 city is in the comparison.
 */

import { motion } from "framer-motion";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { GlassPanel, HudDivider } from "./GlassPanel";
import { useAppStore } from "../../store/useAppStore";
import { useCities, useCityScore } from "../../api/hooks";
import { scoreToHex, cn } from "../../lib/utils";

const RADAR_COLORS = ["#00d4ff", "#f97316", "#a855f7"];

interface CityCardProps {
  cityId: string;
  colorIdx: number;
}

function CityCard({ cityId, colorIdx }: CityCardProps) {
  const date = useAppStore((s) => s.selectedDate);
  const removeFromCompare = useAppStore((s) => s.removeFromCompare);
  const { data: cities = [] } = useCities();
  const { data: score, isLoading } = useCityScore(cityId, date);

  const city = cities.find((c) => c.id === cityId);
  const name = city?.name ?? "…";
  const overall = score?.overall_score ?? null;
  const color = RADAR_COLORS[colorIdx % RADAR_COLORS.length];

  return (
    <div
      className="flex-1 min-w-0 rounded-lg p-3"
      style={{ border: `1px solid ${color}33` }}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="min-w-0">
          <p
            className="text-[11px] font-semibold text-slate-200 truncate"
            style={{ color }}
          >
            {name}
          </p>
          <p className="text-[9px] text-slate-600 font-mono">
            {city?.country_code ?? ""}
          </p>
        </div>
        <button
          onClick={() => removeFromCompare(cityId)}
          className="text-slate-600 hover:text-slate-300 transition-colors text-sm leading-none shrink-0"
          aria-label="Remove from comparison"
        >
          ×
        </button>
      </div>

      {isLoading ? (
        <div className="text-[10px] text-slate-600 animate-pulse">Loading…</div>
      ) : overall != null ? (
        <span
          className="text-2xl font-bold font-mono"
          style={{ color: scoreToHex(overall) }}
        >
          {overall.toFixed(0)}
        </span>
      ) : (
        <span className="text-lg text-slate-600 font-mono">—</span>
      )}
    </div>
  );
}

function CompareRadar({ cityIds }: { cityIds: string[] }) {
  const date = useAppStore((s) => s.selectedDate);
  const { data: cities = [] } = useCities();

  const scoreResults = cityIds.map((id) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const { data } = useCityScore(id, date);
    return data;
  });

  // Build radar data from dimensions
  const dimSet = new Set<string>();
  scoreResults.forEach((s) =>
    s?.dimensions.forEach((d) => dimSet.add(d.dimension)),
  );
  const dims = Array.from(dimSet);
  if (dims.length === 0) return null;

  const radarData = dims.map((dim) => {
    const entry: Record<string, string | number> = {
      dimension: dim.replace(/_/g, " "),
    };
    cityIds.forEach((id, idx) => {
      const score = scoreResults[idx];
      const dScore = score?.dimensions.find((d) => d.dimension === dim);
      entry[id] = dScore?.score ?? 0;
    });
    return entry;
  });

  return (
    <ResponsiveContainer width="100%" height={220}>
      <RadarChart data={radarData}>
        <PolarGrid stroke="rgba(255,255,255,0.08)" />
        <PolarAngleAxis
          dataKey="dimension"
          tick={{ fill: "#64748b", fontSize: 8 }}
        />
        <PolarRadiusAxis
          domain={[0, 100]}
          tick={{ fill: "#475569", fontSize: 7 }}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{
            background: "rgba(5,10,25,0.9)",
            border: "1px solid rgba(0,200,255,0.2)",
            borderRadius: 8,
            fontSize: 10,
          }}
        />
        {cityIds.map((id, idx) => {
          const city = cities.find((c) => c.id === id);
          return (
            <Radar
              key={id}
              name={city?.name ?? id.slice(0, 8)}
              dataKey={id}
              stroke={RADAR_COLORS[idx % RADAR_COLORS.length]}
              fill={RADAR_COLORS[idx % RADAR_COLORS.length]}
              fillOpacity={0.1}
              strokeWidth={1.5}
            />
          );
        })}
      </RadarChart>
    </ResponsiveContainer>
  );
}

export function ComparisonPanel() {
  const { comparedCityIds, clearCompare } = useAppStore();

  if (comparedCityIds.length === 0) return null;

  return (
    <motion.div
      initial={{ x: 40, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 40, opacity: 0 }}
      transition={{ type: "spring", stiffness: 320, damping: 30 }}
      className="pointer-events-auto w-96 h-full flex flex-col"
    >
      <GlassPanel accent className="flex flex-col h-full overflow-hidden">
        {/* Header */}
        <div className="px-4 pt-4 pb-3 flex items-center justify-between shrink-0">
          <p className="text-[9px] text-slate-600 uppercase tracking-widest">
            City Comparison
          </p>
          <button
            onClick={clearCompare}
            className="text-[10px] text-slate-600 hover:text-slate-300 transition-colors"
          >
            Close comparison ×
          </button>
        </div>

        <HudDivider />

        <div className="overflow-y-auto flex-1 min-h-0 px-4 pb-4">
          {/* City cards */}
          <div className="flex gap-2 mb-4">
            {comparedCityIds.map((id, idx) => (
              <CityCard key={id} cityId={id} colorIdx={idx} />
            ))}
          </div>

          {/* Radar chart */}
          {comparedCityIds.length >= 2 && (
            <>
              <HudDivider />
              <p className="text-[9px] text-slate-600 uppercase tracking-widest mb-2 mt-3">
                Dimension Comparison
              </p>
              <CompareRadar cityIds={comparedCityIds} />
            </>
          )}
        </div>
      </GlassPanel>
    </motion.div>
  );
}
