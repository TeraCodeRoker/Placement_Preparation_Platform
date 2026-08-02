# Architecture Decision Log

Discrete records for every ADR. **001–015** were made in Phase 0 (full context —
alternatives considered, rejection rationale, free-tier consequences — in
[`docs/BLUEPRINT.md`](../BLUEPRINT.md) §2); each is recorded below. **016–018**
were added during the build and have standalone files:
[016-security](016-security.md) · [017-cicd](017-cicd.md) · [018-deploy](018-deploy.md).

---

### ADR-001 — Topology: modular monolith
One FastAPI app (`api → services → repositories → models`) on a single Render web
service + static site. **Rejected:** 2-services+gateway (3 cold starts, no
scaling benefit); split-by-concern (artificial seam). **Consequence:** one cold
start; a single DB txn for the OA submit write.

### ADR-002 — Persistence: managed Postgres, repo-swappable
Neon always-free Postgres via `DATABASE_URL` (async SQLAlchemy + asyncpg +
Alembic); Render Postgres the drop-in alternative. **Rejected:** SQLite-on-disk
(disqualified — lost on spin-down; tests only); Render Postgres alone (30-day
expiry → renewal runbook). **Consequence:** one-line DB swap; terms re-verified
at build.

### ADR-003 — Guest mode: persisted-under-token, claim on signup
Guest activity persisted under an anonymous `guest_token` (7-day TTL); claimed
onto the account at register/login. **Rejected:** no-persistence (breaks upgrade
UX); forced signup (breaks zero-friction). **Consequence:** TTL purge bounds row
growth.

### ADR-004 — Token storage: same-origin proxy + httpOnly refresh + in-memory access
Static-site rewrite → same origin; refresh token in `httpOnly; Secure;
SameSite=Lax` cookie; access token in memory (15 min); double-submit CSRF.
**Rejected:** `localStorage` (XSS-readable); cross-site `SameSite=None` (weaker,
documented fallback). **Consequence:** reload needs silent refresh; refresh
tokens rotate + DB-revocable.

### ADR-005 — Code execution via a provider Strategy *(default amended by ADR-020)*
`CodeExecutionProvider` ABC with swappable strategies, selected by
`EXECUTION_PROVIDER`. **Rejected:** self-hosted Docker sandbox (no privileged
containers; in-process untrusted code = risk).
**Consequence:** execution delegated, never in-process; degraded = AI-review-only.
Judge0 was the original default; **[ADR-020](020-free-code-execution.md) moved the
default to the free, keyless Paiza runner** after Judge0's tier became paid.

### ADR-006 — Prompts as versioned pure functions
`integrations/gemini/prompts/*.py`, one pure function per use case, unit-tested.
**Rejected:** inline f-strings in routers (legacy — unreviewable/untestable).
**Consequence:** prompts diffable in review.

### ADR-007 — Sync/async boundaries
All outbound I/O async (Gemini `client.aio`, execution `httpx`, DB asyncpg); no
blocking call in `async def`. **Refinement:** Alembic uses its async env (reusing
asyncpg/aiosqlite) instead of a second sync driver. **Consequence:** event loop
never blocked; one driver stack.

### ADR-008 — DI mechanism: FastAPI `Depends`
Repositories + Gemini/execution providers injected via `Depends`, overridden in
tests. **Rejected:** manual constructor wiring (boilerplate, no override
ergonomics). **Consequence:** services unit-testable with providers mocked.

### ADR-009 — Pagination: limit/offset
History endpoints use `limit`/`offset` (capped 100). **Rejected:** cursor
pagination (complexity unjustified at this scale). **Consequence:** trivial to
implement/test.

### ADR-010 — PII / data retention
Retained tied to the owning account; guest PII purged at TTL; `DELETE /users/me`
cascades to all owned rows. **Consequence:** logs never store raw text; cascade
tested.

### ADR-011 — OA editor: Monaco, code-split
`@monaco-editor/react`, lazy-loaded into its own chunk (verified absent from the
main bundle). **Rejected:** CodeMirror (smaller, less IDE-fidelity).
**Consequence:** heavy editor doesn't compound cold start.

### ADR-012 — Build: native buildpacks, not Docker
Render native Python + Node buildpacks. **Rejected:** Dockerfile (no system dep
needs it). **Consequence:** faster builds, smaller images, lower cold start.

### ADR-013 — CI gates + strictness
Blocking: Ruff, mypy (strict on business layers), import-linter DIP, pytest +
80% services coverage, Vitest + build, gitleaks. Reported-only: pip-audit / npm
audit. Full detail: [017-cicd](017-cicd.md).

### ADR-014 — Frontend typing: keep JSX + JSDoc
Keep `.jsx`; enforce via ESLint + `tsc --checkJs` on new modules. **Rejected:**
full TS migration (risky rewrite of preserved assets).

### ADR-015 — E2E testing: documented omit
Omit per-PR Playwright; substitute a manual checklist ([TESTING.md](../TESTING.md)).
**Rationale:** meaningful E2E needs the full live stack — costly in free CI
minutes/quota — for little gain over the existing RTL + integration tests. Seam
left open for a nightly suite against a deployed preview.
