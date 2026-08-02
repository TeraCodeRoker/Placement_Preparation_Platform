import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Eyebrow, ScoreRing } from "../components/ui";
import { TrendChart, SubjectBars, ActivitySplit } from "../components/charts";
import { getHistory, computeStats, clearHistory } from "../lib/progress";
import {
  IconMic,
  IconList,
  IconDoc,
  IconBook,
  IconRoute,
  IconSpark,
  IconArrow,
} from "../components/icons";

/* ------------------------------------------------------------------ */
/* Content                                                             */
/* ------------------------------------------------------------------ */

// A real sequence — the numbering carries meaning, so it's numbered.
const STEPS = [
  {
    title: "Sit a mock interview",
    body: "Pick a difficulty and answer seven questions in your own words. Each answer is scored out of 10 with feedback and a model answer, so you find out what you actually can't explain yet.",
  },
  {
    title: "Close the gaps you found",
    body: "Your weakest subjects surface on the dashboard. Generate MCQ sets on exactly those topics, and read the notes for the units you fumbled.",
  },
  {
    title: "Get the resume past the filter",
    body: "Upload your resume PDF for an ATS-style score and specific fixes. Paste a real job description to see how you'd score against that exact posting.",
  },
];

const FEATURES = [
  {
    icon: IconMic,
    title: "AI mock interview",
    body: "A full round that mirrors a real placement interview: core CS theory plus DSA problem-solving, evaluated question by question.",
    specs: ["5 core CS questions", "2 DSA problems", "Scored 0–10 each"],
  },
  {
    icon: IconDoc,
    title: "Resume checker",
    body: "Section-by-section scoring with strengths, critical issues, missing keywords and quick wins — plus an ATS match against any job description.",
    specs: ["PDF upload", "ATS score", "Rewritten summary"],
  },
  {
    icon: IconList,
    title: "MCQ practice generator",
    body: "Fresh question sets on demand. Nothing is recycled from a fixed bank, so you can keep drilling the same topic without memorising answers.",
    specs: ["4 subjects", "4 difficulty levels", "5–20 questions"],
  },
  {
    icon: IconBook,
    title: "Subject notes",
    body: "Unit-wise revision notes for the core placement subjects, organised the way your syllabus is, for the night before a round.",
    specs: ["OOPS · OS · CN", "DBMS · SE", "Unit-wise PDFs"],
  },
  {
    icon: IconRoute,
    title: "DSA sheet hub",
    body: "Direct links to the problem sheets people actually finish, so you're not hunting for them. The interview draws its DSA questions from Striver's A2Z.",
    specs: ["Striver A2Z & SDE", "NeetCode 150", "Blind 75 · 450 DSA"],
  },
  {
    icon: IconSpark,
    title: "Progress tracking",
    body: "Every interview and MCQ set is recorded, then turned into a score trend and a per-subject accuracy breakdown that tells you where to spend time.",
    specs: ["Score trend", "Subject accuracy", "Practice streak"],
  },
];

/* ------------------------------------------------------------------ */
/* Dashboard pieces                                                    */
/* ------------------------------------------------------------------ */

function StatCard({ label, value, suffix, hint, tone = "default" }) {
  const toneCls =
    tone === "up"
      ? "text-emerald-600 dark:text-emerald-400"
      : tone === "down"
      ? "text-rose-600 dark:text-rose-400"
      : "";
  return (
    <div className="card p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-400">{label}</p>
      <p className={`mt-2 font-mono text-3xl font-semibold ${toneCls}`}>
        {value}
        {suffix && <span className="ml-0.5 text-base text-gray-400">{suffix}</span>}
      </p>
      {hint && <p className="mt-1 text-xs text-gray-500">{hint}</p>}
    </div>
  );
}

function EmptyDashboard() {
  return (
    <div className="card relative overflow-hidden p-10 text-center">
      <div className="dot-grid pointer-events-none absolute inset-0 text-gray-200 [mask-image:radial-gradient(ellipse_at_center,black,transparent_70%)] dark:text-night-600" />
      <div className="relative mx-auto max-w-md">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
          <IconSpark className="h-6 w-6" />
        </span>
        <h3 className="mt-4 font-display text-xl font-semibold">No results yet</h3>
        <p className="mt-2 text-sm leading-relaxed text-gray-600 dark:text-gray-400">
          Finish a mock interview or an MCQ set and your scores, subject strengths and progress over time will
          show up here.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link to="/interview" className="btn-primary">
            <IconMic className="h-5 w-5" />
            Start mock interview
          </Link>
          <Link to="/mcq" className="btn-ghost">
            <IconList className="h-5 w-5" />
            Practice MCQs
          </Link>
        </div>
      </div>
    </div>
  );
}

function RecentActivity({ items }) {
  return (
    <ul className="divide-y divide-gray-100 dark:divide-night-700">
      {items.map((e) => {
        const tone =
          e.percent >= 75
            ? "text-emerald-600 dark:text-emerald-400"
            : e.percent >= 50
            ? "text-amber-600 dark:text-amber-400"
            : "text-rose-600 dark:text-rose-400";
        return (
          <li key={e.id} className="flex items-center gap-3 px-5 py-3.5">
            <span
              className={`h-2 w-2 shrink-0 rounded-full ${
                e.kind === "interview" ? "bg-brand-500" : "bg-amber-400"
              }`}
            />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{e.label}</p>
              <p className="text-xs text-gray-500">
                {new Date(e.at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                {e.total ? ` · ${e.total} questions` : ""}
                {e.difficulty ? ` · ${e.difficulty}` : ""}
              </p>
            </div>
            <span className={`font-mono text-sm font-semibold ${tone}`}>{e.percent}%</span>
          </li>
        );
      })}
    </ul>
  );
}

/* ------------------------------------------------------------------ */

export default function Home() {
  const [stats, setStats] = useState(() => computeStats(getHistory()));

  // Refresh when another page records a result (or another tab does).
  useEffect(() => {
    const refresh = () => setStats(computeStats(getHistory()));
    window.addEventListener("prepstack:history-changed", refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener("prepstack:history-changed", refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);

  const weakest = stats.bySubject.length ? stats.bySubject[stats.bySubject.length - 1] : null;

  return (
    <div className="animate-fade-up">
      {/* ---------------- Hero: what this is ---------------- */}
      <section className="relative overflow-hidden rounded-3xl border border-gray-200 bg-white px-6 py-14 shadow-card sm:px-12 dark:border-night-700 dark:bg-night-800">
        <div className="dot-grid pointer-events-none absolute inset-0 text-gray-200 [mask-image:radial-gradient(ellipse_at_top_left,black,transparent_70%)] dark:text-night-600" />
        <div className="relative max-w-2xl">
          <Eyebrow>your placement command center</Eyebrow>
          <h1 className="mt-4 font-display text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
            Practice the interview,{" "}
            <span className="text-brand-500">not just the syllabus.</span>
          </h1>
          <p className="mt-4 max-w-xl text-base leading-relaxed text-gray-600 dark:text-gray-400">
            Prepstack is a preparation workspace for campus placements. It runs AI mock interviews on your core
            CS subjects and DSA, scores your resume the way an ATS would, and generates unlimited MCQ practice —
            then tracks which topics are actually letting you down.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/interview" className="btn-primary">
              <IconMic className="h-5 w-5" />
              Start mock interview
            </Link>
            {!stats.isEmpty && weakest && (
              <Link to="/mcq" className="btn-ghost">
                Drill {weakest.subject} — your weakest at {weakest.percent}%
                <IconArrow className="h-4 w-4" />
              </Link>
            )}
          </div>

          {/* Returning users get their headline numbers up top. */}
          {!stats.isEmpty && (
            <div className="mt-8 flex flex-wrap gap-x-8 gap-y-3 border-t border-gray-100 pt-6 dark:border-night-700">
              {[
                { k: "sessions", v: stats.sessions },
                { k: "avg score", v: `${stats.avgPercent}%` },
                { k: "questions", v: stats.questions },
                ...(stats.streak > 0 ? [{ k: "day streak", v: stats.streak }] : []),
              ].map((s) => (
                <div key={s.k}>
                  <p className="font-mono text-2xl font-semibold">{s.v}</p>
                  <p className="text-xs uppercase tracking-wide text-gray-400">{s.k}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ---------------- How to use it ---------------- */}
      <section className="mt-16">
        <Eyebrow>how to use it</Eyebrow>
        <h2 className="mt-2 font-display text-2xl font-bold tracking-tight">A loop that actually closes</h2>
        <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">
          Find your weak spots, fix them, then prove the fix stuck. Each pass through takes about half an hour.
        </p>

        <ol className="mt-8 grid gap-6 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <li key={s.title} className="relative">
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-sm font-semibold text-brand-500">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="h-px flex-1 bg-gray-200 dark:bg-night-600" />
              </div>
              <h3 className="mt-3 font-display text-lg font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-600 dark:text-gray-400">{s.body}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* ---------------- Features ---------------- */}
      <section className="mt-16">
        <Eyebrow>what's inside</Eyebrow>
        <h2 className="mt-2 font-display text-2xl font-bold tracking-tight">Six tools, built for placements</h2>

        <div className="mt-8 grid gap-x-10 gap-y-9 sm:grid-cols-2">
          {FEATURES.map(({ icon: Icon, title, body, specs }) => (
            <div key={title} className="flex gap-4">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
                <Icon className="h-5 w-5" />
              </span>
              <div className="min-w-0">
                <h3 className="font-display text-lg font-semibold">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-gray-600 dark:text-gray-400">{body}</p>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {specs.map((sp) => (
                    <span key={sp} className="chip border-gray-200 font-mono text-gray-500 dark:border-night-600">
                      {sp}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ---------------- Dashboard ---------------- */}
      <section className="mt-16 scroll-mt-24" id="dashboard">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <Eyebrow>dashboard</Eyebrow>
            <h2 className="mt-2 font-display text-2xl font-bold tracking-tight">Your performance</h2>
          </div>
          {!stats.isEmpty && (
            <button
              className="text-sm font-medium text-gray-500 underline-offset-4 hover:text-rose-600 hover:underline"
              onClick={() => {
                if (confirm("Clear all saved practice history from this device?")) clearHistory();
              }}
            >
              Clear history
            </button>
          )}
        </div>

        {stats.isEmpty ? (
          <div className="mt-6">
            <EmptyDashboard />
          </div>
        ) : (
          <>
            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Sessions" value={stats.sessions} hint={`${stats.questions} questions answered`} />
              <StatCard label="Average score" value={stats.avgPercent} suffix="%" hint="across all activity" />
              <StatCard label="Best score" value={stats.bestPercent} suffix="%" hint="personal best" />
              <StatCard
                label="Latest vs. average"
                value={stats.delta == null ? "—" : `${stats.delta > 0 ? "+" : ""}${stats.delta}`}
                suffix={stats.delta == null ? "" : "%"}
                tone={stats.delta == null ? "default" : stats.delta >= 0 ? "up" : "down"}
                hint={stats.streak > 0 ? `${stats.streak}-day practice streak` : "practice today to start a streak"}
              />
            </div>

            <div className="mt-5 grid gap-5 lg:grid-cols-3">
              <div className="card p-6 lg:col-span-2">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="eyebrow">score trend</p>
                    <h3 className="mt-1 font-display text-lg font-semibold">Last {stats.trend.length} sessions</h3>
                  </div>
                  <ScoreRing value={stats.avgPercent} max={100} size={78} label="avg" />
                </div>
                <div className="mt-4">
                  <TrendChart data={stats.trend} />
                </div>
              </div>

              <div className="card p-6">
                <p className="eyebrow">accuracy by subject</p>
                <h3 className="mt-1 font-display text-lg font-semibold">Strengths &amp; gaps</h3>
                <div className="mt-5">
                  <SubjectBars data={stats.bySubject} />
                </div>
              </div>
            </div>

            <div className="mt-5 grid gap-5 lg:grid-cols-3">
              <div className="card p-6">
                <p className="eyebrow">practice mix</p>
                <h3 className="mt-1 mb-5 font-display text-lg font-semibold">What you’ve been doing</h3>
                <ActivitySplit interviews={stats.interviews} mcqSets={stats.mcqSets} />
              </div>

              <div className="card overflow-hidden lg:col-span-2">
                <div className="border-b border-gray-200 px-5 py-4 dark:border-night-600">
                  <p className="font-display font-semibold">Recent activity</p>
                </div>
                <RecentActivity items={stats.recent} />
              </div>
            </div>

            <p className="mt-4 text-xs text-gray-500">
              Progress is saved on this device only. Connect a user backend to sync it across devices.
            </p>
          </>
        )}
      </section>
    </div>
  );
}
