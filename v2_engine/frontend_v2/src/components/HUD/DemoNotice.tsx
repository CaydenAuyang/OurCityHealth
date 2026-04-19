/**
 * DemoNotice
 *
 * Transparency banner that explains why globe coverage is selective in the
 * publicly-deployed demo build.
 *
 * Two surfaces:
 *   1. Persistent "Demo build · why coverage is limited" pill in the brand
 *      bar — always clickable, always visible, never goes away.
 *   2. First-visit modal that auto-opens once per browser. Dismissed via the
 *      X button or by clicking the backdrop. Dismissal is remembered in
 *      localStorage so repeat visitors aren't pestered.
 *
 * The pill is the primary affordance. The auto-open modal exists so a CCMF
 * reviewer (or any first-time visitor) understands the data scope before
 * forming a judgement.
 */

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const STORAGE_KEY = "och.demo-notice.dismissed-v1";

// ------------------------------------------------------------------ //
// Pill button (lives in the brand bar)                                //
// ------------------------------------------------------------------ //

interface DemoBadgeProps {
  onClick: () => void;
}

export function DemoBadge({ onClick }: DemoBadgeProps) {
  return (
    <button
      onClick={onClick}
      title="Why this demo doesn't have data for every date or city"
      className="
        flex items-center gap-1.5 px-2 py-0.5 rounded-full
        border border-amber-400/30 bg-amber-400/5
        text-[10px] font-mono uppercase tracking-wider
        text-amber-300/90 hover:text-amber-200
        hover:border-amber-300/50 hover:bg-amber-400/10
        transition-colors
      "
    >
      <svg
        viewBox="0 0 16 16"
        className="w-2.5 h-2.5 fill-current"
        aria-hidden="true"
      >
        <path d="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zm0 3.25a.875.875 0 1 1 0 1.75.875.875 0 0 1 0-1.75zm.75 7.25h-1.5V7.5h1.5v4.5z" />
      </svg>
      Demo build · why
    </button>
  );
}

// ------------------------------------------------------------------ //
// Modal explaining data coverage                                       //
// ------------------------------------------------------------------ //

interface DemoModalProps {
  open: boolean;
  onClose: () => void;
}

export function DemoModal({ open, onClose }: DemoModalProps) {
  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="demo-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
          onClick={onClose}
          className="fixed inset-0 z-[10000] flex items-center justify-center
            bg-black/60 backdrop-blur-sm pointer-events-auto p-4"
        >
          <motion.div
            key="demo-modal"
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.96 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-xl max-h-[90vh] overflow-y-auto
              rounded-2xl bg-[rgba(5,10,25,0.95)] border border-amber-400/25
              shadow-[0_0_40px_rgba(251,191,36,0.15)]"
          >
            {/* Top accent line */}
            <div
              className="absolute top-0 inset-x-0 h-px"
              style={{
                background:
                  "linear-gradient(90deg, transparent, rgba(251,191,36,0.6), transparent)",
              }}
            />

            {/* Header */}
            <div className="flex items-start justify-between px-6 pt-6 pb-3">
              <div>
                <p className="text-[10px] font-mono uppercase tracking-widest text-amber-300/80">
                  Public demonstration build
                </p>
                <h2 className="text-lg font-semibold text-slate-100 mt-1">
                  About the data you see here
                </h2>
              </div>
              <button
                onClick={onClose}
                aria-label="Close"
                className="text-slate-500 hover:text-slate-200 text-xl leading-none
                  px-2 -mr-2 -mt-1 rounded transition-colors"
              >
                ×
              </button>
            </div>

            {/* Body */}
            <div className="px-6 pb-6 space-y-4 text-[13px] leading-relaxed text-slate-300">
              {/* Quick start tutorial */}
              <div className="rounded-lg border border-hud-accent/25 bg-hud-accent/[0.04] p-4">
                <p className="text-[10px] font-mono uppercase tracking-widest text-hud-accent/90 mb-3">
                  Quick start · 4 things to try
                </p>
                <ol className="space-y-2.5 text-[12.5px] text-slate-300">
                  <li className="flex gap-2.5">
                    <span className="shrink-0 w-5 h-5 rounded-full border border-hud-accent/40 bg-hud-accent/10 text-hud-accent text-[10px] font-mono flex items-center justify-center">
                      1
                    </span>
                    <span>
                      <span className="text-slate-100">Drag the timeline</span>{" "}
                      at the bottom to travel through history. Cyan segments
                      mark dates with available data; click the calendar icon
                      to jump to a specific day.
                    </span>
                  </li>
                  <li className="flex gap-2.5">
                    <span className="shrink-0 w-5 h-5 rounded-full border border-hud-accent/40 bg-hud-accent/10 text-hud-accent text-[10px] font-mono flex items-center justify-center">
                      2
                    </span>
                    <span>
                      <span className="text-slate-100">
                        Click any colored city dot
                      </span>{" "}
                      on the globe to fly in and see its 12-dimension AI
                      assessment, key events, and source citations.
                    </span>
                  </li>
                  <li className="flex gap-2.5">
                    <span className="shrink-0 w-5 h-5 rounded-full border border-hud-accent/40 bg-hud-accent/10 text-hud-accent text-[10px] font-mono flex items-center justify-center">
                      3
                    </span>
                    <span>
                      <span className="text-slate-100">
                        Use the City Explorer
                      </span>{" "}
                      on the left to search and filter all 1,000 cities. Toggle{" "}
                      <span className="text-hud-accent/90">data only</span> to
                      hide cities without GDELT activity for the selected date.
                    </span>
                  </li>
                  <li className="flex gap-2.5">
                    <span className="shrink-0 w-5 h-5 rounded-full border border-hud-accent/40 bg-hud-accent/10 text-hud-accent text-[10px] font-mono flex items-center justify-center">
                      4
                    </span>
                    <span>
                      <span className="text-slate-100">Press</span>{" "}
                      <kbd className="px-1.5 py-0.5 rounded border border-white/15 bg-white/5 text-[10px] font-mono text-slate-200">
                        ?
                      </kbd>{" "}
                      to see all keyboard shortcuts (compare cities, time
                      playback, navigation).
                    </span>
                  </li>
                </ol>
              </div>

              <p>
                This globe is a public demonstration of the Our City Health
                platform. The full system is designed to score 1,000+ cities
                continuously across 12 civic dimensions, but{" "}
                <span className="text-amber-200">
                  the publicly-accessible build ships with a curated subset
                  of pre-computed data
                </span>{" "}
                so it loads instantly and costs nothing to run.
              </p>

              <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4 space-y-3">
                <div>
                  <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-1.5">
                    What's available
                  </p>
                  <ul className="space-y-1 text-[12.5px]">
                    <li>
                      <span className="text-hud-accent">·</span>{" "}
                      <span className="text-slate-200">1,000 cities</span>{" "}
                      loaded on the globe (every dot is a real city)
                    </li>
                    <li>
                      <span className="text-hud-accent">·</span>{" "}
                      <span className="text-slate-200">102 days</span> of
                      raw GDELT-derived stability scores spanning 2014 and
                      2023-2024
                    </li>
                    <li>
                      <span className="text-hud-accent">·</span>{" "}
                      <span className="text-slate-200">
                        7 cities with deep AI analysis
                      </span>
                      : Hong Kong, Shanghai, Shenzhen, Singapore, Tokyo,
                      London, New York
                    </li>
                    <li>
                      <span className="text-hud-accent">·</span> Each AI
                      analysis includes 12-dimension scores, week-over-week
                      deltas, causal drivers, and source citations
                    </li>
                  </ul>
                </div>

                <div>
                  <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-1.5">
                    Why it isn't every city, every day
                  </p>
                  <p className="text-[12.5px]">
                    Each AI evaluation requires a frontier large language
                    model call against several hundred curated articles per
                    city. At commercial scale that runs into significant
                    monthly compute spend. For a public demonstration we
                    pre-compute a representative sample rather than expose a
                    live API that anonymous traffic could rack up costs on.
                  </p>
                </div>

                <div>
                  <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-1.5">
                    What you can still do
                  </p>
                  <p className="text-[12.5px]">
                    Click any of the 7 highlighted cities and scrub the
                    timeline. If you land on a date without an exact
                    snapshot, the panel automatically shows the closest
                    available analysis for that city. Sparklines and globe
                    colors work across the full coverage range.
                  </p>
                </div>
              </div>

              <p className="text-[12px] text-slate-500">
                Production deployments score the full city catalogue on a
                continuous schedule. Reach out if you'd like a walkthrough
                of the live ingestion and scoring pipeline.
              </p>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-white/5 flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-widest text-slate-600">
                You can re-open this from the brand bar
              </span>
              <button
                onClick={onClose}
                className="px-4 py-1.5 rounded-md text-[12px] font-medium
                  bg-amber-400/15 hover:bg-amber-400/25
                  border border-amber-400/30 text-amber-200
                  transition-colors"
              >
                Got it
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ------------------------------------------------------------------ //
// Hook that owns the open/dismiss state                               //
// ------------------------------------------------------------------ //

export function useDemoNotice() {
  const [open, setOpen] = useState(false);

  // Auto-open on first visit
  useEffect(() => {
    try {
      const dismissed = localStorage.getItem(STORAGE_KEY);
      if (!dismissed) {
        // Slight delay so the globe renders behind the modal first — feels
        // more deliberate than a flash on page load.
        const t = setTimeout(() => setOpen(true), 800);
        return () => clearTimeout(t);
      }
    } catch {
      /* localStorage unavailable (privacy mode) — silently skip auto-open */
    }
  }, []);

  const close = () => {
    setOpen(false);
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* ignore */
    }
  };

  const reopen = () => setOpen(true);

  return { open, close, reopen };
}
