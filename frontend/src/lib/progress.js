// ---------------------------------------------------------------------------
// Local performance store
// ---------------------------------------------------------------------------
// There's no user/progress backend yet, so results are kept in localStorage on
// the user's own device. The shape below is deliberately close to what a real
// API would return, so swapping to server-side history later means replacing
// the read/write functions here and nothing else.
//
// To migrate: turn getHistory() into a fetch, and record*() into POSTs.
// ---------------------------------------------------------------------------

const KEY = "prepstack:history:v1";
const MAX_ENTRIES = 100;

// Canonical subject buckets, so interview subjects and MCQ subjects line up
// in the same chart.
const SUBJECT_ALIASES = {
  "object oriented programming": "OOPS",
  oops: "OOPS",
  "operating systems": "OS",
  os: "OS",
  "database management systems": "DBMS",
  dbms: "DBMS",
  "computer networks": "CN",
  cn: "CN",
  "software engineering": "SE",
  "data structures & algorithms": "DSA",
  "data structures and algorithms": "DSA",
  dsa: "DSA",
};

export function normalizeSubject(name = "") {
  return SUBJECT_ALIASES[String(name).trim().toLowerCase()] || name || "Other";
}

function read() {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function write(entries) {
  try {
    localStorage.setItem(KEY, JSON.stringify(entries.slice(-MAX_ENTRIES)));
  } catch {
    /* quota or privacy mode — progress just won't persist */
  }
  // Let any mounted dashboard refresh itself.
  window.dispatchEvent(new Event("prepstack:history-changed"));
}

export function getHistory() {
  return read();
}

export function clearHistory() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
  window.dispatchEvent(new Event("prepstack:history-changed"));
}

/** Record a finished mock interview from the backend's summary object. */
export function recordInterview(summary) {
  if (!summary) return;
  const entries = read();
  entries.push({
    id: `iv_${Date.now()}`,
    kind: "interview",
    at: new Date().toISOString(),
    // Normalised to a 0-100 scale so every activity shares one axis.
    percent: Math.round((Number(summary.average_score) || 0) * 10),
    total: summary.total_questions || 0,
    label: "Mock interview",
    subjects: (summary.per_question || []).map((q) => ({
      subject: normalizeSubject(q.subject),
      percent: Math.round((Number(q.score) || 0) * 10),
    })),
  });
  write(entries);
}

/** Record a completed MCQ set. */
export function recordMcqSet({ subject, difficulty, correct, total }) {
  if (!total) return;
  const entries = read();
  const percent = Math.round((correct / total) * 100);
  const s = normalizeSubject(subject);
  entries.push({
    id: `mcq_${Date.now()}`,
    kind: "mcq",
    at: new Date().toISOString(),
    percent,
    total,
    correct,
    difficulty,
    label: `${s} MCQs`,
    subjects: [{ subject: s, percent }],
  });
  write(entries);
}

// ---------------------------------------------------------------------------
// Derived stats for the dashboard
// ---------------------------------------------------------------------------

export function computeStats(entries = read()) {
  if (entries.length === 0) {
    return {
      isEmpty: true,
      sessions: 0,
      questions: 0,
      avgPercent: 0,
      bestPercent: 0,
      interviews: 0,
      mcqSets: 0,
      trend: [],
      bySubject: [],
      recent: [],
      streak: 0,
      delta: null,
    };
  }

  const sorted = [...entries].sort((a, b) => new Date(a.at) - new Date(b.at));
  const sessions = sorted.length;
  const questions = sorted.reduce((n, e) => n + (e.total || 0), 0);
  const avgPercent = Math.round(sorted.reduce((n, e) => n + e.percent, 0) / sessions);
  const bestPercent = Math.max(...sorted.map((e) => e.percent));

  // Per-subject averages, weighted by how many times each came up.
  const buckets = new Map();
  for (const e of sorted) {
    for (const s of e.subjects || []) {
      const b = buckets.get(s.subject) || { subject: s.subject, sum: 0, n: 0 };
      b.sum += s.percent;
      b.n += 1;
      buckets.set(s.subject, b);
    }
  }
  const bySubject = [...buckets.values()]
    .map((b) => ({ subject: b.subject, percent: Math.round(b.sum / b.n), count: b.n }))
    .sort((a, b) => b.percent - a.percent);

  // Improvement: latest session vs. the average of everything before it.
  let delta = null;
  if (sessions >= 2) {
    const prev = sorted.slice(0, -1);
    const prevAvg = prev.reduce((n, e) => n + e.percent, 0) / prev.length;
    delta = Math.round(sorted[sorted.length - 1].percent - prevAvg);
  }

  // Consecutive-day practice streak, counting back from today.
  const days = new Set(sorted.map((e) => new Date(e.at).toDateString()));
  let streak = 0;
  const cursor = new Date();
  while (days.has(cursor.toDateString())) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }

  return {
    isEmpty: false,
    sessions,
    questions,
    avgPercent,
    bestPercent,
    interviews: sorted.filter((e) => e.kind === "interview").length,
    mcqSets: sorted.filter((e) => e.kind === "mcq").length,
    trend: sorted.slice(-12),
    bySubject,
    recent: [...sorted].reverse().slice(0, 6),
    streak,
    delta,
  };
}
