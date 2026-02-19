import { motion, AnimatePresence } from "framer-motion";
import { useAppStore } from "../../store/useAppStore";

export default function Toast() {
  const msg = useAppStore((s) => s.toastMessage);

  return (
    <AnimatePresence>
      {msg && (
        <motion.div
          key="toast"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 30 }}
          transition={{ duration: 0.25 }}
          className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[9999] px-4 py-2
            rounded-lg bg-black/70 backdrop-blur-md border border-hud-accent/30
            text-xs font-mono text-hud-accent shadow-lg pointer-events-none"
        >
          {msg}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
