// Small presentational helpers shared across pages.

export function Spinner({ className = "h-5 w-5" }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-90" d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
    </svg>
  );
}

export function Eyebrow({ children }) {
  return <p className="eyebrow">{children}</p>;
}

// Score ring — the app's recurring motif for any 0–max score.
export function ScoreRing({ value = 0, max = 100, size = 132, label }) {
  const pct = Math.max(0, Math.min(1, value / max));
  const r = size / 2 - 10;
  const c = 2 * Math.PI * r;
  const tone =
    pct >= 0.75 ? "text-emerald-500" : pct >= 0.5 ? "text-amber-500" : "text-rose-500";
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          className="stroke-gray-200 dark:stroke-night-600"
          strokeWidth="10"
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          className={`${tone} transition-[stroke-dashoffset] duration-700 ease-out`}
          strokeWidth="10"
          strokeLinecap="round"
          fill="none"
          stroke="currentColor"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - pct)}
        />
      </svg>
      <div className="absolute text-center">
        <div className="font-mono text-2xl font-semibold">{Math.round(value)}</div>
        {label && <div className="text-[11px] uppercase tracking-wide text-gray-500">{label}</div>}
      </div>
    </div>
  );
}

export function Alert({ children, tone = "error" }) {
  const tones = {
    error: "border-rose-300 bg-rose-50 text-rose-800 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200",
    info: "border-brand-300 bg-brand-50 text-brand-800 dark:border-brand-500/40 dark:bg-brand-500/10 dark:text-brand-200",
    warn: "border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200",
  };
  return <div className={`rounded-xl border px-4 py-3 text-sm ${tones[tone]}`}>{children}</div>;
}

// Reusable "not built yet" banner for placeholder features.
export function ComingSoon({ children }) {
  return (
    <span className="chip border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200">
      Coming soon
      {children ? <span className="ml-1 font-normal opacity-80">· {children}</span> : null}
    </span>
  );
}
