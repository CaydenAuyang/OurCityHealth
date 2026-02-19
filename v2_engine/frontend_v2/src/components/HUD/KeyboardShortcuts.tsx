import { motion, AnimatePresence } from "framer-motion";
import { useAppStore } from "../../store/useAppStore";
import { GlassPanel } from "./GlassPanel";

const SHORTCUTS = [
  { key: "Esc", desc: "Close panel / overlay" },
  { key: "[", desc: "Previous city with data" },
  { key: "]", desc: "Next city with data" },
  { key: "Space", desc: "Play / pause timeline" },
  { key: "/", desc: "Focus search" },
  { key: "F", desc: "Toggle sidebar" },
  { key: "?", desc: "Toggle this overlay" },
] as const;

export function KeyboardShortcuts() {
  const show = useAppStore((s) => s.showShortcuts);
  const toggle = useAppStore((s) => s.toggleShortcuts);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="kb-overlay"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-[9000] flex items-center justify-center pointer-events-auto"
          onClick={toggle}
        >
          <div onClick={(e) => e.stopPropagation()}>
            <GlassPanel accent className="px-6 py-5 w-72">
              <p className="text-[9px] text-slate-600 uppercase tracking-widest mb-4">
                Keyboard Shortcuts
              </p>

              <div className="space-y-2">
                {SHORTCUTS.map((s) => (
                  <div key={s.key} className="flex items-center justify-between">
                    <kbd className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-[10px] font-mono text-hud-accent">
                      {s.key}
                    </kbd>
                    <span className="text-[11px] text-slate-400">{s.desc}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={toggle}
                className="mt-4 w-full text-center text-[10px] text-slate-600 hover:text-slate-400 transition-colors"
              >
                Press ? or Esc to close
              </button>
            </GlassPanel>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
