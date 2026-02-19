/**
 * GlassPanel — the reusable glassmorphism container used everywhere in the HUD.
 *
 * Styling contract:
 *   background  : rgba(5, 10, 25, 0.82) + backdrop-filter:blur(20px)
 *   border      : 1px rgba(0,200,255,0.18) — subtle cyan outline
 *   top accent  : optional 1-pixel linear-gradient glow across the top edge
 *   box-shadow  : layered outer dark + faint blue glow
 */

import type { ReactNode, CSSProperties } from "react";
import { cn } from "../../lib/utils";

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
  accent?: boolean; // show the top cyan accent line
  style?: CSSProperties;
  onClick?: () => void;
}

export function GlassPanel({
  children,
  className,
  accent = false,
  style,
  onClick,
}: GlassPanelProps) {
  return (
    <div
      className={cn("glass-panel", accent && "glass-panel-accent", className)}
      style={style}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

// ------------------------------------------------------------------ //
// Stat widget — small number + label chip used inside panels          //
// ------------------------------------------------------------------ //

interface StatBadgeProps {
  label: string;
  value: string | number;
  colorClass?: string;
}

export function StatBadge({
  label,
  value,
  colorClass = "text-hud-accent",
}: StatBadgeProps) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className={cn("text-xl font-mono font-medium", colorClass)}>
        {value}
      </span>
      <span className="text-[10px] text-slate-500 uppercase tracking-widest">
        {label}
      </span>
    </div>
  );
}

// ------------------------------------------------------------------ //
// Section divider                                                      //
// ------------------------------------------------------------------ //

export function HudDivider() {
  return (
    <div
      className="w-full h-px my-3"
      style={{
        background:
          "linear-gradient(90deg, transparent, rgba(0,200,255,0.25), transparent)",
      }}
    />
  );
}
