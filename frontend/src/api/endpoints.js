// All backend paths in one place (relative to API_BASE = /api/v1). Migrating the
// backend prefix is a one-file change here + API_BASE in client.js.
export const ENDPOINTS = {
  auth: {
    register: "/auth/register",
    login: "/auth/login",
    refresh: "/auth/refresh",
    logout: "/auth/logout",
    guest: "/auth/guest",
    claim: "/auth/claim",
  },
  users: {
    me: "/users/me",
  },
  interview: {
    start: "/ai/interview/start",
    answer: "/ai/interview/answer",
    codeReview: "/ai/interview/code-review",
    session: (id) => `/ai/interview/session/${id}`,
    history: "/ai/interview/history",
  },
  mcq: {
    generate: "/ai/mcq/generate",
    dailyChallenge: "/ai/mcq/daily-challenge",
    attempt: "/ai/mcq/attempt",
    history: "/ai/mcq/history",
  },
  resume: {
    analyze: "/ai/resume/analyze",
    atsScore: "/ai/resume/ats-score",
    improveBullet: "/ai/resume/improve-bullet",
    placementCheck: "/ai/resume/placement-check",
    pdfToJson: "/ai/resume/pdf-to-json",
    analyzePdf: "/ai/resume/analyze-pdf",
    history: "/ai/resume/history",
  },
  oa: {
    problem: "/ai/oa/problem",
    run: "/ai/oa/run",
    submit: "/ai/oa/submit",
    submission: (id) => `/ai/oa/submission/${id}`,
  },
  notes: {
    list: "/notes",
    adminList: "/admin/notes",
    adminCreate: "/admin/notes",
    adminUpdate: (id) => `/admin/notes/${id}`,
  },
};
