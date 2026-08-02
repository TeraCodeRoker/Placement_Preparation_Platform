// Lightweight SVG charts — no charting library. Each renders into a fixed
// viewBox and scales fluidly with `w-full h-auto`.

const W = 620;
const H = 220;
const PAD = { top: 16, right: 12, bottom: 28, left: 34 };

function niceDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/** Score trend across recent sessions (0–100). */
export function TrendChart({ data = [] }) {
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;

  if (data.length === 0) return null;

  const x = (i) => PAD.left + (data.length === 1 ? innerW / 2 : (i / (data.length - 1)) * innerW);
  const y = (v) => PAD.top + innerH - (v / 100) * innerH;

  const line = data.map((d, i) => `${i === 0 ? "M" : "L"}${x(i)},${y(d.percent)}`).join(" ");
  const area =
    `M${x(0)},${PAD.top + innerH} ` +
    data.map((d, i) => `L${x(i)},${y(d.percent)}`).join(" ") +
    ` L${x(data.length - 1)},${PAD.top + innerH} Z`;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label="Score trend over recent sessions">
      <defs>
        <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.18" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* gridlines + y labels */}
      {[0, 25, 50, 75, 100].map((v) => (
        <g key={v}>
          <line
            x1={PAD.left}
            x2={W - PAD.right}
            y1={y(v)}
            y2={y(v)}
            className="stroke-gray-200 dark:stroke-night-600"
            strokeWidth="1"
            strokeDasharray={v === 0 ? "0" : "3 4"}
          />
          <text
            x={PAD.left - 8}
            y={y(v) + 4}
            textAnchor="end"
            className="fill-gray-400 font-mono"
            style={{ fontSize: 10 }}
          >
            {v}
          </text>
        </g>
      ))}

      <g className="text-brand-500">
        <path d={area} fill="url(#trendFill)" />
        <path d={line} fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        {data.map((d, i) => (
          <g key={d.id}>
            <circle cx={x(i)} cy={y(d.percent)} r="4" fill="currentColor" />
            <circle cx={x(i)} cy={y(d.percent)} r="7" fill="currentColor" opacity="0.15" />
            <title>{`${d.label} — ${d.percent}% (${niceDate(d.at)})`}</title>
          </g>
        ))}
      </g>

      {/* x labels: first, middle, last only, to avoid crowding */}
      {data.map((d, i) => {
        const show = i === 0 || i === data.length - 1 || (data.length > 4 && i === Math.floor((data.length - 1) / 2));
        if (!show) return null;
        return (
          <text
            key={`x${d.id}`}
            x={x(i)}
            y={H - 8}
            textAnchor={i === 0 ? "start" : i === data.length - 1 ? "end" : "middle"}
            className="fill-gray-400 font-mono"
            style={{ fontSize: 10 }}
          >
            {niceDate(d.at)}
          </text>
        );
      })}
    </svg>
  );
}

/** Horizontal accuracy bars per subject. */
export function SubjectBars({ data = [] }) {
  if (data.length === 0) return null;

  const toneFor = (p) =>
    p >= 75 ? "bg-emerald-500" : p >= 50 ? "bg-amber-500" : "bg-rose-500";

  return (
    <div className="space-y-3.5">
      {data.map((s) => (
        <div key={s.subject}>
          <div className="mb-1.5 flex items-baseline justify-between text-sm">
            <span className="font-medium">
              {s.subject}
              <span className="ml-2 font-mono text-xs text-gray-400">×{s.count}</span>
            </span>
            <span className="font-mono text-gray-500">{s.percent}%</span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-gray-200 dark:bg-night-700">
            <div
              className={`h-full rounded-full ${toneFor(s.percent)} transition-[width] duration-700 ease-out`}
              style={{ width: `${s.percent}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Compact split of activity types. */
export function ActivitySplit({ interviews = 0, mcqSets = 0 }) {
  const total = interviews + mcqSets;
  if (!total) return null;
  const ivPct = (interviews / total) * 100;
  return (
    <div>
      <div className="flex h-2.5 overflow-hidden rounded-full bg-gray-200 dark:bg-night-700">
        <div className="bg-brand-500 transition-[width] duration-700" style={{ width: `${ivPct}%` }} />
        <div className="bg-amber-400 transition-[width] duration-700" style={{ width: `${100 - ivPct}%` }} />
      </div>
      <div className="mt-3 flex flex-wrap gap-4 text-sm">
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-brand-500" />
          Interviews <span className="font-mono text-gray-500">{interviews}</span>
        </span>
        <span className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
          MCQ sets <span className="font-mono text-gray-500">{mcqSets}</span>
        </span>
      </div>
    </div>
  );
}
