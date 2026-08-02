import { useState } from "react";
import { Link } from "react-router-dom";
import { ensureGuest } from "../api/auth";
import { generateProblem, runCode, submitCode } from "../api/oa";
import CodeEditor from "../components/CodeEditor";
import { Alert, Eyebrow, ScoreRing, Spinner } from "../components/ui";
import { useAuth } from "../context/AuthContext";

const LANGUAGES = ["python", "java", "cpp", "c", "javascript"];
const PRESETS = [
  { step: "Step 3 - Arrays", topic: "Two Sum" },
  { step: "Step 4 - Binary Search", topic: "Koko Eating Bananas" },
  { step: "Step 9 - Stacks & Queues", topic: "Valid Parentheses" },
  { step: "Step 16 - Dynamic Programming", topic: "Climbing Stairs" },
];

function CaseRow({ result }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-gray-100 py-2 text-sm last:border-0 dark:border-night-700">
      <div className="flex items-center gap-2">
        <span
          className={`chip ${
            result.passed
              ? "border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200"
              : "border-rose-300 bg-rose-50 text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200"
          }`}
        >
          {result.passed ? "passed" : result.timed_out ? "timeout" : "failed"}
        </span>
        <span className="font-mono text-xs text-gray-500">
          {result.visible ? `case #${result.index + 1}` : "hidden case"}
        </span>
      </div>
      {result.visible && result.expected_output != null && (
        <span className="truncate font-mono text-xs text-gray-500">
          expected: {result.expected_output}
        </span>
      )}
    </div>
  );
}

export default function OA() {
  const { status } = useAuth();
  const [preset, setPreset] = useState(PRESETS[0]);
  const [language, setLanguage] = useState("python");
  const [problem, setProblem] = useState(null);
  const [code, setCode] = useState("");
  const [runResult, setRunResult] = useState(null);
  const [submitResult, setSubmitResult] = useState(null);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  async function handleGenerate() {
    setError("");
    setLoading("generate");
    try {
      await ensureGuest();
      const p = await generateProblem({ step: preset.step, topic: preset.topic, languages: LANGUAGES });
      setProblem(p);
      setCode(p.starter_code?.[language] || "");
      setRunResult(null);
      setSubmitResult(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading("");
    }
  }

  function changeLanguage(lang) {
    setLanguage(lang);
    if (problem) setCode(problem.starter_code?.[lang] || "");
  }

  async function handleRun() {
    setError("");
    setSubmitResult(null);
    setLoading("run");
    try {
      setRunResult(await runCode({ problemId: problem.problem_id, language, sourceCode: code }));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading("");
    }
  }

  async function handleSubmit() {
    setError("");
    setRunResult(null);
    setLoading("submit");
    try {
      setSubmitResult(await submitCode({ problemId: problem.problem_id, language, sourceCode: code }));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading("");
    }
  }

  return (
    <div className="mx-auto max-w-5xl animate-fade-up">
      <Eyebrow>online assessment</Eyebrow>
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">OA Coding Compiler</h1>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        Generate a DSA problem, write a solution, and run it against real test cases. Submit for a
        graded pass-rate plus an AI code review.
      </p>

      {error && (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      )}

      {/* setup */}
      <div className="card mt-6 grid gap-4 p-6 sm:grid-cols-[1fr_auto_auto]">
        <label className="block">
          <span className="field-label">Problem</span>
          <select
            className="field"
            value={preset.topic}
            onChange={(e) => setPreset(PRESETS.find((p) => p.topic === e.target.value) || PRESETS[0])}
          >
            {PRESETS.map((p) => (
              <option key={p.topic} value={p.topic}>
                {p.topic} · {p.step}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="field-label">Language</span>
          <select className="field" value={language} onChange={(e) => changeLanguage(e.target.value)}>
            {LANGUAGES.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </label>
        <div className="flex items-end">
          <button className="btn-primary w-full" onClick={handleGenerate} disabled={loading === "generate"}>
            {loading === "generate" ? <Spinner /> : null}
            {problem ? "New problem" : "Generate problem"}
          </button>
        </div>
      </div>

      {problem && (
        <div className="mt-6 space-y-5">
          <div className="card p-6">
            <p className="font-display text-lg font-semibold">{problem.title}</p>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-gray-600 dark:text-gray-300">
              {problem.statement}
            </p>
            {problem.time_complexity_hint && (
              <p className="mt-3 font-mono text-xs text-gray-500">
                target: {problem.time_complexity_hint}
              </p>
            )}
          </div>

          <CodeEditor language={language} value={code} onChange={setCode} />

          <div className="flex flex-wrap gap-3">
            <button className="btn-ghost border border-gray-200 dark:border-night-600" onClick={handleRun} disabled={!!loading}>
              {loading === "run" ? <Spinner /> : null}
              Run (visible tests)
            </button>
            <button className="btn-primary" onClick={handleSubmit} disabled={!!loading}>
              {loading === "submit" ? <Spinner /> : null}
              Submit (graded)
            </button>
          </div>

          {runResult && (
            <div className="card p-6">
              <p className="eyebrow">run · visible tests</p>
              <p className="mt-1 font-mono text-sm">
                {runResult.passed}/{runResult.total} passed
              </p>
              <div className="mt-3">
                {runResult.results.map((r) => (
                  <CaseRow key={r.index} result={r} />
                ))}
              </div>
            </div>
          )}

          {submitResult && (
            <div className="space-y-5">
              {submitResult.mode === "ai_review_only" && (
                <Alert tone="warn">
                  Objective execution was unavailable for this attempt — showing the AI review only.
                  Your code was not run against the test cases.
                </Alert>
              )}
              <div className="card flex flex-col items-center gap-5 p-6 sm:flex-row">
                <ScoreRing value={submitResult.final_score} max={100} label="pass rate" />
                <div className="min-w-0 flex-1">
                  <p className="eyebrow">submission</p>
                  <p className="mt-1 font-mono text-sm">
                    {submitResult.pass_count}/{submitResult.total_count} test cases passed
                  </p>
                  {submitResult.ai_review && (
                    <p className="mt-1 font-mono text-sm text-gray-500">
                      AI review: {submitResult.ai_review.review_score}/10 ·{" "}
                      {submitResult.ai_review.time_complexity}
                    </p>
                  )}
                </div>
              </div>

              <div className="card p-6">
                <p className="eyebrow">test cases</p>
                <div className="mt-3">
                  {submitResult.test_results.map((r) => (
                    <CaseRow key={r.index} result={r} />
                  ))}
                </div>
              </div>

              {submitResult.ai_review && (
                <div className="card space-y-3 p-6 text-sm">
                  <p className="eyebrow">ai review</p>
                  <p className="text-gray-600 dark:text-gray-300">
                    {submitResult.ai_review.correctness_rationale}
                  </p>
                  {submitResult.ai_review.suggestions?.length > 0 && (
                    <ul className="list-inside list-disc text-gray-600 dark:text-gray-300">
                      {submitResult.ai_review.suggestions.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {status !== "authed" && (
                <div className="card flex flex-col items-center justify-between gap-3 p-6 text-sm sm:flex-row">
                  <span className="text-gray-600 dark:text-gray-300">
                    Create an account to save this submission to your history.
                  </span>
                  <Link
                    to="/register"
                    className="rounded-lg bg-brand-500 px-4 py-2 font-medium text-white hover:bg-brand-600"
                  >
                    Save my progress
                  </Link>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
