import { useState } from "react";

export type SortKey =
  | "name-asc"
  | "name-desc"
  | "pop-desc"
  | "pop-asc"
  | "score-desc"
  | "score-asc";

export type PopFilter = "all" | "10m" | "5m" | "1m";

interface FilterControlsProps {
  sortKey: SortKey;
  onSortChange: (key: SortKey) => void;
  popFilter: PopFilter;
  onPopFilterChange: (f: PopFilter) => void;
  dataOnly: boolean;
  onDataOnlyChange: (v: boolean) => void;
}

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: "name-asc", label: "Name A→Z" },
  { value: "name-desc", label: "Name Z→A" },
  { value: "pop-desc", label: "Population ↓" },
  { value: "pop-asc", label: "Population ↑" },
  { value: "score-desc", label: "Score ↓" },
  { value: "score-asc", label: "Score ↑" },
];

const POP_BUTTONS: { value: PopFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "10m", label: ">10M" },
  { value: "5m", label: ">5M" },
  { value: "1m", label: ">1M" },
];

export function FilterControls({
  sortKey,
  onSortChange,
  popFilter,
  onPopFilterChange,
  dataOnly,
  onDataOnlyChange,
}: FilterControlsProps) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-[10px] text-slate-500 hover:text-slate-300 transition-colors uppercase tracking-widest font-mono w-full"
      >
        <svg
          className={`w-2.5 h-2.5 transition-transform ${open ? "rotate-90" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={3}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        Filters & Sort
      </button>

      {open && (
        <div className="mt-2 space-y-3">
          {/* Sort dropdown */}
          <div>
            <label className="text-[9px] text-slate-600 uppercase tracking-widest block mb-1">
              Sort by
            </label>
            <select
              value={sortKey}
              onChange={(e) => onSortChange(e.target.value as SortKey)}
              className="w-full bg-white/5 border border-white/10 rounded-md px-2 py-1.5
                         text-xs text-slate-200 font-mono outline-none
                         focus:border-hud-accent/50 transition-colors appearance-none cursor-pointer"
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value} className="bg-slate-900">
                  {o.label}
                </option>
              ))}
            </select>
          </div>

          {/* Population filter */}
          <div>
            <label className="text-[9px] text-slate-600 uppercase tracking-widest block mb-1">
              Population
            </label>
            <div className="flex gap-1">
              {POP_BUTTONS.map((b) => (
                <button
                  key={b.value}
                  onClick={() => onPopFilterChange(b.value)}
                  className={`flex-1 text-[10px] font-mono py-1 rounded border transition-colors ${
                    popFilter === b.value
                      ? "border-hud-accent/60 text-hud-accent bg-hud-accent/10"
                      : "border-white/10 text-slate-500 hover:text-slate-300"
                  }`}
                >
                  {b.label}
                </button>
              ))}
            </div>
          </div>

          {/* Data-only toggle */}
          <label className="flex items-center gap-2 cursor-pointer group">
            <div
              className={`w-7 h-4 rounded-full relative transition-colors ${
                dataOnly ? "bg-hud-accent/40" : "bg-white/10"
              }`}
              onClick={() => onDataOnlyChange(!dataOnly)}
            >
              <div
                className={`absolute top-0.5 w-3 h-3 rounded-full transition-all ${
                  dataOnly
                    ? "left-3.5 bg-hud-accent"
                    : "left-0.5 bg-slate-500"
                }`}
              />
            </div>
            <span className="text-[10px] text-slate-500 group-hover:text-slate-300 transition-colors font-mono">
              With GDELT data only
            </span>
          </label>
        </div>
      )}
    </div>
  );
}
