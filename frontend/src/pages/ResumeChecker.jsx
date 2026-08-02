import { useRef, useState } from "react";
import { analyzePdf, pdfToJson, atsScore } from "../api/resume";
import { Eyebrow, Spinner, ScoreRing, Alert } from "../components/ui";
import { IconUpload, IconDoc, IconCheck, IconX } from "../components/icons";

const SECTION_MAX = {
  contact_info: 10,
  skills: 20,
  experience: 30,
  projects: 25,
  education: 15,
};
const SECTION_LABEL = {
  contact_info: "Contact info",
  skills: "Skills",
  experience: "Experience",
  projects: "Projects",
  education: "Education",
};

function SectionBar({ name, value }) {
  const max = SECTION_MAX[name] || 100;
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-gray-600 dark:text-gray-300">{SECTION_LABEL[name] || name}</span>
        <span className="font-mono text-gray-500">
          {value}/{max}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-night-700">
        <div className="h-full rounded-full bg-brand-500 transition-[width] duration-700" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function ProbabilityChip({ value }) {
  const v = (value || "").toLowerCase();
  const tone =
    v === "high"
      ? "border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200"
      : v === "medium"
      ? "border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200"
      : "border-rose-300 bg-rose-50 text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200";
  return <span className={`chip ${tone}`}>Shortlist: {value}</span>;
}

function List({ items, tone = "default" }) {
  const marker =
    tone === "good" ? (
      <IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
    ) : tone === "bad" ? (
      <IconX className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" />
    ) : (
      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
    );
  return (
    <ul className="space-y-2 text-sm">
      {(items || []).map((it, i) => (
        <li key={i} className="flex gap-2 leading-relaxed text-gray-600 dark:text-gray-300">
          {marker}
          <span>{it}</span>
        </li>
      ))}
    </ul>
  );
}

export default function ResumeChecker() {
  const [file, setFile] = useState(null);
  const [role, setRole] = useState("");
  const [companies, setCompanies] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  // Optional ATS-against-JD flow (uses extracted resume text).
  const [resumeText, setResumeText] = useState("");
  const [jd, setJd] = useState("");
  const [atsLoading, setAtsLoading] = useState(false);
  const [atsError, setAtsError] = useState("");
  const [ats, setAts] = useState(null);

  const inputRef = useRef(null);

  function pickFile(f) {
    if (!f) return;
    if (f.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      return;
    }
    setError("");
    setFile(f);
  }

  async function handleAnalyze() {
    if (!file || !role.trim()) return;
    setError("");
    setLoading(true);
    setResult(null);
    setAts(null);
    setResumeText("");
    try {
      const res = await analyzePdf({ file, targetRole: role.trim(), targetCompanies: companies.trim() });
      setResult(res.analysis);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAts() {
    if (!jd.trim() || !file) return;
    setAtsError("");
    setAtsLoading(true);
    setAts(null);
    try {
      let text = resumeText;
      if (!text) {
        const parsed = await pdfToJson({ file });
        text = parsed.resume_text;
        setResumeText(text);
      }
      const res = await atsScore({ resumeText: text, jobDescription: jd.trim() });
      setAts(res.details);
    } catch (e) {
      setAtsError(e.message);
    } finally {
      setAtsLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl animate-fade-up">
      <Eyebrow>resume checker</Eyebrow>
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight">Resume Checker</h1>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        Upload your resume as a PDF and get an ATS-style score, a section breakdown, and specific fixes for the
        role you’re targeting.
      </p>

      {/* Upload form */}
      <div className="card mt-6 p-6">
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            pickFile(e.dataTransfer.files?.[0]);
          }}
          onClick={() => inputRef.current?.click()}
          className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 px-6 py-10 text-center transition hover:border-brand-400 dark:border-night-600"
        >
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => pickFile(e.target.files?.[0])}
          />
          {file ? (
            <div className="flex items-center gap-3">
              <IconDoc className="h-8 w-8 text-brand-500" />
              <div className="text-left">
                <p className="text-sm font-medium">{file.name}</p>
                <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(0)} KB · click to replace</p>
              </div>
            </div>
          ) : (
            <>
              <IconUpload className="h-8 w-8 text-gray-400" />
              <p className="mt-2 text-sm font-medium">Drop your resume PDF here, or click to browse</p>
              <p className="text-xs text-gray-500">PDF only · max 10 MB · text-based (not scanned)</p>
            </>
          )}
        </div>

        <div className="mt-5 grid gap-5 sm:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="role">
              Target role
            </label>
            <input
              id="role"
              className="field"
              placeholder="e.g. Software Engineer"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            />
          </div>
          <div>
            <label className="field-label" htmlFor="companies">
              Target companies <span className="font-normal text-gray-400">(optional)</span>
            </label>
            <input
              id="companies"
              className="field"
              placeholder="e.g. Google, Amazon"
              value={companies}
              onChange={(e) => setCompanies(e.target.value)}
            />
          </div>
        </div>

        {error && (
          <div className="mt-4">
            <Alert>{error}</Alert>
          </div>
        )}

        <button className="btn-primary mt-5" onClick={handleAnalyze} disabled={loading || !file || !role.trim()}>
          {loading ? <Spinner /> : <IconCheck className="h-5 w-5" />}
          {loading ? "Analyzing resume…" : "Analyze resume"}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="mt-6 space-y-6 animate-fade-up">
          <div className="card flex flex-col items-center gap-6 p-6 sm:flex-row">
            <ScoreRing value={result.overall_score} max={100} label="score" />
            <div className="flex-1">
              <div className="flex flex-wrap gap-2">
                <ProbabilityChip value={result.shortlist_probability} />
                {result.experience_level_detected && (
                  <span className="chip border-gray-200 dark:border-night-600">
                    Level: {result.experience_level_detected}
                  </span>
                )}
              </div>
              <p className="mt-3 leading-relaxed text-gray-700 dark:text-gray-300">{result.verdict}</p>
            </div>
          </div>

          {result.section_scores && (
            <div className="card p-6">
              <p className="eyebrow">section scores</p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                {Object.entries(result.section_scores).map(([k, v]) => (
                  <SectionBar key={k} name={k} value={v} />
                ))}
              </div>
            </div>
          )}

          <div className="grid gap-6 sm:grid-cols-2">
            <div className="card p-6">
              <p className="eyebrow">strengths</p>
              <div className="mt-4">
                <List items={result.strengths} tone="good" />
              </div>
            </div>
            <div className="card p-6">
              <p className="eyebrow">critical issues</p>
              <div className="mt-4">
                <List items={result.critical_issues} tone="bad" />
              </div>
            </div>
          </div>

          {result.missing_keywords?.length > 0 && (
            <div className="card p-6">
              <p className="eyebrow">missing keywords</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {result.missing_keywords.map((k, i) => (
                  <span key={i} className="chip border-gray-200 font-mono dark:border-night-600">
                    {k}
                  </span>
                ))}
              </div>
            </div>
          )}

          {result.quick_wins?.length > 0 && (
            <div className="card p-6">
              <p className="eyebrow">quick wins</p>
              <div className="mt-4">
                <List items={result.quick_wins} />
              </div>
            </div>
          )}

          {/* Optional: true ATS score against a specific JD */}
          <div className="card p-6">
            <p className="eyebrow">ats match against a job</p>
            <h3 className="mt-2 font-display text-lg font-semibold">Score against a specific job description</h3>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Paste a job description to see how your resume scores as an ATS scan against that exact posting.
            </p>
            <textarea
              className="field mt-4 min-h-[120px] resize-y"
              placeholder="Paste the full job description here…"
              value={jd}
              onChange={(e) => setJd(e.target.value)}
            />
            {atsError && (
              <div className="mt-3">
                <Alert>{atsError}</Alert>
              </div>
            )}
            <button className="btn-ghost mt-4" onClick={handleAts} disabled={atsLoading || !jd.trim()}>
              {atsLoading ? <Spinner /> : null}
              {atsLoading ? "Scanning…" : "Get ATS score"}
            </button>

            {ats && (
              <div className="mt-6 space-y-5 animate-fade-up border-t border-gray-100 pt-6 dark:border-night-700">
                <div className="flex flex-col items-center gap-5 sm:flex-row">
                  <ScoreRing value={ats.ats_score} max={100} label="ATS" size={112} />
                  <div className="flex flex-wrap gap-2">
                    <span
                      className={`chip ${
                        ats.will_pass_ats
                          ? "border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200"
                          : "border-rose-300 bg-rose-50 text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200"
                      }`}
                    >
                      {ats.will_pass_ats ? "Likely to pass ATS" : "May be filtered out"}
                    </span>
                    {ats.keyword_match?.match_percentage != null && (
                      <span className="chip border-gray-200 font-mono dark:border-night-600">
                        {ats.keyword_match.match_percentage}% keyword match
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid gap-6 sm:grid-cols-2">
                  {ats.keyword_match?.matched_keywords?.length > 0 && (
                    <div>
                      <p className="mb-2 text-sm font-semibold">Matched keywords</p>
                      <div className="flex flex-wrap gap-1.5">
                        {ats.keyword_match.matched_keywords.map((k, i) => (
                          <span
                            key={i}
                            className="chip border-emerald-200 bg-emerald-50 font-mono text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200"
                          >
                            {k}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {ats.keyword_match?.missing_keywords?.length > 0 && (
                    <div>
                      <p className="mb-2 text-sm font-semibold">Missing keywords</p>
                      <div className="flex flex-wrap gap-1.5">
                        {ats.keyword_match.missing_keywords.map((k, i) => (
                          <span
                            key={i}
                            className="chip border-rose-200 bg-rose-50 font-mono text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200"
                          >
                            {k}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {ats.recommended_additions?.length > 0 && (
                  <div>
                    <p className="mb-2 text-sm font-semibold">Recommended additions</p>
                    <List items={ats.recommended_additions} />
                  </div>
                )}

                {ats.rewritten_summary && (
                  <div className="rounded-xl bg-gray-50 p-4 dark:bg-night-700/60">
                    <p className="text-sm font-semibold">Optimized summary you can paste in</p>
                    <p className="mt-1 text-sm leading-relaxed text-gray-600 dark:text-gray-300">
                      {ats.rewritten_summary}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
