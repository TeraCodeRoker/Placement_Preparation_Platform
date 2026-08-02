# Prepstack — Placement Prep Frontend

React + Vite + Tailwind frontend for a tech interview prep platform. Talks to
your existing AI services (mock interview, MCQ, resume analysis) through one
configurable API layer.

## Stack

- **React 18** + **Vite 5**
- **Tailwind CSS 3** (dark/light via `class` strategy)
- **react-router-dom** for routing
- No icon or UI libraries — icons are inline SVGs (`src/components/icons.jsx`)

## Pages

| Route        | What it does                                                                 |
| ------------ | ---------------------------------------------------------------------------- |
| `/`          | Home / landing with links to every tool                                      |
| `/interview` | AI mock interview: 5 core CS + 2 DSA questions, scored one by one            |
| `/resume`    | Upload a resume PDF → ATS-style score, section breakdown, fixes; JD matching |
| `/mcq`       | Generate MCQs by subject (OOPS/OS/CN/DBMS), difficulty and count             |
| `/notes`     | Notes library (placeholder) + admin upload panel (placeholder)              |
| `/sheets`    | External DSA sheet links (Striver, NeetCode, etc.)                           |

> Notes downloads and admin upload are **placeholder UI** — there is no notes
> backend yet. Wire `src/pages/Notes.jsx` `handlePublish` and the download
> buttons to your endpoint when it exists.

## Getting started

```bash
npm install
cp .env.example .env      # then edit VITE_API_PROXY to point at your backend
npm run dev               # http://localhost:5173
```

## Backend integration (this is the important part)

The frontend never hardcodes a backend origin. Every request goes through
`src/api/client.js` and hits a same-origin **`/api`** prefix.

- **In dev**, `vite.config.js` proxies `/api` → `VITE_API_PROXY`
  (default `http://localhost:8000`).
- **In prod**, serve the built frontend behind the same domain as your backend,
  or set `VITE_API_BASE` to an absolute URL at build time.

### Moving to a Django gateway

Two files control everything:

1. `src/api/client.js` — `API_BASE` (defaults to `/api`).
2. `src/api/endpoints.js` — every path, in one object.

If Django proxies the AI services under `/api/ai/...`, nothing changes. If your
paths differ, edit `endpoints.js` only — no component touches a URL directly.

### Endpoints the frontend calls

Interview (`routers/interview.py`)

- `POST /ai/interview/start` — `{ user_name, difficulty, num_subjective, num_dsa }`
- `POST /ai/interview/answer` — `{ session_id, answer }`

MCQ (`routers/mcq.py`)

- `POST /ai/mcq/generate` — `{ topic, subtopic, count, difficulty }`

Resume (`resume.py`)

- `POST /ai/resume/analyze-pdf` — multipart: `file`, `target_role`, `target_companies`
- `POST /ai/resume/pdf-to-json` — multipart: `file`
- `POST /ai/resume/ats-score` — `{ resume_text, job_description }`

> The two AI services run as separate FastAPI apps (interview+MCQ, and resume).
> Put them behind one gateway/origin (Django, or an Nginx/`vite` proxy) so the
> frontend's single `/api` prefix reaches both. If you must keep them on
> separate origins during dev, split `API_BASE` per module in `endpoints.js`.

### CORS

The interview/MCQ service reads `ALLOWED_ORIGINS`. Add your frontend origin
(e.g. `http://localhost:5173`) there, or route through the same-origin proxy
(recommended — then CORS is a non-issue).

## Design notes

- Fonts: **Space Grotesk** (display), **Inter** (body), **JetBrains Mono** (code/scores).
- Theme persists in `localStorage`; respects `prefers-color-scheme` on first load.
- Recurring motifs: the `// section` monospaced eyebrow and the score ring.

## Project structure

```
src/
  api/            # client + one wrapper per service (single integration point)
  components/     # Navbar, Layout, icons, shared UI (ScoreRing, Alert, ...)
  context/        # ThemeContext
  data/           # subjects, sheets, notes (static config)
  pages/          # one file per route
```
