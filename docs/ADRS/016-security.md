# ADR-016 — Security hardening

**Status:** Accepted · **Relates to:** §9.1

## Context
The rebuilt system exposes expensive, abusable surfaces (Gemini-backed and
code-execution endpoints) and handles PII (resumes, transcripts). Service B's
original `allow_origins=["*"]` must not survive into production.

## Decisions

### CORS — explicit origins only
`CORSMiddleware` is locked to `ALLOWED_ORIGINS` (comma-separated env, default
`http://localhost:5173`); **never `*`**. Credentials are allowed (cookies), so a
wildcard would be both insecure and rejected by browsers. A test asserts an
allowed origin is echoed and a foreign origin is not.

### Rate limiting — path-classified, per-identity, in-memory
A custom sliding-window limiter (`core/rate_limit.py`) applied as middleware —
chosen over `slowapi` to classify by path centrally without decorating ~25
endpoints and threading `Request` through each. Classes: **EXEC** (`/ai/oa/run`,
`/ai/oa/submit` — strictest, the most externally-billable-adjacent surface),
**AI** (other `/ai/*`), **AUTH**, **STD**. Keyed by authenticated user → guest
token → client IP. Exceeding a limit returns `429` with `Retry-After` in the
standard error envelope.
- **Trade-off:** in-memory means it resets on restart and isn't shared across
  workers (accepted free-tier trade-off). **Upgrade path:** a Redis backend for
  shared, restart-durable counters. Toggle via `RATE_LIMIT_ENABLED` (off in
  tests so the suite's many requests don't self-throttle).

### Prompt-injection mitigation
User-supplied content (answers, code, resume text, JD) is wrapped in explicit
begin/end delimiters with an injection-guard instruction, and outputs are
schema-constrained (`response_schema` + defensive parse). Full prevention is
impossible; the blast radius is bounded — a smuggled instruction stays inert
data, and a bad generation fails validation (502) rather than exfiltrating or
changing the task. Tests assert the fencing.

### Upload hardening
Resume PDFs: magic-byte sniff (`%PDF`), 10 MB cap, scanned-PDF rejection, and a
20k-char input truncation before any prompt (ADR/§9.1). Tested per branch.

### Secrets & dependency hygiene
- Secrets only via env vars; `.env` git-ignored; `.env.example` placeholders
  kept current. The one leaked source key was flagged for rotation and never
  committed (a `git grep` for its value is part of T1's validation).
- Dependencies pinned. `pip-audit` / `npm audit` run in CI as **reported-only**
  (advisory, non-blocking); `gitleaks` runs as a **blocking** gate (ADR-013/T34).

## Key-rotation runbook
1. **Gemini:** create a new key at aistudio.google.com → set `GEMINI_API_KEY` in
   Render's env group → redeploy. Revoke the old key. No code change.
2. **Code execution:** nothing to rotate by default — the Paiza runner uses the
   public `guest` key (ADR-020). If you switch to Judge0, regenerate the RapidAPI
   key → set `JUDGE0_API_KEY` → redeploy.
3. **JWT secret:** set a new strong `JWT_SECRET` → redeploy. Existing access
   tokens (≤15 min TTL) expire quickly; refresh tokens are DB-backed and
   re-issued on next login, so rotation invalidates outstanding sessions safely.
4. **DB URL:** provision the new database, migrate data, set `DATABASE_URL`,
   redeploy (see `docs/DEPLOYMENT.md`).
