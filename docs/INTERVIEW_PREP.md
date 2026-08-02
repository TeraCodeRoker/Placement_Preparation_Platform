# PrepStack — Interview Prep Companion

> Cumulative §12.4 write-ups, one per completed module, organized by topic
> (§12.5). Every answer is traceable to code actually in this repo — not generic
> textbook filler. Grows as the build proceeds.

**Topics:** [Architecture](#architecture) · [Backend](#backend) · [Persistence](#persistence) · [AI Integration](#ai-integration) · [Security](#security) · [Testing](#testing) · [DevOps](#devops) · [System Design](#system-design)

---

## Architecture

### Module 1 — Project foundation & modular-monolith layout (T1–T3)

**What was built:** a single git monorepo (`backend/` + `frontend/` + `docs/`);
a FastAPI **application-factory** (`create_app()`) with a layered package
(`api → services → repositories → models`, plus `core`, `schemas`,
`integrations`, `db`); pinned dependency manifests; a `/health` liveness
endpoint; and a first passing test.

**1. Why this design.** A modular monolith matches the actual constraints:
single team, one Render free Web Service (512 MB, spins down after 15 min idle),
and an interview-showcase goal. One deployable = one cold start and one env
surface, while hard internal seams still demonstrate layered architecture. The
application-factory pattern keeps all wiring in one place and lets tests build
isolated app instances.

**2. Principles/patterns demonstrated (named precisely).**
- **Application Factory pattern** (`create_app()` in `app/main.py`).
- **Layered architecture** + **Dependency Inversion (SOLID "D")**: routers
  depend inward on services, never on `google.genai`/execution SDKs (to be
  CI-enforced by an import-linter in T34).
- **Separation of Concerns**: `api/` = HTTP only; business logic lives in
  `services/`.
- **Single Responsibility (SOLID "S")** at the package level: one directory per
  concern.
- **Convention over configuration**: plain `backend/`+`frontend/` workspace with
  independent toolchains (Blueprint §7 monorepo note).

**3. Credible alternative not chosen.** Microservices (separate interview, mcq,
resume, oa services). Rejected: they solve independent-deploy/team-scaling
problems this project doesn't have, and would add 2–3 cold starts, 3 env
surfaces, and a distributed-transaction problem for the OA submit write — pure
cost on a free tier. "Why a modular monolith over microservices here" is itself
a strong prepared answer.

**4. Trade-offs accepted.** One process means no independent scaling of a hot
module; a bug can take down the whole app; the 512 MB ceiling is shared. The
in-repo build imports the two legacy services as `backend/app_legacy_ref/`
(reference only, deleted at T23) so the migration diff stays reviewable — extra
transient weight for auditability.

**5. Future improvements.** Extract a hot module (e.g., execution proxy) into its
own service *if* real traffic justifies it; add a container image for
reproducibility once a system dependency demands it; workspace tooling (uv/pnpm)
if the package count grows.

**6–7. Interview Q&A (grounded in this code).**

- **Q: Why a modular monolith instead of microservices?**
  A: The forces here are a single team, a free-tier host that spins down after
  15 min, and a cross-module transactional write (OA submit persists a
  submission + updates history counters atomically). Microservices would turn
  that into a saga and add multiple cold starts for no scaling benefit. The
  monolith keeps it one DB transaction and one cold start, while the enforced
  `api→services→repositories` layering still gives clean, testable seams.

- **Q: What is the application-factory pattern and why use it?**
  A: `create_app()` constructs and wires the FastAPI instance instead of a
  module-level singleton built at import time. It centralizes wiring and lets
  tests spin up isolated apps (and later override dependencies) without import
  side effects. `app = create_app()` at the bottom is what `uvicorn app.main:app`
  targets.

- **Q: How do you keep the layering from rotting?**
  A: Direction is inward-only: routers import services, services import
  repositories/integrations. It's not just documented — T34 adds an
  import-linter contract (and a unit test) that fails CI if `api/` imports a
  provider SDK, making Dependency Inversion a checked property.

- **Q: How do you manage secrets and why pin dependencies?**
  A: Secrets come only from env vars; `.env` is git-ignored and `.env.example`
  holds placeholders. The one real key found in the source archives was flagged
  for rotation and never copied in (a `git grep` for its value is part of T1's
  validation). Dependencies are pinned so builds are reproducible and a
  transitive bump can't silently change behavior between local and Render.

**8. Senior follow-ups.**

- **Q: At 10× traffic, what breaks first, and what do you do?**
  A: The single process saturates CPU/memory first — most likely the
  Gemini/execution-bound request handlers holding connections during slow
  provider calls. First mitigations: raise worker count (still one service),
  add the already-planned circuit breaker + rate limits, and cache MCQ/daily
  generation (T20). If a specific module stays hot, the seam is already clean
  enough to extract just that module into its own service without touching
  callers — which is the payoff of enforcing the layering now.

- **Q: The free instance spins down after 15 min — how do you keep the demo from
  looking broken?**
  A: A `/health` endpoint exists from first boot; the frontend polls it and
  shows a "waking up the server" state (T28) so the ~30–60 s cold start reads as
  intentional, not a hang. Durable data lives in managed Postgres (not the
  ephemeral disk), so a spin-down loses nothing.

---

## Backend

### Module 2 — Config, observability & error handling (T4–T6)

**What was built:** typed settings (`app/core/config.py`) with a fail-fast
production check; structured JSON logging with request-id correlation
(`logging.py` + `middleware.py`); an internal exception hierarchy mapped to a
consistent error envelope (`exceptions.py` + `error_handlers.py`).

**1. Why.** Configuration, observability, and error shaping are cross-cutting —
building them before any feature means every later module inherits typed config,
correlated logs, and a uniform error contract for free, instead of retrofitting.

**2. Principles/patterns (named).** Twelve-Factor **config-in-environment**;
**fail-fast** (`assert_production_ready()` refuses to boot a prod deploy missing
real secrets); **single source of truth** (one `Settings`, cached via
`lru_cache`); **cross-cutting concern via middleware/decorator** (request-id
context); **uniform interface** for errors (envelope + exception hierarchy so
raw strings never leak — an information-disclosure control).

**3. Alternative not chosen.** Reading `os.environ` ad hoc at call sites.
Rejected: no validation, no typing, no single place to see the config surface,
and no fail-fast — misconfig would surface as a random 500 mid-request instead
of at boot.

**4. Trade-offs.** Dev-safe defaults mean a developer *can* run with an insecure
JWT secret locally; that's deliberate (zero-friction dev) and bounded by the
prod gate. structlog's `PrintLoggerFactory` writes to stdout — perfect for
Render's log capture, but there's no built-in log shipping/retention on the free
tier (accepted; a future sink is a config change).

**5. Future improvements.** Sampling/log levels per route; ship logs to an
external aggregator; add OpenTelemetry spans reusing the same request-id.

**6–7. Interview Q&A (grounded).**

- **Q: How is configuration managed and validated?**
  A: A single `pydantic-settings` `Settings` class reads every value from env
  (Render env groups in prod, git-ignored `.env` locally), with types and
  defaults. `get_settings()` is `lru_cache`d so it's parsed once. CORS origins
  accept a comma-separated string via a `NoDecode` + before-validator (avoiding
  pydantic-settings' default JSON decoding of list env vars).

- **Q: What does "fail fast" mean here and why?**
  A: `assert_production_ready()` runs in `create_app()`; if `APP_ENV=prod` but
  the JWT secret is the dev default/too short, or the Gemini key is unset, or
  `DATABASE_URL` is still SQLite, it raises at startup. A bad prod deploy dies
  immediately with a clear message instead of serving broken requests — and on
  Render a failed deploy keeps the previous good one live.

- **Q: How would you debug a specific failed request in production?**
  A: Every request gets a `request_id` (inbound `X-Request-ID` or a fresh UUID)
  bound into structlog contextvars, echoed back as a response header, and
  attached to every log line for that request including a `request_completed`
  line with status + latency. Give me the id from the client and I can grep one
  correlated trace. Bodies/PII are deliberately never logged.

- **Q: How do you stop internal errors leaking to clients?**
  A: All errors flow through registered handlers into
  `{"error":{code,message,details}}`. Known `AppError`s carry a safe message;
  anything unhandled becomes a generic 500 while the real exception is logged
  server-side. A test asserts a raised secret marker never appears in the
  response body.

**8. Senior follow-up.**

- **Q: `lru_cache` on settings — how do you change config without a redeploy, and
  what are the risks?**
  A: You don't, by design: config is immutable per process, which makes behavior
  reproducible and thread-safe. Changing env on Render triggers a redeploy,
  which is the intended control point. The risk is tests polluting the cache —
  handled by constructing `Settings(_env_file=None, ...)` directly in tests
  rather than going through the cached accessor.

---

## Persistence

### Module 3 — Persistence layer & migrations (T7–T10)

**What was built:** async SQLAlchemy 2.0 engine + session (`asyncpg` prod /
`aiosqlite` test) with a `get_db` dependency; twelve ORM aggregates with portable
UUID/JSON types and correct FK actions; Alembic async migrations (upgrade/
downgrade verified); a generic `BaseRepository` + one repository per aggregate.

**1. Why.** Replacing the legacy in-memory `SESSIONS` dict with durable Postgres
is the single most important correctness fix: on Render's free tier the dict is
lost on every 15-min idle spin-down. The repository seam means "swap the DB" is a
one-line `DATABASE_URL` change (Neon ↔ Render Postgres) — a stated interview
point.

**2. Principles/patterns (named).** **Repository pattern** (persistence isolated
behind repos; services never see `Session`); **Dependency Inversion** (services
depend on the repo abstraction); **Unit of Work** (repos `flush`, the service
`commit`s — so multi-aggregate writes are one transaction); **portability via
type abstraction** (`sa.Uuid`/`sa.JSON` render per-dialect); **schema-as-code**
(Alembic migrations are reviewable, reversible artifacts).

**3. Alternative not chosen.** SQLite-on-local-disk. Rejected as *disqualifying*:
Render's ephemeral filesystem loses it on spin-down/restart/redeploy, violating
the DoD "a restart does not lose history." SQLite is used only for the fast,
isolated test DB.

**4. Trade-offs.** Async SQLAlchemy needs `greenlet` and careful "no blocking in
the event loop" discipline. `sa.Uuid` stores as `CHAR(32)` on SQLite vs native
`UUID` on Postgres — fine because we never write dialect-specific SQL. Alembic
runs an *async* env (refined from ADR-007's "sync engine") to avoid adding a
second DB driver.

**6–7. Interview Q&A (grounded).**

- **Q: Why can't you just use SQLite on the server?**
  A: Render free web dirs are ephemeral — a SQLite file dies on the 15-minute
  idle spin-down, every restart, and every redeploy. The DoD requires history to
  survive those, so durable data lives in managed Postgres (Neon). SQLite is only
  the test database, where its speed and isolation are an asset.

- **Q: How do you keep persistence swappable?**
  A: Every DB access goes through a repository; nothing above the repo layer
  imports `Session` or SQLAlchemy. The engine is built from `DATABASE_URL`, so
  moving Neon → Render Postgres (or vice-versa) is one env change with no code
  edit. Both are Postgres, so the same `asyncpg` driver and migrations apply.

- **Q: A single OA submit writes a submission and updates counters — how do you
  keep that atomic?**
  A: Repositories `flush` but never `commit`; the transaction boundary is the
  service method, which does the writes and one `commit`. A failure mid-way rolls
  the whole unit back — no orphaned score. `get_db` also rolls back on any
  exception before closing.

- **Q: How do you evolve the schema safely in production?**
  A: Alembic migrations are committed, reviewed, and reversible. The initial
  migration was autogenerated then read line-by-line to confirm FK cascade/
  set-null actions and the idempotency unique constraint. `upgrade head` and
  `downgrade base` are both tested (CLI + pytest). On deploy, `alembic upgrade
  head` runs before the app serves traffic.

- **Q: How does the account-deletion cascade actually work across databases?**
  A: FK constraints declare `ON DELETE CASCADE` for user/guest-owned rows and
  `ON DELETE SET NULL` where history must survive (an attempt's cached set, a
  note's uploader). Postgres enforces this natively; for SQLite tests we enable
  `PRAGMA foreign_keys=ON` per connection so the same cascade is exercised — a
  test deletes a user and asserts the sessions/results are gone.

**8. Senior follow-up.**

- **Q: `sa.Uuid` is `CHAR(32)` on SQLite but native `UUID` on Postgres — could a
  test pass while prod breaks?**
  A: Possible in principle, which is why the migration is reviewed to use the
  same portable SQLAlchemy types the models declare (not dialect-specific DDL),
  the CI runs migrations, and the deploy runbook runs `alembic upgrade head`
  against the real Postgres. The remaining prod-only surface (native UUID, JSONB
  behavior) is small and covered by the integration tests hitting a Postgres in a
  future CI matrix if needed.

---

## Security

### Module 4 — Authentication & authorization (T11–T14)

**What was built:** argon2 password hashing; short-lived JWT access tokens +
DB-backed rotating refresh tokens; `/auth` endpoints (register/login/refresh/
logout/guest/claim) with an httpOnly refresh cookie, a double-submit CSRF cookie,
and env-driven admin bootstrap; `Depends` guards (`get_current_user`,
`get_current_admin`, `get_optional_identity`); and `users/me` with a cascading
account-deletion path.

**1. Why.** The legacy system had no auth at all. This adds registered users +
guests + admin while keeping the "just click Start" zero-friction demo, and puts
the token-storage decision on defensible footing (a standard first interview
question).

**2. Principles/patterns (named).** **Stateless auth** (JWT access tokens);
**token rotation** (each refresh revokes its predecessor — limits replay);
**defense in depth** (httpOnly cookie stops XSS token theft; double-submit CSRF
stops cross-site abuse; SameSite=Lax adds a layer); **least privilege**
(role-gated admin); **secure-by-default** (`Secure` cookies outside local; only a
SHA-256 of the refresh token is stored, so a DB leak isn't replayable); **DIP**
(guards/services injected, unit-testable).

**3. Alternative not chosen.** Server-side sessions in a store. Rejected on a
free-tier, cold-starting, ephemeral-disk host: a session store is another moving
part, and stateless JWTs validate without a round-trip — which matters when the
instance just cold-started. Trade-off: JWTs can't be instantly revoked, so
access tokens are short-lived (15 min) and refresh tokens are revocable in the DB.

**4. Trade-offs.** Access-token in memory means a full page reload needs a silent
refresh (handled in T27). CSRF via double-submit needs the SPA to echo the cookie
in a header. A 15-min access token is a deliberate revocation-latency vs
round-trip trade-off.

**6–7. Interview Q&A (grounded).**

- **Q: Where do you store the tokens and why?** (the classic)
  A: The refresh token lives in an httpOnly, Secure, SameSite=Lax cookie scoped
  to `/api/v1/auth` — unreadable by JS, so XSS can't exfiltrate it. The access
  token is short-lived and held in memory (React state), never `localStorage`
  (which any injected script can read). To make the Lax cookie work, the frontend
  is served same-origin via a Render static-site rewrite, so there's no
  cross-site cookie problem.

- **Q: If refresh is a cookie, what about CSRF?**
  A: A companion non-httpOnly `csrf` cookie is set; the SPA reads it and echoes
  it in an `X-CSRF-Token` header on state-changing cookie routes (refresh/logout),
  and the server compares the two (double-submit). SameSite=Lax is a second layer.
  Bearer-authenticated routes (claim, delete) are inherently CSRF-safe since a
  browser won't auto-attach an `Authorization` header cross-site. A test asserts
  refresh without the header returns 403.

- **Q: How do refresh tokens rotate, and what does that buy you?**
  A: On refresh, the presented token is marked revoked and a new one issued; only
  SHA-256 hashes are stored. If a refresh token is stolen and used, the legitimate
  client's next refresh (or the attacker's) invalidates the other — and a leaked
  DB can't replay a raw token. A test asserts the rotated-away token can't be
  reused.

- **Q: How does guest mode coexist with auth, and how does upgrade work?**
  A: `get_optional_identity` resolves a user (Bearer), a guest (`X-Guest-Token`),
  or anonymous, and never raises — so AI endpoints work with zero signup. Guest
  activity is keyed by an opaque guest token with a TTL. On `/auth/claim`, a bulk
  `UPDATE ... SET user_id=?, guest_id=NULL` re-parents the guest's interview/OA/
  MCQ/resume rows to the new account in one transaction.

- **Q: How do you handle admin without hardcoding credentials?**
  A: Exactly one bootstrap mechanism: whoever registers with
  `ADMIN_BOOTSTRAP_EMAIL` (an env var) gets the admin role; everyone else is a
  user. No admin password is committed. A test verifies only the configured email
  is elevated.

**8. Senior follow-up.**

- **Q: A user clicks "delete my account" — walk me through what's guaranteed.**
  A: `DELETE /users/me` deletes the user row inside a transaction; FK
  `ON DELETE CASCADE` removes every owned row (resumes, analyses, interview/OA/MCQ
  history, refresh tokens), while `SET NULL` preserves shared artifacts (an
  uploaded note's authorship). It's the concrete data-retention deletion path
  from the PII ADR, and a test asserts the owned rows are gone. Their access token
  still decodes for ≤15 min but resolves to a missing user → 401, so it's
  effectively dead immediately.

---

## AI Integration

### Module 5 — Gemini integration layer (T15–T17)

**What was built:** one shared async `google-genai` client (legacy SDK dropped);
a `GeminiService` with timeout + jittered retry + circuit breaker + the §10.6
error taxonomy + defensive JSON parse + Pydantic validation; and centralized,
versioned prompt templates with prompt-injection mitigations. Every AI feature
in the app runs through this one layer.

**1. Why.** Two things an interviewer probes: "how do you integrate an external
AI API robustly?" and "how do you manage prompts like code?" Centralizing gives
one place for reliability, cost control, and prompt review, and enforces the
router→service→integration dependency direction (routers never touch the SDK).

**2. Principles/patterns (named).** **Adapter** (SDK response → validated internal
schema); **Facade** (`GeminiService` hides SDK + reliability + parsing);
**Circuit Breaker** and **Retry with backoff+jitter** (resilience patterns);
**Strategy-ready** (services depend on a `SupportsGenerate` Protocol, so the
provider is swappable/mockable); **fail-safe defaults** (every failure maps to a
typed error, never a bare 500).

**3. Alternative not chosen.** Let each router call `google.genai` directly (the
legacy Service A style). Rejected: duplicated boilerplate, no shared reliability
or caching, untestable without network, and prompts scattered as inline
f-strings — exactly the smells this refactor removes.

**4. Trade-offs.** The circuit breaker is in-memory, so it resets on restart and
isn't shared across workers (accepted free-tier trade-off; Redis is the upgrade).
`response_schema` constrains generation but we still defensively parse — belt and
braces, at a little extra code.

**6–7. Interview Q&A (grounded).**

- **Q: How do you get reliable structured output from an LLM?**
  A: Two layers. At generation time we set `response_mime_type=application/json`
  plus a `response_schema` (a Pydantic model) so the model is constrained. On the
  way out we never trust it: strip fences, parse defensively (direct parse, then
  slice to the outermost object/array), then `model_validate`. A parse failure is
  `GeminiMalformedResponse` (502); a validation failure is `GeminiSchemaViolation`
  (502) — never passed through to the UI.

- **Q: What happens when Gemini is slow or down?**
  A: Each call has a timeout; transient failures retry with exponential backoff +
  jitter (bounded); and a circuit breaker opens after N consecutive failures so
  we fast-fail with a clear "temporarily unavailable" (503) instead of piling up
  requests on a 512 MB instance. Five failure-mode tests assert timeout→503,
  malformed→502, empty→502, schema→502, and open-circuit→503.

- **Q: How do you manage prompts?**
  A: As code — versioned pure functions of typed inputs in
  `integrations/gemini/prompts/`, one per use case. They're unit-tested (fields
  interpolated, untrusted content fenced) and diffable in review, unlike inline
  f-strings.

- **Q: Users paste arbitrary resume text and code into prompts. Prompt injection?**
  A: You can't fully prevent it, so you bound the blast radius. User content is
  wrapped in explicit begin/end delimiters with an instruction to treat it as
  inert data, and the output shape is enforced server-side by the schema. A test
  smuggles "IGNORE ALL INSTRUCTIONS" into an answer and asserts it lands inside
  the data fence. Worst case, a bad generation fails validation and returns a 502
  — it can't exfiltrate data or change the task.

**8. Senior follow-up.**

- **Q: Your breaker is per-process and per-worker. At scale, what's wrong and what
  do you do?**
  A: With multiple workers each has its own breaker, so the provider can still get
  N× the intended trial traffic during an outage, and a restart forgets the open
  state. The fix is a shared store (Redis) for breaker + rate-limit state, which
  also enables cross-instance coordination. On the free tier that's out of scope,
  so I document it as the first thing I'd add when moving off free — the seam is
  already isolated in `reliability.py`, so it's a localized change.

---

## System Design

### Module 6 — Interview feature (T18–T19)

**What was built:** the mock-interview flow end-to-end — `question_bank`
(syllabus source of truth) + Gemini (phrasing/evaluation) + DB-backed sessions
replacing the in-memory `SESSIONS` dict, with an idempotent `/answer`, session
reconnect, paginated history, and free-text code review.

**1. Why.** This is the first full feature and it proves the layered stack:
router → service → {repositories, Gemini} with a clean transaction boundary. It
also fixes the legacy's biggest liability — process-local session state that a
free-tier spin-down erases.

**2. Principles/patterns (named).** **Separation of concerns** (syllabus = data,
Gemini = phrasing/scoring); **idempotency key** (safe retries); **capability vs
ownership authorization** (guest sessions are capability-based, user sessions are
private); **transaction script** owning the commit so a write is atomic.

**3. Alternative not chosen.** Generate all questions up front at start. Rejected:
it front-loads N Gemini calls (cost + latency + a slow first response against a
cold instance) for questions the user may never reach; lazy generation (one per
step) is cheaper and matches the UX.

**4. Trade-offs.** The generated question text is stored inside the session's JSON
`plan`, which needs `flag_modified` because SQLAlchemy doesn't track in-place JSON
mutation — a real gotcha. Each answer is atomic all-or-nothing, so if
next-question generation fails the answer isn't recorded and the client retries
(the idempotency key protects the *committed-but-response-lost* case).

**6–7. Interview Q&A (grounded).**

- **Q: `/answer` can be retried after a timeout. How don't you double-count?**
  A: The client sends an idempotency key per answer. Before evaluating, the
  service checks for an existing result on `(session_id, key)` (a DB unique
  constraint backs it); if present it replays the stored evaluation without
  re-calling Gemini or advancing the index. A test submits twice with the same
  key and asserts one result row, one Gemini eval, and no double-advance.

- **Q: Why store the plan as JSON instead of a questions table?**
  A: The plan is a small, session-scoped, always-read-together document — a JSON
  column keeps it in one row with no join, which fits a read-mostly reconnect
  path. Per-question *results* (the durable, queryable history) do get their own
  table. It's a deliberate document-vs-relational split by access pattern.

- **Q: How is a guest's interview secured vs a logged-in user's?**
  A: A user's session is private — the ownership guard rejects another account
  (403). A guest session is capability-based: holding the session UUID is the
  credential, which is what makes zero-signup "just click Start" work. On signup
  the guest's sessions are claimed into the account.

**8. Senior follow-up.**

- **Q: Two Gemini calls per answer (evaluate + next question) on a slow provider —
  what's the user impact and how would you improve it?**
  A: Worst case the user waits for both sequentially on top of a possible cold
  start. Mitigations already present: timeouts + breaker bound the wait, and the
  answer write is atomic. Improvements: return the evaluation immediately and
  fetch the next question in a second request (or stream), and/or prefetch the
  next question while the user reads feedback — the service seam makes either a
  localized change.

---

### Module 7 — MCQ generation + caching (T20–T21) [Gemini feature #1]

**What was built:** one of the two explicitly Gemini-driven features. Schema-
validated MCQ generation with a **production cache**: identical
`(topic, subtopic, count, difficulty)` requests within a TTL are served from
Postgres instead of re-calling Gemini; daily-challenge is cached per day+topic;
plus attempt recording and history.

**1. Why cache.** Gemini calls cost money/latency and are the abusable surface on
a free tier. Identical MCQ requests are common (a student redoing "OS, medium,
5"), so a TTL cache is the primary cost/abuse lever and a concrete "engineered
with production discipline, not a pass-through" answer.

**2. Principles/patterns (named).** **Cache-aside** (look up → miss → generate →
store); **TTL invalidation** with **eviction** (stale entries deleted, not
served); **content-addressable key** (deterministic cache key from the request
tuple); **schema-validated output** (Gemini result validated before it's cached
or returned).

**3. Alternative not chosen.** Cache forever (no TTL). Rejected: MCQs would go
stale and identical every day, and you could never refresh phrasing. A short TTL
balances cost against variety. Also rejected: an in-memory LRU — it dies on
spin-down and isn't shared across workers, whereas the DB cache survives both.

**4. Trade-offs.** Two concurrent identical misses could both insert and race on
the unique `cache_key` (rare on a single free instance; documented — the fix is
catch-and-refetch or an upsert). Evicting a stale set nulls `mcq_attempts.set_id`
rather than cascading, so history survives — a deliberate `SET NULL` choice.

**6–7. Interview Q&A (grounded).**

- **Q: Walk me through the MCQ cache.**
  A: Cache-aside. I build a deterministic key from `(topic, subtopic, count,
  difficulty)`. On request I look up `mcq_sets` by that key: if a row exists and
  is within `mcq_cache_ttl_hours`, I return its questions (zero Gemini calls); if
  it's stale I delete it and regenerate; if it's absent I generate, validate, and
  store. Tests assert the second identical request makes **zero** Gemini calls and
  that a stale entry regenerates.

- **Q: How do you invalidate?**
  A: TTL-based with eviction. There's no manual bust needed for correctness — an
  entry simply expires and the next request regenerates. Deleting the set nulls
  the attempts' `set_id` (SET NULL), so a user's score history isn't lost when a
  cached set is evicted.

- **Q: What stops a user hammering generation to run up API cost?**
  A: Three layers: the cache absorbs identical requests; `count` is capped at 20
  in the request schema; and per-IP/per-user rate limiting sits on the endpoint
  (security pass). The Gemini circuit breaker is the final backstop.

**8. Senior follow-up.**

- **Q: Two users request the same uncached set at the same instant — what happens?**
  A: Both miss, both generate, both try to insert the same `cache_key`; the second
  insert violates the unique constraint. On one free instance with low concurrency
  it's unlikely, but the correct fix is to make the write an upsert (or catch the
  IntegrityError and re-read the winner's row). I chose to document it rather than
  add locking that the free tier doesn't warrant — the unique constraint at least
  guarantees we never store duplicates.

---

### Module 8 — Resume analysis + upload hardening (T22–T23)

**What was built:** all six resume operations ported onto the shared Gemini layer
with schema-validated output and persisted analyze/ats/placement history; a
hardened PDF upload path; and the deletion of the legacy service source (both
former Gemini call sites now share one integration layer).

**1. Why.** Resumes are untrusted file uploads full of PII — the highest-risk
input surface in the app. It needs defense-in-depth on ingest and a clear PII
lifecycle, not just a happy path.

**2. Principles/patterns (named).** **Defense in depth** (size cap → magic-byte
sniff → scanned-PDF rejection → input truncation); **validate-then-act**;
**permissive-but-validated** output schemas (`extra="allow"` for deeply nested,
human-consumed blobs); **DRY consolidation** (one Gemini layer, legacy deleted).

**3. Alternative not chosen.** Trust the file extension / `Content-Type`. Rejected:
both are attacker-controlled. We sniff the `%PDF` magic bytes on the actual
payload instead.

**4. Trade-offs.** Truncating resume text at 20k chars could clip a very long CV,
but it bounds prompt cost/latency and is far safer than sending unbounded input.
Permissive schemas mean a malformed nested field is tolerated rather than 502'd —
the right call for read-only display data.

**6–7. Interview Q&A (grounded).**

- **Q: A user uploads a file to your resume endpoint. What can go wrong and how do
  you defend?**
  A: Oversized payloads (DoS) → 10 MB cap checked on the read bytes; a non-PDF or
  disguised file → magic-byte sniff (`%PDF`), not the extension; a scanned image
  PDF with no text → detected (extracted text < 50 chars) and rejected with a
  helpful 422; and unbounded text inflating prompt cost → truncated to 20k chars
  before it reaches Gemini. Each branch has a test.

- **Q: These endpoints handle PII. What's the lifecycle?**
  A: Analyses are stored tied to the owning user (or a guest with a TTL) with the
  scores JSON and verdict; logs never carry raw resume text (lengths/hashes only).
  Deletion is real: `DELETE /users/me` cascades to `resume_analyses`. Utility
  calls (bullet improvement) aren't persisted at all — no reason to keep them.

- **Q: You migrated two separate services onto one Gemini layer. How do you know
  it's actually consolidated?**
  A: The legacy source tree was deleted, a grep proves nothing imports it, and
  `google-generativeai` (the old SDK) is neither installed nor referenced — only
  `google-genai`. The 112-test suite passes after deletion, so the port is
  complete, not parallel.

**8. Senior follow-up.**

- **Q: `pdfplumber` runs untrusted PDF parsing in-process — is that a risk on a
  512 MB instance?**
  A: Yes — a malicious/huge PDF could spike memory or CPU. Mitigations present:
  the 10 MB cap bounds input, and parse errors are caught and returned as a clean
  400 rather than crashing the worker. Further hardening if it mattered: a page
  count cap and a wall-clock timeout on extraction, or moving extraction to a
  separate worker so a parser blow-up can't take down request handling.

---

### Module 9 — OA code-execution compiler (T24–T26) [Gemini feature #2]

**What was built:** the second Gemini-driven feature and the only one that runs
real code. A `CodeExecutionProvider` Strategy (Paiza default; Piston + Judge0
behind the same ABC) plus
an OA flow: generate+persist a problem, `run` against visible cases, `submit`
grades against ALL cases via the provider and combines an honest objective
pass-rate with a SEPARATE Gemini review, with an AI-review-only degraded mode.

**Why delegate execution to an external provider (the key §12.5 point).** Running
an arbitrary-language sandbox inside the 512 MB Render free web service isn't
viable — no privileged containers, tight memory, shared CPU, and executing
untrusted code in-process is a critical security risk. So execution is delegated
to a hosted sandbox; our backend is a thin, validated, rate-limited
proxy + grader. This is both a security decision (isolation) and a resource
decision (the free instance can't host safe multi-language execution).

> **The Strategy seam paid for itself (ADR-020).** Judge0's free tier became
> metered and the public Piston API went whitelist-only. Because every provider
> sits behind one ABC + a factory, migrating to the free Paiza runner was a new
> module + one env var — **zero changes to services, views, or the frontend**.
> That's the concrete answer to "why not just call the vendor SDK directly?"

**Principles/patterns (named).** **Strategy** (swappable provider); **Adapter**
(provider response → `ExecutionResult`); **Anti-corruption layer** (our schema,
not the vendor's); **graceful degradation** (provider down → AI-review-only);
**separation of signals** (objective pass-rate vs subjective AI score, never
conflated).

**Alternative not chosen.** Self-host a Docker-based runner. Rejected on the free
tier: no privileged containers, and it turns our web service into an
arbitrary-code sandbox — the exact thing you don't want one process doing.

**Trade-offs.** We depend on a third-party's uptime and rate limits (mitigated by
the degraded mode + aggressive rate limiting), and network latency per test case
(mitigated by a per-case timeout + a per-submission wall-clock ceiling).

**Interview Q&A (grounded).**

- **Q: Why not run the submitted code yourself?**
  A: Security and resources. Executing untrusted, arbitrary-language code
  in-process on a 512 MB shared instance is a sandbox-escape and DoS risk and
  isn't affordable. We delegate to Judge0's sandbox and act as a validated proxy:
  size cap + language allowlist before forwarding, per-case timeout, wall-clock
  ceiling, and we never reflect hidden-case output back.

- **Q: How is grading honest and non-gameable?**
  A: The objective score is strictly `passed/total` test cases, computed by
  comparing normalized stdout (trailing-whitespace-trimmed, float tolerance for
  numeric answers) — surfaced separately from the AI's qualitative 0-10. A test
  asserts 3/4 → `pass_count=3, final_score=75` alongside a distinct `review_score`.
  Hidden-case stdin/expected/stdout are never returned (a test checks this), so a
  candidate can't reverse-engineer them.

- **Q: The execution provider goes down mid-assessment. What does the user see?**
  A: `submit` catches `ExecutionUnavailableError`, sets `mode=ai_review_only`,
  `final_score=0`, empty test results, but still returns the Gemini review with a
  banner (frontend) that objective execution was unavailable. It never silently
  pretends tests ran — a test asserts the degraded shape.

**Senior follow-up.**

- **Q: A test case makes N sequential HTTP calls to Judge0. What's the failure and
  cost profile, and how would you harden it?**
  A: Latency stacks per case and the free provider is rate-limited, so a big
  hidden suite is slow and abusable. Guards present: per-case timeout, a
  per-submission wall-clock ceiling that short-circuits remaining cases, source
  size cap, and (T32) aggressive per-user rate limits on run/submit. Next steps
  off free tier: Judge0 batch submissions, a small concurrency pool, and caching
  identical (problem, code) submissions.

---

## Frontend

### Module 10 — Frontend: auth, cold-start UX, and the lazy OA editor (T27–T29)

**What was built:** the single API seam extended (in-memory access token, silent
refresh-on-401, guest + CSRF headers), an `AuthContext` (Context + reducer),
accessible login/register with guest-upgrade, a cold-start "waking up" banner,
and the OA page with a **lazy-loaded Monaco editor** and honest dual scoring.

**1. Why.** These are the §9.5 binding frontend decisions: token storage, state
management, code-split editor, cold-start UX, accessibility. Each was made
deliberately, not defaulted.

**2. Principles/patterns (named).** **Single integration point** (every call
through `client.js`; no raw `fetch` in components); **token-in-memory** (XSS can't
read it); **single-flight refresh** (dedupe parallel 401s); **route-level
code-splitting + `React.lazy`** for Monaco; **Context + reducer** over a heavy
store for a small surface.

**3. Alternative not chosen.** Tokens in `localStorage` + Redux. Rejected:
`localStorage` is XSS-readable (full-account blast radius), and Redux is overkill
for one user object — Context + a 3-line reducer suffices.

**4. Trade-offs.** In-memory access token means a hard reload needs a silent
refresh round-trip (handled on mount). Monaco is loaded from a CDN by
`@monaco-editor/react`'s default loader, so it isn't in the JS bundle at all —
great for bundle size, but it needs network on first editor open (acceptable;
could self-host later).

**6–7. Interview Q&A (grounded).**

- **Q: Where's the access token and how does a 401 self-heal?**
  A: In a module variable in `client.js` — never storage. On a 401, `client.js`
  calls `/auth/refresh` once (single-flight, so 10 parallel 401s trigger one
  refresh), swaps in the new access token, and retries the original request. A
  test asserts exactly one refresh and that the refresh call itself never
  recurses.

- **Q: How did you keep Monaco from bloating first paint?**
  A: The OA route is `React.lazy`, and the editor is a further lazy import, so
  Monaco's wrapper lands in its own ~16 KB chunk. A build check greps the main
  bundle and asserts "monaco" is absent — it's proven, not assumed. First paint
  ships React + the app only (~73 KB gzip).

- **Q: The backend cold-starts for ~30-60s. What does the user see?**
  A: A `WakingServer` banner: it probes `/health` on load and, if slow, shows
  "waking up the server…" so the delay reads as intentional. Combined with the
  small main bundle, a heavy frontend doesn't compound the slow first request.

- **Q: How does guest → account upgrade work on the frontend?**
  A: Guests get an anonymous token (`ensureGuest`) and use every feature. On
  register/login the client calls `/auth/claim` with that guest token, so the
  just-finished OA/interview attempts attach to the new account — the OA page
  even shows a "save my progress" prompt after a guest submission.

**8. Senior follow-up.**

- **Q: Your silent refresh is single-flight in memory. What breaks with two tabs?**
  A: Each tab has its own in-memory token and refresh promise, so both may
  refresh independently — fine because refresh tokens rotate server-side and the
  latest wins; a stale tab just refreshes again on its next 401. If I needed
  cross-tab sync I'd use a BroadcastChannel or the `storage` event to share the
  new access token, but that adds complexity the demo doesn't need.

---

## DevOps

### Module 11 — Security, CI/CD, and deployment (T32–T35)

**What was built:** CORS lockdown + a path-classified rate limiter; a CI pipeline
(lint, types, DIP contract, coverage gate, secret scan, audits); a `render.yaml`
Blueprint with same-origin proxying; and `/health/detailed`.

**1. Why.** These turn "it works on my machine" into "it's defensibly
production-ready on a free tier" — the second half of the interview.

**2. Principles/patterns (named).** **Defense in depth** (CORS + rate limits +
injection fencing + upload validation); **fail-fast config**; **IaC**
(`render.yaml`); **checked architecture** (import-linter makes DIP a gate, not a
comment); **graceful degradation** everywhere.

**6–7. Interview Q&A (grounded).**

- **Q: How do you keep the layering from silently rotting?**
  A: An import-linter contract in CI fails the build if anything under `app.api`
  *directly* imports a provider SDK (`google`) or a raw HTTP client (`httpx`) —
  routers must go through services. It's `allow_indirect_imports=True` so it
  checks direct edges only (the transitive path through services is the whole
  point). DIP is enforced, not just described.

- **Q: How is rate limiting applied without decorating 25 endpoints?**
  A: A middleware classifies each request by path into EXEC / AI / AUTH / STD and
  applies a per-identity (user→guest→IP) sliding window, returning 429 +
  Retry-After in the standard envelope. Centralized, so a new AI route is limited
  automatically. In-memory (resets on restart, per-worker) is the accepted
  free-tier trade-off; Redis is the documented upgrade.

- **Q: The frontend and backend are separate Render services — how do cookies
  work?**
  A: The static site rewrites `/api/*` and `/health` to the backend, so the
  browser only ever sees one origin. That makes the `SameSite=Lax` httpOnly
  refresh cookie same-site and CORS a non-issue in the happy path (CORS is still
  locked to `ALLOWED_ORIGINS` for the documented cross-site fallback).

- **Q: How would you know if this broke in production?**
  A: `/health` (liveness, drives the cold-start banner) + `/health/detailed` (a
  cheap `SELECT 1` and provider-config status) + structured JSON logs with a
  request-id per request — enough to triage on a free tier without Prometheus.

**8. Senior follow-up.**

- **Q: `alembic upgrade head` runs in the build command. What's the risk and how
  would you harden it?**
  A: Two builds racing (or a slow migration) could contend on the DB, and a
  failed migration fails the deploy — though Render keeps the previous version
  live, so the site stays up. On a paid tier I'd move it to a `preDeployCommand`
  (runs once, after build, before cutover) and gate destructive migrations behind
  an explicit review; on free tier, build-time migration + the rollback guarantee
  is the pragmatic choice.
