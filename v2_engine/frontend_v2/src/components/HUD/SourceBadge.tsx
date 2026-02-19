const TIER_CONFIG: Record<number, { icon: string; color: string }> = {
  1: { icon: "★", color: "#F59E0B" },
  2: { icon: "✦", color: "#94A3B8" },
  3: { icon: "◆", color: "#D97706" },
  4: { icon: "○", color: "#6B7280" },
};

interface SourceBadgeProps {
  sourceName?: string;
  tier: number;
  showName?: boolean;
}

export function SourceBadge({
  sourceName,
  tier,
  showName = true,
}: SourceBadgeProps) {
  const cfg = TIER_CONFIG[tier] ?? TIER_CONFIG[4];
  return (
    <span
      className="inline-flex items-center gap-1 whitespace-nowrap"
      style={{ fontSize: "0.75rem", color: cfg.color }}
    >
      <span>{cfg.icon}</span>
      {showName && sourceName && (
        <span className="text-slate-400">{sourceName}</span>
      )}
    </span>
  );
}

export function TierCounts({
  sources,
}: {
  sources: { tier: number }[];
}) {
  const counts = [0, 0, 0, 0];
  for (const s of sources) {
    const idx = Math.min(Math.max(s.tier, 1), 4) - 1;
    counts[idx]++;
  }
  return (
    <span className="inline-flex gap-1.5 text-[0.65rem]">
      <span style={{ color: "#F59E0B" }}>★{counts[0]}</span>
      <span style={{ color: "#94A3B8" }}>✦{counts[1]}</span>
      <span style={{ color: "#D97706" }}>◆{counts[2]}</span>
      <span style={{ color: "#6B7280" }}>○{counts[3]}</span>
    </span>
  );
}

export function extractDomain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}
