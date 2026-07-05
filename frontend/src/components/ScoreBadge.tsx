export function ScoreBadge({ score }: { score: number | null | undefined }) {
  if (score == null) return null;
  const cls =
    score >= 75
      ? 'bg-emerald-400/10 text-emerald-400 ring-emerald-400/20'
      : score >= 50
        ? 'bg-amber-400/10 text-amber-400 ring-amber-400/20'
        : 'bg-slate-400/10 text-slate-400 ring-slate-400/20';
  return (
    <span className={`text-xs font-bold px-2 py-1 rounded-md ring-1 ring-inset ${cls}`}>
      {score}%
    </span>
  );
}
