import { useState } from "react";
import { generateMcqs } from "../api/mcq";
import { recordMcqSet } from "../lib/progress";
import { SUBJECTS, DIFFICULTIES, QUESTION_COUNTS } from "../data/subjects";
import { Eyebrow, Spinner, ScoreRing, Alert } from "../components/ui";
import { IconSpark, IconCheck, IconX } from "../components/icons";

const LETTERS = ["A", "B", "C", "D"];

export default function McqPractice() {
  const [subject, setSubject] = useState(SUBJECTS[0]);
  const [difficulty, setDifficulty] = useState("medium");
  const [count, setCount] = useState(5);

  const [questions, setQuestions] = useState(null);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate() {
    setError("");
    setLoading(true);
    setQuestions(null);
    setAnswers({});
    setSubmitted(false);
    try {
      const res = await generateMcqs({ topic: subject.topic, count, difficulty });
      // Normalise: ensure each question has a stable id.
      const qs = (res.questions || []).map((q, i) => ({ ...q, id: q.id ?? i + 1 }));
      if (qs.length === 0) throw new Error("The generator returned no questions. Try again.");
      setQuestions(qs);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function choose(qid, letter) {
    if (submitted) return;
    setAnswers((a) => ({ ...a, [qid]: letter }));
  }

  const answeredCount = Object.keys(answers).length;
  const score = questions ? questions.filter((q) => answers[q.id] === q.correct_answer).length : 0;

  function handleCheckAnswers() {
    setSubmitted(true);
    recordMcqSet({
      subject: subject.label,
      difficulty,
      correct: score,
      total: questions.length,
    });
  }

  return (
    <div className="mx-auto max-w-3xl animate-fade-up">
      <Eyebrow>mcq practice</Eyebrow>
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">MCQ Practice Generator</h1>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        Pick a subject, difficulty and length. We’ll generate a fresh set with answers and explanations.
      </p>

      {/* Config */}
      <div className="card mt-6 p-6">
        <span className="field-label">Subject</span>
        <div className="grid gap-2 sm:grid-cols-2">
          {SUBJECTS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSubject(s)}
              className={`rounded-xl border p-3 text-left transition ${
                subject.id === s.id
                  ? "border-brand-400 bg-brand-50 dark:border-brand-500/50 dark:bg-brand-500/10"
                  : "border-gray-200 hover:border-gray-300 dark:border-night-600 dark:hover:border-night-500"
              }`}
            >
              <p className="text-sm font-semibold">{s.label}</p>
              <p className="mt-0.5 text-xs leading-snug text-gray-500">{s.blurb}</p>
            </button>
          ))}
        </div>

        <div className="mt-5 grid gap-5 sm:grid-cols-2">
          <div>
            <span className="field-label">Difficulty</span>
            <div className="flex flex-wrap gap-2">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setDifficulty(d.id)}
                  className={`btn flex-1 ${
                    difficulty === d.id
                      ? "bg-brand-500 text-white"
                      : "border border-gray-200 text-gray-600 hover:bg-gray-100 dark:border-night-600 dark:text-gray-300 dark:hover:bg-night-700"
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <span className="field-label">Number of questions</span>
            <div className="flex gap-2">
              {QUESTION_COUNTS.map((c) => (
                <button
                  key={c}
                  onClick={() => setCount(c)}
                  className={`btn flex-1 font-mono ${
                    count === c
                      ? "bg-brand-500 text-white"
                      : "border border-gray-200 text-gray-600 hover:bg-gray-100 dark:border-night-600 dark:text-gray-300 dark:hover:bg-night-700"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4">
            <Alert>{error}</Alert>
          </div>
        )}

        <button className="btn-primary mt-5" onClick={handleGenerate} disabled={loading}>
          {loading ? <Spinner /> : <IconSpark className="h-5 w-5" />}
          {loading ? "Generating…" : questions ? "Generate a new set" : "Generate questions"}
        </button>
      </div>

      {/* Quiz */}
      {questions && (
        <div className="mt-6 space-y-4 animate-fade-up">
          {!submitted && (
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span className="font-mono">
                {answeredCount}/{questions.length} answered
              </span>
              <span>{subject.label} · {difficulty}</span>
            </div>
          )}

          {submitted && (
            <div className="card flex flex-col items-center gap-5 p-6 sm:flex-row">
              <ScoreRing value={(score / questions.length) * 100} max={100} label={`${score}/${questions.length}`} />
              <div>
                <p className="eyebrow">result</p>
                <h2 className="mt-1 font-display text-2xl font-bold">
                  {score} out of {questions.length} correct
                </h2>
                <p className="mt-1 text-gray-600 dark:text-gray-400">
                  {subject.label} · {difficulty} difficulty. Review the explanations below.
                </p>
              </div>
            </div>
          )}

          {questions.map((q, idx) => (
            <div key={q.id} className="card p-6">
              <div className="flex gap-3">
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-gray-100 font-mono text-sm dark:bg-night-700">
                  {idx + 1}
                </span>
                <p className="font-medium leading-relaxed">{q.question}</p>
              </div>

              <div className="mt-4 space-y-2">
                {LETTERS.map((L) => {
                  const optText = q.options?.[L];
                  if (optText == null) return null;
                  const chosen = answers[q.id] === L;
                  const isCorrect = q.correct_answer === L;
                  let cls =
                    "border-gray-200 hover:border-gray-300 dark:border-night-600 dark:hover:border-night-500";
                  if (submitted) {
                    if (isCorrect)
                      cls = "border-emerald-400 bg-emerald-50 dark:border-emerald-500/50 dark:bg-emerald-500/10";
                    else if (chosen)
                      cls = "border-rose-400 bg-rose-50 dark:border-rose-500/50 dark:bg-rose-500/10";
                    else cls = "border-gray-200 dark:border-night-600 opacity-70";
                  } else if (chosen) {
                    cls = "border-brand-400 bg-brand-50 dark:border-brand-500/50 dark:bg-brand-500/10";
                  }
                  return (
                    <button
                      key={L}
                      onClick={() => choose(q.id, L)}
                      disabled={submitted}
                      className={`flex w-full items-center gap-3 rounded-xl border px-3.5 py-2.5 text-left text-sm transition ${cls}`}
                    >
                      <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md border border-gray-300 font-mono text-xs dark:border-night-500">
                        {L}
                      </span>
                      <span className="flex-1">{optText}</span>
                      {submitted && isCorrect && <IconCheck className="h-4 w-4 text-emerald-600" />}
                      {submitted && chosen && !isCorrect && <IconX className="h-4 w-4 text-rose-600" />}
                    </button>
                  );
                })}
              </div>

              {submitted && q.explanation && (
                <div className="mt-4 rounded-xl bg-gray-50 p-4 text-sm dark:bg-night-700/60">
                  <span className="font-semibold">Why: </span>
                  <span className="text-gray-600 dark:text-gray-300">{q.explanation}</span>
                </div>
              )}
            </div>
          ))}

          {!submitted && (
            <button
              className="btn-primary w-full sm:w-auto"
              onClick={handleCheckAnswers}
              disabled={answeredCount < questions.length}
            >
              <IconCheck className="h-5 w-5" />
              {answeredCount < questions.length
                ? `Answer all ${questions.length} to submit`
                : "Check answers"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
