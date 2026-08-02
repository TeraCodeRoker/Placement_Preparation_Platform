# PrepStack — MECE Atomic Roadmap (Phase 1)

> Mandatory artifact per MASTER_PROMPT §12.2. Decomposes `docs/BLUEPRINT.md`
> into **M**utually **E**xclusive, **C**ollectively **E**xhaustive atomic tasks
> that together implement 100 % of §§3–11 + §12. Executed **one task per turn**
> in dependency order (§12.3). Status column updated as tasks complete.

**Per-task fields (§12.2):** each task specifies **Dep** (dependencies),
**Deliv** (deliverables), **Files** (created `＋` / modified `~` / deleted `－`),
**Validate** (how correctness is checked), **Done** (objective done criteria),
**Tests** (tests that must exist/pass), **Commit** (Conventional Commits msg),
**Risks** (common failure points), **Verify** (exact end-to-end confirmation).

**Confirmed decisions:** Neon Postgres · build-deploy-ready + user deploys ·
modular monolith · Judge0 primary · Monaco lazy · JSX+JSDoc. (See Blueprint.)

**Status legend:** ☐ not started · ◐ in progress · ☑ done

---

## Phase 1 — Repo / monorepo restructuring

### T1 · Monorepo skeleton + git init + asset extraction ☑
- **Dep:** none
- **Deliv:** fresh git repo; `backend/` + `frontend/` + `docs/` layout; assets extracted (no vendored deps); root `.gitignore`, `README.md` stub, `LICENSE`.
- **Files:** ＋`.gitignore` ＋`README.md` ＋`frontend/**` (from `interview-prep-frontend`, minus `node_modules`) ＋`backend/app_legacy_ref/**` (Service A+B source, reference only, removed by T23) ＋`docs/**` (already present).
- **Validate:** `git status` clean-ish; `ls backend frontend docs`; no `node_modules`/`venv`/`.env` tracked; the leaked source key does not appear in any tracked file (grep for its full value returns empty).
- **Done:** repo initialized on `main`; assets in place; no secret committed.
- **Tests:** n/a (structural) — a `scripts/check_no_secrets.sh` grep asserted in CI later.
- **Commit:** `chore: scaffold monorepo and import existing frontend/backend assets`
- **Risks:** accidentally committing `.env`/venv/node_modules; path typos (`ai_serivce`).
- **Verify:** clone-free `git ls-files | grep -E "node_modules|venv|\.env$"` returns nothing; `docs/BLUEPRINT.md` present.

### T2 · Backend layered package + FastAPI app factory + /health ☑
- **Dep:** T1
- **Deliv:** `backend/app/` layered dirs with `__init__.py`; `create_app()` factory; `/health`; `pyproject.toml`/`requirements.txt` (pinned); `uvicorn` entrypoint; Ruff config.
- **Files:** ＋`backend/app/{api/v1,services,repositories,models,schemas,core,integrations/gemini/prompts,integrations/execution,db,tests}/__init__.py` ＋`backend/app/main.py` ＋`backend/app/api/v1/health.py` ＋`backend/pyproject.toml` ＋`backend/requirements.txt` ＋`backend/README.md`
- **Validate:** `uvicorn app.main:app` boots; `GET /health` → 200 `{"status":"healthy"}`; `ruff check .` clean.
- **Done:** app boots with zero routers beyond health; layout matches Blueprint §5.2.
- **Tests:** `tests/test_health.py` (TestClient asserts 200 + body).
- **Commit:** `feat(core): FastAPI app factory, layered package skeleton, health endpoint`
- **Risks:** import cycles; missing `__init__`; unpinned deps.
- **Verify:** run server, `curl /health`; `pytest tests/test_health.py` green.

### T3 · Frontend relocation sanity build ☑
- **Dep:** T1
- **Deliv:** frontend installs and builds unchanged in new location; dev proxy documented.
- **Files:** ~`frontend/.env.example` ~`frontend/README.md`
- **Validate:** `npm ci && npm run build` succeeds; `npm run dev` serves.
- **Done:** production build emits `dist/` with no errors; existing pages render.
- **Tests:** n/a yet (Vitest added T27).
- **Commit:** `chore(frontend): verify build in monorepo layout`
- **Risks:** lockfile drift; node version mismatch.
- **Verify:** open dev server, confirm Home/Interview/Resume/MCQ pages load.

---

## Phase 2 — Config & environment plumbing

### T4 · Typed settings + secrets strategy ☑
- **Dep:** T2
- **Deliv:** `core/config.py` (`pydantic-settings`), `Settings` (DB URL, GEMINI_API_KEY/MODEL, ALLOWED_ORIGINS, JWT secrets, execution provider/keys, rate limits, admin bootstrap email, TTLs); committed `.env.example` (placeholders only).
- **Files:** ＋`backend/app/core/config.py` ＋`backend/.env.example` ~`backend/app/main.py`
- **Validate:** app fails fast with clear error if required secret missing; `get_settings()` cached.
- **Done:** every config value read from env; no hardcoded model/keys/origins anywhere.
- **Tests:** `tests/test_config.py` (missing required var raises; defaults applied).
- **Commit:** `feat(core): typed settings via pydantic-settings and .env.example`
- **Risks:** committing real secrets; missing `GEMINI_MODEL` default (`gemini-2.5-flash`).
- **Verify:** unset a required var → startup raises; set all → boots.

### T5 · Structured JSON logging + request-id correlation ☑
- **Dep:** T2
- **Deliv:** `core/logging.py` (structlog or stdlib JSON), request-id middleware propagated to logs, redaction defaults (no raw resume/answer text).
- **Files:** ＋`backend/app/core/logging.py` ＋`backend/app/core/middleware.py` ~`backend/app/main.py`
- **Validate:** each request logs one structured line with `request_id`, method, path, status, latency.
- **Done:** logs are JSON; correlation id present; secrets/PII not logged.
- **Tests:** `tests/test_logging.py` (asserts request_id present, resume text absent).
- **Commit:** `feat(core): structured JSON logging with request-id correlation`
- **Risks:** logging full bodies; double-logging.
- **Verify:** hit `/health`, inspect stdout JSON has request_id + latency.

### T6 · Exception hierarchy + error envelope handler ☑
- **Dep:** T2
- **Deliv:** `core/exceptions.py` (`AppError` base + `NotFound/Validation/RateLimitExceeded/Gemini*/Execution*`), global handlers mapping to `{"error":{code,message,details}}` (no raw strings leak).
- **Files:** ＋`backend/app/core/exceptions.py` ＋`backend/app/core/error_handlers.py` ~`backend/app/main.py`
- **Validate:** raising each error → correct HTTP + envelope; unhandled → generic 500 envelope (no stack to client).
- **Done:** consistent error envelope for all handled errors.
- **Tests:** `tests/test_errors.py` (each error type → status + envelope shape).
- **Commit:** `feat(core): internal exception hierarchy and error-envelope handlers`
- **Risks:** leaking exception text; inconsistent envelope.
- **Verify:** temporary debug route raising each error returns mapped status + envelope.

---

## Phase 3 — Persistence layer & migrations

### T7 · Async DB engine/session + DI ☑
- **Dep:** T4
- **Deliv:** `db/session.py` (async engine `asyncpg`, `AsyncSession` factory), `db/base.py` (DeclarativeBase), `get_db` FastAPI dependency; test SQLite config seam.
- **Files:** ＋`backend/app/db/session.py` ＋`backend/app/db/base.py` ~`backend/app/core/config.py`
- **Validate:** engine connects to Postgres (and to SQLite in tests); `get_db` yields/closes cleanly.
- **Done:** DB session injectable; no blocking calls.
- **Tests:** `tests/test_db.py` (session opens/closes against SQLite).
- **Commit:** `feat(db): async SQLAlchemy engine, session factory, get_db dependency`
- **Risks:** sync driver in async path; session leaks; asyncpg vs psycopg URL scheme.
- **Verify:** test connects; `/health/detailed` (T later) reports DB up.

### T8 · ORM models (all aggregates) ☑
- **Dep:** T7
- **Deliv:** all models from Blueprint ER: `users, guest_sessions, refresh_tokens, interview_sessions, interview_results, mcq_sets, mcq_questions, mcq_attempts, resume_analyses, oa_problems, oa_submissions, notes` with FKs + `ON DELETE CASCADE`.
- **Files:** ＋`backend/app/models/*.py` ~`backend/app/models/__init__.py`
- **Validate:** `Base.metadata.create_all` builds schema on SQLite without error; relationships load.
- **Done:** models match ER; cascade set on user-owned rows.
- **Tests:** `tests/test_models.py` (create user+session+result, cascade delete removes children).
- **Commit:** `feat(models): ORM aggregates for users, interview, mcq, resume, oa, notes`
- **Risks:** wrong cascade; UUID type portability (SQLite vs PG); nullable owner columns.
- **Verify:** insert graph, delete user, assert children gone.

### T9 · Alembic setup + initial migration ☑
- **Dep:** T8
- **Deliv:** Alembic (sync engine) configured; autogenerated + reviewed initial migration; upgrade/downgrade work.
- **Files:** ＋`backend/alembic.ini` ＋`backend/migrations/env.py` ＋`backend/migrations/versions/0001_initial.py`
- **Validate:** `alembic upgrade head` then `downgrade base` clean on a scratch PG/SQLite.
- **Done:** committed migration reproduces the full schema.
- **Tests:** `tests/test_migrations.py` (upgrade head produces expected tables).
- **Commit:** `feat(db): Alembic migrations with reviewed initial schema`
- **Risks:** autogen misses cascades/indexes; async/sync engine mismatch in env.py.
- **Verify:** fresh DB `alembic upgrade head` → all tables present.

### T10 · Repository layer + tests ☑
- **Dep:** T8
- **Deliv:** `repositories/base.py` (generic CRUD) + one repo per aggregate; the only layer touching the session; `limit/offset` list helpers.
- **Files:** ＋`backend/app/repositories/*.py`
- **Validate:** each repo CRUD + list pagination works against test DB.
- **Done:** services never import Session directly; repos cover all aggregates.
- **Tests:** `tests/repositories/test_*.py` (CRUD + pagination + cascade helpers) — behavior-asserting.
- **Commit:** `feat(repositories): repository pattern per aggregate with pagination`
- **Risks:** N+1 loads; leaking ORM objects across session boundary.
- **Verify:** repo tests green; a service can persist+read via repo only.

---

## Phase 4 — Auth

### T11 · Password hashing + JWT + refresh-token model ☑
- **Dep:** T7,T4
- **Deliv:** `core/security.py` (argon2 via passlib; access-JWT create/verify; refresh token issue/hash/rotate/revoke using `refresh_tokens`).
- **Files:** ＋`backend/app/core/security.py` ＋`backend/app/services/token_service.py`
- **Validate:** hash+verify round-trip; access token expiry enforced; refresh rotation invalidates old.
- **Done:** short-lived access (15 min) + rotating DB-backed refresh.
- **Tests:** `tests/test_security.py` (hash verify; expired token rejected; rotated refresh revokes prior).
- **Commit:** `feat(auth): argon2 hashing, JWT access tokens, rotating refresh tokens`
- **Risks:** weak alg/secret; not hashing refresh at rest; clock skew.
- **Verify:** unit tests cover expiry + rotation + revoke.

### T12 · Auth service + endpoints + cookies + CSRF ☑ (claim endpoint deferred to T13, where the auth guard lives)
- **Dep:** T11,T10,T6
- **Deliv:** `/auth/register|login|refresh|logout|guest|claim`; httpOnly `Secure` `SameSite=Lax` refresh cookie scoped to `/api/v1/auth`; CSRF via custom-header/double-submit on state-changing routes; admin-bootstrap on register.
- **Files:** ＋`backend/app/services/auth_service.py` ＋`backend/app/api/v1/auth.py` ＋`backend/app/schemas/auth.py`
- **Validate:** register→login sets cookie + returns access; refresh rotates; logout revokes; guest issues token; claim re-parents rows in 1 txn.
- **Done:** full auth flow incl guest-upgrade works.
- **Tests:** `tests/api/test_auth.py` (register/login/refresh/logout/guest/claim; wrong-CSRF rejected; duplicate email 409).
- **Commit:** `feat(auth): register/login/refresh/logout/guest/claim with secure cookies + CSRF`
- **Risks:** cookie attributes wrong for same-origin proxy; CSRF gap; claim txn partial failure.
- **Verify:** TestClient runs full flow; claim moves guest interview/OA rows to user id.

### T13 · Auth guards + admin bootstrap ☑ (also hosts the /claim endpoint moved from T12)
- **Dep:** T12
- **Deliv:** `Depends` guards: `current_user`, `current_admin`, `optional_identity` (user-or-guest-or-anon); admin seeded by `ADMIN_BOOTSTRAP_EMAIL` at first register.
- **Files:** ＋`backend/app/core/deps.py` ~`backend/app/services/auth_service.py`
- **Validate:** protected route rejects anon 401; admin route rejects non-admin 403; guest allowed on AI routes.
- **Done:** guards reusable across routers; no hardcoded admin creds.
- **Tests:** `tests/test_guards.py` (401/403/guest-allowed matrix).
- **Commit:** `feat(auth): Depends-based auth guards and env-driven admin bootstrap`
- **Risks:** guest path leaking into protected routes; admin gate bypass.
- **Verify:** matrix test green.

### T14 · users/me + account-deletion cascade ☑
- **Dep:** T13,T10
- **Deliv:** `GET /users/me`; `DELETE /users/me` cascading to resumes/analyses/interview/OA/mcq history (§7/§9.1 PII path).
- **Files:** ＋`backend/app/api/v1/users.py` ＋`backend/app/services/user_service.py` ＋`backend/app/schemas/user.py`
- **Validate:** delete removes user + all owned rows in one txn; second call 404.
- **Done:** working PII deletion cascade.
- **Tests:** `tests/api/test_users.py` (profile; delete cascades; unauth 401).
- **Commit:** `feat(users): profile endpoint and cascading account deletion (PII)`
- **Risks:** orphaned rows; cascade missing an aggregate.
- **Verify:** seed a full user graph, delete, assert every child table empty for that user.

---

## Phase 5 — Gemini integration layer (incl. Service A SDK migration)

### T15 · Gemini client singleton (modern SDK, async) ☑
- **Dep:** T4
- **Deliv:** `integrations/gemini/client.py` — single `genai.Client` via lifespan/DI; async `generate_content`; model from `GEMINI_MODEL`. **Removes legacy `google-generativeai` entirely.**
- **Files:** ＋`backend/app/integrations/gemini/client.py` ~`backend/app/main.py` ~`backend/requirements.txt` (add `google-genai`, ensure no `google-generativeai`)
- **Validate:** client constructed once; calls are awaited; model name env-driven.
- **Done:** one SDK in tree; no per-request client; no blocking call in async.
- **Tests:** `tests/integrations/test_gemini_client.py` (client is singleton; call awaited — mocked).
- **Commit:** `feat(gemini): shared async google-genai client (drops legacy SDK)`
- **Risks:** reintroducing blocking call; two SDKs coexisting; leaking key in logs.
- **Verify:** `pip show google-generativeai` absent; mocked call awaited.

### T16 · Reliability + error taxonomy ☑
- **Dep:** T15,T6
- **Deliv:** per-call timeout, bounded retry (exp backoff + jitter) for transient only, circuit breaker/failure-rate guard; map failures → `GeminiUnavailable/EmptyResponse/Malformed/SchemaViolation/RateLimitExceeded` → HTTP 503/502/502/502/429 (§10.6).
- **Files:** ＋`backend/app/integrations/gemini/reliability.py` ＋`backend/app/integrations/gemini/errors.py`
- **Validate:** timeout→503; malformed→502; breaker opens after threshold; 4xx/safety don't retry.
- **Done:** taxonomy table fully implemented; no bare 500 on any mapped failure.
- **Tests (5 mandatory failure modes start here):** `tests/integrations/test_gemini_reliability.py` (timeout, malformed JSON, empty/blocked, schema-violation, breaker-open).
- **Commit:** `feat(gemini): timeouts, jittered retry, circuit breaker, error taxonomy`
- **Risks:** retrying non-idempotent/expensive calls; breaker never resets.
- **Verify:** failure-mode tests assert exact status + envelope.

### T17 · Prompt templates + response schema + defensive parse/adapter ☑
- **Dep:** T15
- **Deliv:** `prompts/*.py` pure functions per use case; `response_mime_type=application/json` + `response_schema` where supported; defensive parse → Pydantic-validate adapter; free-text exception documented (code-review prose).
- **Files:** ＋`backend/app/integrations/gemini/prompts/{interview,mcq,resume,oa}.py` ＋`backend/app/integrations/gemini/adapters.py` ＋`backend/app/integrations/gemini/service.py` (typed helpers `generate_json(model_schema,...)`)
- **Validate:** each template interpolates required fields, leaks no internal instructions; parse rejects invalid JSON → `GeminiSchemaViolationError`.
- **Done:** all AI calls routed through this helper; no inline prompts in routers.
- **Tests:** `tests/integrations/test_prompts.py` (fields interpolated, no leakage) + `test_adapters.py` (valid parses, invalid raises).
- **Commit:** `feat(gemini): versioned prompt templates, schema-constrained JSON, defensive adapter`
- **Risks:** prompt injection via user data; schema drift; over-forcing JSON on prose call.
- **Verify:** template unit tests green; a service call returns validated model.

---

## Phase 6 — Interview module port + upgrade

### T18 · Interview service (port + persist + idempotency) ☑
- **Dep:** T17,T10,T13
- **Deliv:** move `question_bank.py`; `InterviewService` (plan factory, generate/evaluate via Gemini helper), persistence replacing `SESSIONS`; `/answer` idempotency via `answer_idempotency_key`; single-txn write+advance.
- **Files:** ＋`backend/app/services/interview_service.py` ＋`backend/app/data/question_bank.py` ＋`backend/app/schemas/interview.py`
- **Validate:** start→persisted session; answer→result persisted + index advanced atomically; retry same idem key doesn't double-count.
- **Done:** no in-memory session state; separation (syllabus=truth, Gemini=phrasing) preserved.
- **Tests:** `tests/services/test_interview_service.py` (plan shape; evaluate parse; idempotent retry; txn rollback on Gemini failure mid-write).
- **Commit:** `feat(interview): DB-backed sessions, idempotent answers, Gemini-driven Q&A`
- **Risks:** double-scoring on retry; losing "subjective first" ordering; partial write.
- **Verify:** service test simulates timeout retry → single result row.

### T19 · Interview routers + history + code-review ☑
- **Dep:** T18
- **Deliv:** `/ai/interview/start|answer|session/{id}|history|code-review`; envelopes; `limit/offset` history; free-text code-review kept.
- **Files:** ＋`backend/app/api/v1/interview.py`
- **Validate:** end-to-end start→answer×N→summary via TestClient (Gemini mocked); history paginates; guest + user both work.
- **Done:** endpoints match Blueprint API surface + envelopes.
- **Tests:** `tests/api/test_interview.py` (full lifecycle; history; code-review; 404 unknown session).
- **Commit:** `feat(interview): interview + code-review routers with paginated history`
- **Risks:** envelope inconsistency; guest vs user history leakage.
- **Verify:** lifecycle test green; history shows only caller's sessions.

---

## Phase 7 — MCQ module port + upgrade + caching

### T20 · MCQ service + caching + persistence ☑
- **Dep:** T17,T10
- **Deliv:** `McqService` on shared Gemini helper; **cache-first** on `(topic,subtopic,count,difficulty)` via `mcq_sets/mcq_questions` with TTL + documented invalidation; daily-challenge cached per day/topic.
- **Files:** ＋`backend/app/services/mcq_service.py` ＋`backend/app/schemas/mcq.py`
- **Validate:** identical request within TTL served from DB (no Gemini call); expired/forced → regenerate; questions validated against schema.
- **Done:** production-grade cache (not pass-through); invalidation policy documented.
- **Tests:** `tests/services/test_mcq_service.py` (cache miss calls Gemini once; cache hit calls zero; TTL expiry regenerates).
- **Commit:** `feat(mcq): schema-validated generation with persistent TTL cache`
- **Risks:** cache key omitting a param; stale-forever cache; unvalidated options.
- **Verify:** assert Gemini mock call-count 1 then 0 on repeat.

### T21 · MCQ routers + attempt + history ☑
- **Dep:** T20
- **Deliv:** `/ai/mcq/generate|daily-challenge|attempt|history`; attempt records score; history paginated.
- **Files:** ＋`backend/app/api/v1/mcq.py`
- **Validate:** generate returns validated set; attempt persists correct/total; history paginates.
- **Done:** endpoints + envelopes complete.
- **Tests:** `tests/api/test_mcq.py` (generate cached; attempt persists; history).
- **Commit:** `feat(mcq): MCQ routers with attempt recording and history`
- **Risks:** attempt without a set; count cap ignored.
- **Verify:** generate→attempt→history round-trip green.

---

## Phase 8 — Resume module port

### T22 · Resume service (port + upload validation + persist) ☑
- **Dep:** T17,T10
- **Deliv:** port all 6 resume endpoints onto shared Gemini helper; upload validation (magic-byte sniff, ≤10 MB, content-length, scanned-PDF rejection); input truncation cap; persist analyses.
- **Files:** ＋`backend/app/services/resume_service.py` ＋`backend/app/schemas/resume.py` ＋`backend/app/core/uploads.py`
- **Validate:** analyze/ats/improve/placement/pdf-to-json/analyze-pdf all return validated JSON; oversized/non-PDF/scanned rejected with clear errors.
- **Done:** parity with Service B + hardening + persistence.
- **Tests:** `tests/services/test_resume_service.py` (each endpoint mocked; bad upload rejected; truncation applied).
- **Commit:** `feat(resume): port resume analysis onto shared Gemini layer with upload hardening`
- **Risks:** MIME spoofing; huge input cost; losing `improve-bullet` echo-original fix.
- **Verify:** upload a fake `.pdf` (wrong magic) → 400; valid text → analysis.

### T23 · Resume routers + history; remove legacy reference code ☑
- **Dep:** T22
- **Deliv:** `/ai/resume/*` routers + `/history`; delete `backend/app_legacy_ref/**` (source now fully ported); confirm no legacy SDK anywhere.
- **Files:** ＋`backend/app/api/v1/resume.py` －`backend/app_legacy_ref/**`
- **Validate:** endpoints work; `git grep google.generativeai` empty; both former Gemini call sites now use shared layer.
- **Done:** single Gemini integration; legacy tree gone.
- **Tests:** `tests/api/test_resume.py` (analyze/ats/pdf paths; history).
- **Commit:** `feat(resume): resume routers + history; drop legacy service source`
- **Risks:** dangling imports to removed tree.
- **Verify:** full backend test suite green after deletion; grep clean.

---

## Phase 9 — Code-execution integration layer

### T24 · Provider ABC + Judge0 + Piston stub + factory ☑
- **Dep:** T4,T6
- **Deliv:** `CodeExecutionProvider(ABC).execute(language,source,stdin,timeout)->ExecutionResult`; `Judge0ExecutionProvider` (RapidAPI free, async httpx, language map, batch/stdin); `PistonExecutionProvider` gated on key; factory via `EXECUTION_PROVIDER`; size/timeout ceilings pre-forward.
- **Files:** ＋`backend/app/integrations/execution/{base,judge0,piston,factory,errors}.py` ＋`backend/app/schemas/execution.py`
- **Validate:** Judge0 request built correctly (mocked httpx); size/timeout enforced before send; unreachable→`ExecutionUnavailableError`.
- **Done:** Strategy pattern seam; provider swappable by config; never executes in-process.
- **Tests:** `tests/integrations/test_execution.py` (mocked run pass/fail/timeout/unreachable; oversized rejected pre-send).
- **Commit:** `feat(execution): CodeExecutionProvider strategy with Judge0 (Piston seam)`
- **Risks:** language id mapping; provider rate-limit; leaking key.
- **Verify:** mocked provider returns per-case stdout/time; unreachable path raises mapped error.

---

## Phase 10 — OA module (new)

### T25 · OA service (problem/run/submit, grading, degraded, txn) ☑
- **Dep:** T24,T17,T10
- **Deliv:** `OAService`: generate+persist problem (visible+hidden tests, Gemini-authored, validated); `run` (visible only, no score); `submit` (all tests → pass-rate; Gemini qualitative review; store `oa_submissions` in 1 txn; **degraded AI-review-only** when provider down); grading semantics (trim-trailing exact match, float tolerance, per-case + wall-clock timeout, size cap, partial credit surfaced separately from AI score).
- **Files:** ＋`backend/app/services/oa_service.py` ＋`backend/app/schemas/oa.py`
- **Validate:** run hides hidden cases; submit computes pass_count/total honestly + separate ai_review; provider-down → degraded mode + labeled flag; write atomic.
- **Done:** honest non-conflated objective + subjective results; degraded mode works.
- **Tests:** `tests/services/test_oa_service.py` (grading pass/partial/fail; hidden not exposed on run; degraded mode; float tolerance; txn rollback).
- **Commit:** `feat(oa): OA grading orchestrator with real execution + AI review and degraded mode`
- **Risks:** hidden-case leakage; conflating scores; float compare; regenerating hidden tests on refresh.
- **Verify:** submit with 6/8 passing returns `pass_count=6,total=8` + separate `ai_review`; kill provider mock → degraded banner flag set.

### T26 · OA routers + history + aggressive rate limit ☑ (rate limit wired in T32 with slowapi)
- **Dep:** T25,T13
- **Deliv:** `/ai/oa/problem|run|submit|submission/{id}`; stricter EXEC rate-limit; sanitized/length-capped stderr/stdout; auth for non-guest history.
- **Files:** ＋`backend/app/api/v1/oa.py`
- **Validate:** end-to-end problem→run→submit (execution + Gemini mocked); submission retrievable; run/submit rate-limited harder.
- **Done:** OA is a first-class `/ai/oa/*` module wired per API surface.
- **Tests:** `tests/api/test_oa.py` (lifecycle; degraded; rate-limit 429; history auth).
- **Commit:** `feat(oa): OA routers with strict rate limiting and submission history`
- **Risks:** unsanitized provider output; rate-limit too loose.
- **Verify:** lifecycle test green; exceed limit → 429 + Retry-After.

---

## Phase 11 — Frontend: Auth UI

### T27 · API layer extension + AuthContext ☑
- **Dep:** T12 (contract)
- **Deliv:** extend `endpoints.js` (auth/oa/history/notes) via `client.js` only; access-token in-memory + auto-refresh-on-401 in `client.js`; `api/auth.js`; `AuthContext` (Context + reducer) + Vitest/RTL setup.
- **Files:** ~`frontend/src/api/endpoints.js` ~`frontend/src/api/client.js` ＋`frontend/src/api/auth.js` ＋`frontend/src/context/AuthContext.jsx` ＋`frontend/vitest.config.js` ＋`frontend/src/test/setup.js` ~`frontend/package.json`
- **Validate:** 401 triggers one refresh then retry; no raw `fetch` in components; context exposes user/login/logout/guest.
- **Done:** single-integration-point intact + extended; auth state centralized.
- **Tests:** `src/api/client.test.js` (refresh-on-401), `context/AuthContext.test.jsx` (reducer transitions) — API mocked at client boundary.
- **Commit:** `feat(frontend): auth API layer, in-memory token, refresh, AuthContext`
- **Risks:** infinite refresh loop; bypassing client.js.
- **Verify:** Vitest green; grep components for `fetch(` returns none.

### T28 · Auth pages + guest + cold-start UX + upgrade ☑
- **Dep:** T27
- **Deliv:** Login/Register pages (labeled inputs, keyboard-operable, contrast in both themes), guest "just click Start" path, Navbar auth state, "waking up the server" state on slow `/health`, guest→registered upgrade prompt after a completed attempt (calls `/auth/claim`).
- **Files:** ＋`frontend/src/pages/{Login,Register}.jsx` ＋`frontend/src/components/AuthMenu.jsx` ＋`frontend/src/components/WakingServer.jsx` ~`frontend/src/App.jsx` ~`frontend/src/components/Navbar.jsx`
- **Validate:** register/login round-trip against mocked API; guest completes flow; upgrade attaches activity.
- **Done:** auth UX complete, accessible, on existing design system.
- **Tests:** `src/pages/Login.test.jsx`, upgrade-flow test.
- **Commit:** `feat(frontend): login/register, guest mode, cold-start UX, guest-upgrade`
- **Risks:** second design language; a11y regressions.
- **Verify:** Vitest green; manual keyboard-only pass of forms.

---

## Phase 12 — Frontend: OA / compiler UI

### T29 · OA page with lazy Monaco ☑
- **Dep:** T27,T26 (contract)
- **Deliv:** `/oa` route; `@monaco-editor/react` **lazy-loaded** (`React.lazy` + dynamic import, own chunk); language selector; Run (visible) / Submit (graded) with per-case pass/fail, complexity + ai_review (separate from pass rate), degraded banner; perf budget (Monaco not in main chunk); a11y.
- **Files:** ＋`frontend/src/pages/OA.jsx` ＋`frontend/src/components/CodeEditor.jsx` ＋`frontend/src/api/oa.js` ~`frontend/src/App.jsx` ~`frontend/src/api/endpoints.js`
- **Validate:** `vite build` shows Monaco in a **separate** chunk; run shows only visible results; submit shows honest dual signals + degraded banner when flagged.
- **Done:** OA experience wired; main bundle not bloated.
- **Tests:** `src/pages/OA.test.jsx` (run/submit render; degraded banner; editor lazy boundary), build-artifact chunk assertion.
- **Commit:** `feat(frontend): OA page with lazy-loaded Monaco editor and run/submit`
- **Risks:** Monaco in main bundle; conflating scores in UI.
- **Verify:** inspect `dist/assets` — separate monaco chunk; Vitest green.

---

## Phase 13 — Frontend: history + Notes admin wiring

### T30 · History views + progress.js → API migration ☑
- **Dep:** T27,T19,T21 (contracts)
- **Deliv:** migrate `lib/progress.js` reads/writes to API (interview/MCQ/OA history) while keeping localStorage fallback for guests; history/dashboard views.
- **Files:** ~`frontend/src/lib/progress.js` ＋`frontend/src/pages/History.jsx` ~`frontend/src/pages/Home.jsx`
- **Validate:** logged-in history from API; guest history still local; dashboard renders both.
- **Done:** persistence seam moved to backend per design.
- **Tests:** `src/lib/progress.test.js` (API path vs guest local path).
- **Commit:** `feat(frontend): server-backed history via progress.js migration`
- **Risks:** breaking existing dashboard shape; double-counting.
- **Verify:** Vitest green; dashboard shows server history when logged in.

### T31 · Notes admin panel + public notes wiring ☑
- **Dep:** T27,T13 (admin), backend notes routes (add here if not present)
- **Deliv:** backend `/admin/notes` + public `/notes` routes/service/repo (if not yet); frontend admin upload panel (admin-gated) + public Notes page reads backend instead of static `data/notes.js`.
- **Files:** ＋`backend/app/api/v1/admin_notes.py` ＋`backend/app/services/notes_service.py` ~`frontend/src/pages/Notes.jsx` ＋`frontend/src/pages/AdminNotes.jsx`
- **Validate:** admin uploads → appears after approve; non-admin can't reach panel; public page lists approved notes.
- **Done:** `/notes` placeholder finally backed by real backend + admin role.
- **Tests:** `tests/api/test_notes.py` (admin CRUD, non-admin 403); `src/pages/AdminNotes.test.jsx`.
- **Commit:** `feat(notes): admin upload panel and backend-backed public notes`
- **Risks:** admin gate bypass; unapproved notes shown publicly.
- **Verify:** non-admin blocked; approved note visible publicly.

---

## Phase 14 — Security hardening pass (cross-cutting verification)

### T32 · Security sweep + rate limiting + CORS + injection audit ☑
- **Dep:** all module tasks
- **Deliv:** verify/enforce: CORS explicit origins (no `*`); `slowapi` rate limits active on every AI + EXEC endpoint (per-IP + per-user); upload validation audited; prompt-injection mitigations (delimiting, instruction-reiteration, schema enforcement, inert user content) present at each call site; deps pinned; `.env.example` current; key-rotation procedure doc.
- **Files:** ＋`backend/app/core/rate_limit.py` ~routers (decorators) ＋`docs/ADRS/016-security.md` ~`backend/.env.example`
- **Validate:** hitting an AI endpoint past limit → 429; CORS preflight from unlisted origin blocked; injection probe stays inert.
- **Done:** §9.1 checklist fully satisfied (this phase *verifies*, doesn't defer).
- **Tests:** `tests/test_security.py` (429 on limit; CORS rejects; injection probe returns schema-valid, no instruction execution).
- **Commit:** `feat(security): rate limiting, CORS lockdown, prompt-injection mitigations`
- **Risks:** limiter missing on a route; CORS regex too broad.
- **Verify:** automated rate-limit + CORS tests green; manual injection probe.

---

## Phase 15 — Test suite completion & coverage gate

### T33 · Coverage gate + contract tests + E2E ☑ (E2E: documented omit + manual checklist per §9.2)
- **Dep:** all backend/frontend tasks
- **Deliv:** coverage config; fill *meaningful* gaps to ≥80 % on `services/` (no padding); contract tests (responses match Pydantic models); confirm no test hits real network; minimal Playwright (interview + OA journeys), on-demand not per-PR; manual-verification checklist.
- **Files:** ＋`backend/pytest.ini`/`.coveragerc` ＋`backend/tests/contract/*` ＋`e2e/*.spec.ts` ＋`docs/TESTING.md`
- **Validate:** `pytest --cov` ≥80 % services/; contract tests green; Playwright journeys pass locally.
- **Done:** §9.2 satisfied incl the 5 failure-mode tests (already at module level) verified holistically.
- **Tests:** the suite itself.
- **Commit:** `test: coverage gate, contract tests, and Playwright E2E for key journeys`
- **Risks:** coverage padding; flaky E2E; hidden real network call.
- **Verify:** CI-equivalent local run: coverage ≥ bar, `-p no:cacheprovider` offline run green.

---

## Phase 16 — CI/CD

### T34 · GitHub Actions pipeline ☑
- **Dep:** T33
- **Deliv:** PR workflow: Ruff, mypy (strict on services/integrations/schemas), ESLint + `tsc --checkJs`, backend+frontend tests, build check, coverage gate (blocking), **gitleaks** (blocking), `pip-audit`/`npm audit` (reported-only), import-linter DIP check; deploy step doc (Render auto-deploy on merge to main); rollback note.
- **Files:** ＋`.github/workflows/ci.yml` ＋`.github/workflows/e2e-nightly.yml` ＋`.importlinter` ＋`docs/ADRS/017-cicd.md`
- **Validate:** workflow passes on a clean PR; a planted secret fails gitleaks; a coverage drop fails.
- **Done:** §9.3 CI satisfied with named tools + stated strictness.
- **Tests:** CI run itself (green on main).
- **Commit:** `ci: lint, type-check, tests, coverage gate, gitleaks, audits`
- **Risks:** flaky/slow CI; over-strict blocking on advisories.
- **Verify:** open a scratch PR → all required checks green; secret-planted branch → red.

---

## Phase 17 — Render deployment manifest & live deploy (handoff)

### T35 · render.yaml + runbooks + deploy handoff ☑ (live deploy is user-performed)
- **Dep:** T34
- **Deliv:** committed `render.yaml` (web service native buildpack + static site with `/api/*` rewrite → backend; `/health` health check; env groups); `/health/detailed` (DB + Gemini/exec reachability); cold-start UX verified; **step-by-step deploy runbook** (Neon provision, env vars, rotated keys, Judge0 key, first deploy, Alembic migrate on deploy) for the user to execute.
- **Files:** ＋`render.yaml` ＋`backend/app/api/v1/health.py` (detailed) ＋`docs/DEPLOYMENT.md` ＋`docs/ADRS/018-deploy.md`
- **Validate:** `render.yaml` validates; local `/health/detailed` reports subsystems; rewrite config correct.
- **Done:** everything deploy-ready; only user-account steps remain (documented).
- **Tests:** `tests/test_health_detailed.py`.
- **Commit:** `feat(deploy): render.yaml blueprint, detailed health, deployment runbook`
- **Risks:** rewrite misconfig breaking same-origin cookies; missing migrate step.
- **Verify:** user follows runbook → `/run` and `/submit` execute real code on the live provider (final DoD item, user-performed).

---

## Phase 18 — Documentation & interview-prep companion

### T36 · Docs finalization + INTERVIEW_PREP.md ☑
- **Dep:** all prior (INTERVIEW_PREP.md accumulated per-module along the way, §12.5)
- **Deliv:** `README.md` (setup/architecture/deploy), `docs/ADRS/*.md` (one per ADR), `docs/INTERVIEW_PREP.md` (traceable §12.4 output incl. dedicated MCQ + OA-compiler + why-external-execution write-ups), `docs/ROADMAP.md` status updated, OpenAPI `/docs` verified.
- **Files:** ~`README.md` ＋`docs/ADRS/001..018-*.md` ＋`docs/INTERVIEW_PREP.md` ~`docs/ROADMAP.md`
- **Validate:** every ADR referenced in Blueprint has a file; INTERVIEW_PREP traceable to real code.
- **Done:** §12.6 deliverables present and non-trivial.
- **Tests:** doc-lint/link check (optional).
- **Commit:** `docs: README, ADRs, and traceable interview-prep companion`
- **Risks:** generic filler; stale roadmap status.
- **Verify:** open `/docs`; spot-check INTERVIEW_PREP answers cite actual files.

---

## Phase 19 — Final polish / demo-data seeding

### T37 · Seed script + DoD verification ☑
- **Dep:** all
- **Deliv:** idempotent seed (demo user, admin, sample approved notes, one cached MCQ set, one OA problem); final walk of the §13 DoD checklist with evidence.
- **Files:** ＋`backend/scripts/seed.py` ＋`docs/DOD_CHECKLIST.md`
- **Validate:** seed runs against a fresh DB; demo flows work end-to-end.
- **Done:** every §13 box either checked with evidence or explicitly marked user-action (live deploy/keys).
- **Tests:** `tests/test_seed.py` (seed idempotent).
- **Commit:** `chore: demo-data seed script and Definition-of-Done verification`
- **Risks:** non-idempotent seed; DoD gaps.
- **Verify:** fresh DB → seed → demo login → interview/OA/MCQ/resume/notes all functional.

---

## Coverage map (Collectively Exhaustive check)

| Master-prompt section | Tasks |
|---|---|
| §3 Deploy constraint | T2,T12(rewrite),T29(lazy),T35 |
| §4 Target scope | all |
| §5 Architecture/layering/patterns | T2,T10,T13,T17,T24 |
| §6 API design (versioning, envelopes, pagination, idempotency) | T6,T18,T19,T21,T23,T26 |
| §7 Persistence + migrations + txn + PII | T7–T10,T14,T25 |
| §8 Auth (registered+guest+admin, token ADR) | T11–T14 |
| §9.1 Security | T5,T22,T26,T32 |
| §9.2 Testing (incl 5 failure modes, E2E) | T16 + each module's tests + T33 |
| §9.3 DevOps | T34,T35 |
| §9.4 Observability | T5,T35 |
| §9.5 Frontend engineering | T27–T31 |
| §10 Gemini integration | T15–T17 (+ all consumers) |
| §11 Execution engine | T24–T26 |
| §12 Process/docs/interview-fuel | T36 (+ per-module §12.4 explanations each turn) |
| §13 DoD | T37 |

## MECE note
**Mutually Exclusive:** each task owns a distinct responsibility/file set; shared
files (`endpoints.js`, `client.js`, `main.py`, `App.jsx`) are touched additively
in dependency order to avoid overlap. **Collectively Exhaustive:** the coverage
map shows every binding section maps to ≥1 task. The two late "sweep" phases
(T32, T33) *verify* cross-cutting properties; the actual security/testing work
lives in each module task (§12.2 clarification).
