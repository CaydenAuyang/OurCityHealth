import { memo, useCallback } from "react";
import { FixedSizeList, type ListChildComponentProps } from "react-window";
import { countryFlag, formatPopulation, scoreToHex } from "../../lib/utils";
import type { City } from "../../api/types";

interface CityListProps {
  cities: City[];
  scoresMap: Record<string, number>;
  selectedCityId: string | null;
  onSelect: (id: string, name: string) => void;
  height: number;
}

interface RowData {
  cities: City[];
  scoresMap: Record<string, number>;
  selectedCityId: string | null;
  onSelect: (id: string, name: string) => void;
}

const ROW_HEIGHT = 52;

const Row = memo(function Row({ index, style, data }: ListChildComponentProps<RowData>) {
  const { cities, scoresMap, selectedCityId, onSelect } = data;
  const city = cities[index];
  if (!city) return null;

  const isSelected = city.id === selectedCityId;
  const score = scoresMap[city.id] ?? null;
  const flag = countryFlag(city.country_code);

  return (
    <div
      style={style}
      className={`flex items-center gap-2.5 px-3 cursor-pointer transition-colors group ${
        isSelected
          ? "bg-hud-accent/10 border-l-2 border-hud-accent"
          : "border-l-2 border-transparent hover:bg-white/5"
      }`}
      onClick={() => onSelect(city.id, city.name)}
    >
      {/* Flag */}
      <span className="text-base shrink-0 w-6 text-center leading-none">
        {flag}
      </span>

      {/* City info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-1.5">
          <span
            className={`text-xs truncate ${
              isSelected ? "text-hud-accent font-semibold" : "text-slate-200 font-medium"
            }`}
          >
            {city.name}
          </span>
          <span className="text-[9px] text-slate-600 font-mono shrink-0">
            {city.country_code}
          </span>
        </div>
        <span className="text-[10px] text-slate-600 font-mono">
          {formatPopulation(city.population)}
        </span>
      </div>

      {/* Score indicator */}
      <div className="flex items-center gap-1.5 shrink-0">
        {score != null && (
          <span
            className="text-[10px] font-mono"
            style={{ color: scoreToHex(score) }}
          >
            {score.toFixed(1)}
          </span>
        )}
        <span
          className="inline-block w-2 h-2 rounded-full shrink-0"
          style={{ background: scoreToHex(score) }}
        />
      </div>
    </div>
  );
});

export function CityList({
  cities,
  scoresMap,
  selectedCityId,
  onSelect,
  height,
}: CityListProps) {
  const itemData: RowData = { cities, scoresMap, selectedCityId, onSelect };

  const itemKey = useCallback(
    (index: number, data: RowData) => data.cities[index]?.id ?? index,
    [],
  );

  if (cities.length === 0) {
    return (
      <div className="flex items-center justify-center h-24">
        <span className="text-xs text-slate-600 font-mono">No cities match</span>
      </div>
    );
  }

  return (
    <FixedSizeList
      height={height}
      width="100%"
      itemCount={cities.length}
      itemSize={ROW_HEIGHT}
      itemData={itemData}
      itemKey={itemKey}
      overscanCount={10}
      className="scrollbar-thin"
    >
      {Row}
    </FixedSizeList>
  );
}
