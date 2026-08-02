# PrepStack

A placement-preparation platform — AI mock interviews, an **OA coding compiler**
that runs real code, MCQ practice, resume analysis, and admin-curated notes —
engineered as an **interview showcase** and deployable entirely on the Render
free tier.

## Features
- **Mock Interview** — core-CS + Striver A2Z DSA questions phrased and scored by
  Gemini, with idempotent answers and per-session history.
- **OA Compiler** — generate a problem, solve it in a Monaco editor, **Run**
  against visible tests and **Submit** for a real pass-rate (executed on a free,
  keyless sandbox) plus a separate AI review, with an AI-review-only degraded mode.
- **MCQ Practice** — cache-first generation (identical requests served from
  Postgres within a TTL), attempts + history.
- **Resume Analysis** — analyze / ATS-score / bullet-improve / placement-check /
  PDF extraction, with hardened uploads.
- **Notes** — admin-uploaded, approval-gated public library.
- **Auth** — registered + guest + admin, with guest→account upgrade.

## Architecture
A **plain Django** backend (per-context apps + a services layer over the Django
ORM) + a Vite/React static frontend, backed by managed Postgres. Every AI task
goes through one shared Gemini integration layer (timeout, retry, circuit breaker,
schema-validated output); code execution is delegated to an external sandbox
behind a Strategy-pattern abstraction (never in-process) — the default is the
**free, keyless** Paiza runner ([ADR-020](docs/ADRS/020-free-code-execution.md)),
with Piston/Judge0 as one-env-var swaps. Django's worker model means the
external calls are synchronous (Gunicorn) — the idiomatic translation of the
original async design (see [ADR-019](docs/ADRS/019-django-overhaul.md)). The whole
`/api/v1` contract is preserved, so the frontend is framework-agnostic.

```
backend/   Django (prepstack/ project + apps/{accounts,interview,mcq,resume,oa,notes,core,integrations})
frontend/  React 18 + Vite 5 + Tailwind 3 — single API seam: src/api/client.js + endpoints.js
docs/      BLUEPRINT · ROADMAP · ADRS/ · INTERVIEW_PREP · TESTING · DEPLOYMENT
```

## Local development
```bash
# Backend  (Python 3.12)
cd backend
python -m venv .venv && .venv/Scripts/activate     # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                                # fill values; never commit .env
python manage.py migrate                            # against your DATABASE_URL (sqlite by default)
python manage.py runserver 8000
pytest                                              # Django tests, all external calls mocked

# Frontend  (Node 20)
cd frontend
npm ci
npm run dev                                         # proxies /api + /health -> VITE_API_PROXY
npm test                                            # Vitest + React Testing Library
```

## Quality gates (CI — `.github/workflows/ci.yml`)
Ruff · mypy (pure logic layers) · `manage.py check` · migrations-up-to-date ·
pytest · Vitest + build · **gitleaks** (blocking) · pip-audit / npm audit
(reported-only). See [ADR-017](docs/ADRS/017-cicd.md).

## Deployment
Infra-as-code in [`render.yaml`](render.yaml); step-by-step handoff in
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Deploying requires **your** accounts
and keys — a rotated **Gemini** key (free tier) and a **Neon/Render Postgres**
URL. That's it: code execution needs no key and nothing here requires payment.
The app fails fast at boot if a required prod secret is missing.

## Docs
- [Blueprint](docs/BLUEPRINT.md) — architecture, ADRs, ER, API surface, sequences
- [Roadmap](docs/ROADMAP.md) — the MECE task plan + completion status
- [Interview-Prep companion](docs/INTERVIEW_PREP.md) — per-module design Q&A
- [Testing](docs/TESTING.md) · [Deployment](docs/DEPLOYMENT.md) · [ADR log](docs/ADRS/README.md)

## Security
Secrets only via environment variables; `.env` is git-ignored and `.env.example`
holds placeholders. CORS is locked to configured origins; AI/execution endpoints
are rate-limited. See [ADR-016](docs/ADRS/016-security.md).

## License
MIT — see [`LICENSE`](LICENSE).
