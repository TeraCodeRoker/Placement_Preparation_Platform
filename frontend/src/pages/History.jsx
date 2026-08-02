import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { interviewHistory } from "../api/interview";
import { mcqHistory } from "../api/mcq";
import { Alert, Eyebrow, Spinner } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { computeStats } from "../lib/progress";

function Stat({ label, value }) {
  return (
    <div className="card p-5 text-center">
      <div className="font-mono text-2xl font-semibold">{value}</div>
      <div className="mt-1 text-xs uppercase tracking-wide text-gray-500">{label}</div>
    </div>
  );
}

export default function History() {
  const { status } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (status !== "authed") return undefined;
    let active = true;
    Promise.all([interviewHistory().catch(() => []), mcqHistory().catch(() => [])])
      .then(([interviews, mcqs]) => active && setData({ interviews, mcqs }))
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [status]);

  if (status === "loading") {
    return (
      <div className="grid place-items-center py-24">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  // Guests: local-only history from localStorage, with a prompt to sync.
  if (status !== "authed") {
    const stats = computeStats();
    return (
      <div className="mx-auto max-w-3xl animate-fade-up">
        <Eyebrow>your progress</Eyebrow>
        <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">History</h1>
        <div className="mt-6">
          <Alert tone="info">
            You&apos;re browsing as a guest — this history is stored only on this device.{" "}
            <Link className="font-medium underline" to="/register">
              Create an account
            </Link>{" "}
            to sync it across sessions.
          </Alert>
        </div>
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Stat label="Sessions" value={stats.sessions} />
          <Stat label="Avg %" value={stats.avgPercent} />
          <Stat label="Interviews" value={stats.interviews} />
          <Stat label="MCQ sets" value={stats.mcqSets} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl">
        <Alert>{error}</Alert>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="grid place-items-center py-24">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl animate-fade-up">
      <Eyebrow>your progress</Eyebrow>
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">History</h1>
      <p className="mt-2 text-gray-600 dark:text-gray-400">Synced to your account.</p>

      <div className="mt-6 grid grid-cols-2 gap-4">
        <Stat label="Interviews" value={data.interviews.length} />
        <Stat label="MCQ attempts" value={data.mcqs.length} />
      </div>

      <div className="card mt-6 p-6">
        <p className="eyebrow">recent interviews</p>
        <ul className="mt-3 divide-y divide-gray-100 dark:divide-night-700">
          {data.interviews.map((s) => (
            <li key={s.session_id} className="flex items-center justify-between gap-3 py-3 text-sm">
              <span className="font-mono text-xs text-gray-500">
                {new Date(s.created_at).toLocaleString()}
              </span>
              <span className="flex items-center gap-2">
                <span className="text-gray-600 dark:text-gray-300">
                  {s.total_questions} questions
                </span>
                <span
                  className={`chip ${
                    s.status === "complete"
                      ? "border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200"
                      : "border-gray-200 dark:border-night-600"
                  }`}
                >
                  {s.status}
                </span>
              </span>
            </li>
          ))}
          {data.interviews.length === 0 && (
            <li className="py-3 text-sm text-gray-500">No interviews yet.</li>
          )}
        </ul>
      </div>

      <div className="card mt-5 p-6">
        <p className="eyebrow">recent mcq attempts</p>
        <ul className="mt-3 divide-y divide-gray-100 dark:divide-night-700">
          {data.mcqs.map((a) => (
            <li key={a.id} className="flex items-center justify-between gap-3 py-3 text-sm">
              <span className="text-gray-600 dark:text-gray-300">{a.subject || "MCQ"}</span>
              <span className="font-mono text-xs text-gray-500">
                {a.correct}/{a.total} · {a.percent}%
              </span>
            </li>
          ))}
          {data.mcqs.length === 0 && (
            <li className="py-3 text-sm text-gray-500">No MCQ attempts yet.</li>
          )}
        </ul>
      </div>
    </div>
  );
}
