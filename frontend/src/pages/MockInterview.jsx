import { useState } from "react";
import { startInterview, submitAnswer } from "../api/interview";
import { recordInterview } from "../lib/progress";
import { Eyebrow, Spinner, ScoreRing, Alert } from "../components/ui";
import { IconMic, IconArrow, IconCheck } from "../components/icons";

const DIFFICULTIES = ["easy", "medium", "hard"];

function TypeChip({ type }) {
  const dsa = type === "dsa";
  return (
    <span
      className={`chip ${
        dsa
          ? "border-brand-300 bg-brand-50 text-brand-700 dark:border-brand-500/40 dark:bg-brand-500/10 dark:text-brand-200"
          : "border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200"
      }`}
    >
      {dsa ? "DSA · Striver A2Z" : "Core CS"}
    </span>
  );
}

function ScoreBadge({ score }) {
  const tone =
    score >= 7 ? "text-emerald-600 dark:text-emerald-400" : score >= 4 ? "text-amber-600 dark:text-amber-400" : "text-rose-600 dark:text-rose-400";
  return (
    <span className={`font-mono text-2xl font-semibold ${tone}`}>
      {score}
      <span className="text-sm text-gray-400">/10</span>
    </span>
  );
}

export default function MockInterview() {
  const [phase, setPhase] = useState("setup"); // setup | question | evaluated | done
  const [userName, setUserName] = useState("");
  const [difficulty, setDifficulty] = useState("medium");

  const [sessionId, setSessionId] = useState(null);
  const [current, setCurrent] = useState(null);
  const [answer, setAnswer] = useState("");
  const [lastEval, setLastEval] = useState(null);
  const [nextQuestion, setNextQuestion] = useState(null);
  const [summary, setSummary] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleStart() {
    setError("");
    setLoading(true);
    try {
      const res = await startInterview({ userName: userName.trim() || "Candidate", difficulty });
      setSessionId(res.session_id);
      setCurrent(res); // res carries the question payload fields
      setAnswer("");
      setLastEval(null);
      setPhase("question");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    if (!answer.trim()) return;
    setError("");
    setLoading(true);
    try {
      const res = await submitAnswer({ sessionId, answer: answer.trim() });
      setLastEval(res.evaluation);
      if (res.is_complete) {
        setSummary(res.summary);
        recordInterview(res.summary); // save to local performance history
        setPhase("done");
      } else {
        setNextQuestion(res.next_question);
        setPhase("evaluated");
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function handleContinue() {
    setCurrent(nextQuestion);
    setNextQuestion(null);
    setLastEval(null);
    setAnswer("");
    setPhase("question");
  }

  function reset() {
    setPhase("setup");
    setSessionId(null);
    setCurrent(null);
    setAnswer("");
    setLastEval(null);
    setNextQuestion(null);
    setSummary(null);
    setError("");
  }

  const progress = current ? (current.question_number / current.total_questions) * 100 : 0;

  return (
    <div className="mx-auto max-w-3xl animate-fade-up">
      <Eyebrow>mock interview</Eyebrow>
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">AI Mock Interview</h1>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        Five core CS questions (OOPS, OS, DBMS, CN, Software Engineering) plus two DSA problems from Striver’s
        A2Z sheet. Answer in your own words — you’re scored on each one.
      </p>

      {error && (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      )}

      {/* SETUP */}
      {phase === "setup" && (
        <div className="card mt-6 p-6">
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label className="field-label" htmlFor="name">
                Your name <span className="font-normal text-gray-400">(optional)</span>
              </label>
              <input
                id="name"
                className="field"
                placeholder="e.g. Aarav"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
              />
            </div>
            <div>
              <span className="field-label">Difficulty</span>
              <div className="flex gap-2">
                {DIFFICULTIES.map((d) => (
                  <button
                    key={d}
                    onClick={() => setDifficulty(d)}
                    className={`btn flex-1 capitalize ${
                      difficulty === d
                        ? "bg-brand-500 text-white"
                        : "border border-gray-200 text-gray-600 hover:bg-gray-100 dark:border-night-600 dark:text-gray-300 dark:hover:bg-night-700"
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-2 text-sm text-gray-500">
            <span className="chip border-gray-200 dark:border-night-600">5 core questions</span>
            <span className="chip border-gray-200 dark:border-night-600">2 DSA questions</span>
            <span className="chip border-gray-200 dark:border-night-600">~7 evaluated answers</span>
          </div>

          <button className="btn-primary mt-6 w-full sm:w-auto" onClick={handleStart} disabled={loading}>
            {loading ? <Spinner /> : <IconMic className="h-5 w-5" />}
            {loading ? "Preparing questions…" : "Start interview"}
          </button>
        </div>
      )}

      {/* QUESTION / EVALUATED */}
      {(phase === "question" || phase === "evaluated") && current && (
        <div className="mt-6 space-y-5">
          {/* progress */}
          <div>
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="font-mono text-gray-500">
                Question {current.question_number} / {current.total_questions}
              </span>
              <TypeChip type={current.question_type} />
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-night-700">
              <div
                className="h-full rounded-full bg-brand-500 transition-[width] duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* question */}
          <div className="card p-6">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
              {current.subject} · {current.topic}
            </p>
            <p className="mt-2 whitespace-pre-wrap font-display text-lg leading-relaxed">{current.question}</p>
          </div>

          {/* answer box (locked once evaluated) */}
          <div className="card p-6">
            <label className="field-label" htmlFor="answer">
              Your answer
            </label>
            <textarea
              id="answer"
              className="field min-h-[160px] resize-y font-sans"
              placeholder={
                current.question_type === "dsa"
                  ? "Explain your approach, the data structures/algorithms you'd use, and the time & space complexity."
                  : "Explain the concept clearly, as you would to an interviewer."
              }
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              disabled={phase === "evaluated" || loading}
            />
            {phase === "question" && (
              <button
                className="btn-primary mt-4"
                onClick={handleSubmit}
                disabled={loading || !answer.trim()}
              >
                {loading ? <Spinner /> : <IconCheck className="h-5 w-5" />}
                {loading ? "Evaluating…" : "Submit answer"}
              </button>
            )}
          </div>

          {/* evaluation */}
          {phase === "evaluated" && lastEval && (
            <div className="card animate-fade-up p-6">
              <div className="flex items-center justify-between">
                <p className="eyebrow">evaluation</p>
                <ScoreBadge score={lastEval.score} />
              </div>
              <div className="mt-4 space-y-4 text-sm">
                <div>
                  <p className="font-semibold text-night-800 dark:text-gray-200">Feedback</p>
                  <p className="mt-1 leading-relaxed text-gray-600 dark:text-gray-400">{lastEval.feedback}</p>
                </div>
                {lastEval.correct_answer && (
                  <div className="rounded-xl bg-gray-50 p-4 dark:bg-night-700/60">
                    <p className="font-semibold text-night-800 dark:text-gray-200">Model answer</p>
                    <p className="mt-1 leading-relaxed text-gray-600 dark:text-gray-400">
                      {lastEval.correct_answer}
                    </p>
                  </div>
                )}
              </div>
              <button className="btn-primary mt-5" onClick={handleContinue}>
                Next question
                <IconArrow className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* DONE */}
      {phase === "done" && summary && (
        <div className="mt-6 space-y-6">
          <div className="card flex flex-col items-center gap-4 p-8 text-center sm:flex-row sm:text-left">
            <ScoreRing value={summary.average_score * 10} max={100} label="avg" />
            <div>
              <p className="eyebrow">interview complete</p>
              <h2 className="mt-1 font-display text-2xl font-bold">
                Nice work{summary.user_name && summary.user_name !== "Candidate" ? `, ${summary.user_name}` : ""}!
              </h2>
              <p className="mt-1 text-gray-600 dark:text-gray-400">
                Average score {summary.average_score}/10 across {summary.total_questions} questions.
              </p>
            </div>
          </div>

          <div className="card overflow-hidden">
            <div className="border-b border-gray-200 px-6 py-4 dark:border-night-600">
              <p className="font-display font-semibold">Per-question breakdown</p>
            </div>
            <ul className="divide-y divide-gray-100 dark:divide-night-700">
              {summary.per_question.map((q) => (
                <li key={q.question_number} className="flex items-center gap-4 px-6 py-4">
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gray-100 font-mono text-sm dark:bg-night-700">
                    {q.question_number}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{q.topic}</p>
                    <p className="truncate text-xs text-gray-500">{q.subject}</p>
                  </div>
                  <ScoreBadge score={q.score} />
                </li>
              ))}
            </ul>
          </div>

          <button className="btn-ghost" onClick={reset}>
            Start a new interview
          </button>
        </div>
      )}
    </div>
  );
}
