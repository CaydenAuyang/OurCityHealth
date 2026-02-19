import { useState, useCallback, useRef, useEffect, createRef } from "react";

/** Module-level ref for keyboard shortcut "/" to focus this input. */
export const searchInputRef = createRef<HTMLInputElement>();

interface CitySearchProps {
  value: string;
  onChange: (query: string) => void;
}

export function CitySearch({ value, onChange }: CitySearchProps) {
  const [local, setLocal] = useState(value);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();
  const internalRef = useRef<HTMLInputElement>(null);

  // Keep module-level ref in sync
  useEffect(() => {
    (searchInputRef as React.MutableRefObject<HTMLInputElement | null>).current =
      internalRef.current;
  });

  useEffect(() => {
    setLocal(value);
  }, [value]);

  const handleInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const v = e.target.value;
      setLocal(v);
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => onChange(v), 150);
    },
    [onChange],
  );

  const clear = useCallback(() => {
    setLocal("");
    clearTimeout(timerRef.current);
    onChange("");
  }, [onChange]);

  return (
    <div className="relative">
      {/* Search icon */}
      <svg
        className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 pointer-events-none"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
        />
      </svg>

      <input
        ref={internalRef}
        type="text"
        value={local}
        onChange={handleInput}
        placeholder="Search 1,000 cities…"
        className="w-full bg-white/5 border border-white/10 focus:border-hud-accent/50 rounded-lg
                   pl-9 pr-8 py-2 text-xs text-slate-200 font-mono
                   placeholder:text-slate-600 outline-none transition-colors"
      />

      {local && (
        <button
          onClick={clear}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors text-sm leading-none"
          aria-label="Clear search"
        >
          ×
        </button>
      )}
    </div>
  );
}
