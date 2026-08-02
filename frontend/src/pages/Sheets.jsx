import { SHEETS } from "../data/sheets";
import { Eyebrow } from "../components/ui";
import { IconRoute, IconExternal } from "../components/icons";

function SheetCard({ sheet }) {
  return (
    <a
      href={sheet.url}
      target="_blank"
      rel="noopener noreferrer"
      className="card group flex flex-col p-6 transition hover:-translate-y-0.5 hover:border-brand-300 dark:hover:border-brand-500/50"
    >
      <div className="flex items-start justify-between">
        <span className="grid h-11 w-11 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
          <IconRoute className="h-6 w-6" />
        </span>
        <span className="font-mono text-sm text-gray-400">{sheet.problems}</span>
      </div>

      <h3 className="mt-4 font-display text-lg font-semibold">{sheet.name}</h3>
      <p className="text-xs text-gray-500">by {sheet.author}</p>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-gray-600 dark:text-gray-400">{sheet.desc}</p>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {sheet.tags.map((t) => (
          <span key={t} className="chip border-gray-200 dark:border-night-600">
            {t}
          </span>
        ))}
      </div>

      <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 dark:text-brand-300">
        Open sheet
        <IconExternal className="h-4 w-4 transition group-hover:translate-x-0.5" />
      </span>
    </a>
  );
}

export default function Sheets() {
  return (
    <div className="mx-auto max-w-5xl animate-fade-up">
      <Eyebrow>dsa sheets</Eyebrow>
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">DSA Practice Sheets</h1>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        Trusted problem sheets from across the community. The mock interview here samples DSA questions from
        Striver’s A2Z sheet, so it pairs well with the first card.
      </p>

      <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {SHEETS.map((s) => (
          <SheetCard key={s.id} sheet={s} />
        ))}
      </div>
    </div>
  );
}
