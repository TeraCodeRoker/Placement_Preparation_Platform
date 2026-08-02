# Testing strategy

Traceable to §9.2. The suite is fast, deterministic, and free: **no test hits a
real external network** — Gemini, the execution provider, and the DB driver are
all mocked or run against a temp SQLite.

## Backend (`pytest` + `pytest-asyncio` + `httpx.AsyncClient`)
- **Unit** — services tested with the Gemini + execution clients injected as
  fakes (constructor/`Depends` injection).
- **Integration** — full request/response cycles through the ASGI app against a
  per-test temp SQLite DB (`api_client` fixture with `get_db` overridden).
- **Contract** — endpoints declare `response_model`s, and tests assert the
  returned shapes (e.g. auth envelopes, OA dual signals, error envelope).
- **Failure modes (mandatory, §9.2)** — all present at the module level:
  - Gemini timeout → 503, malformed JSON → 502 (`test_gemini_reliability.py`)
  - Execution provider unreachable → 503, execution timeout/TLE
    (`test_execution.py`)
  - DB-unavailable behavior: `get_db` rolls back on error; account-deletion
    cascade + migration up/down verified.
- **Coverage** — `≥80%` on `app/services/` enforced in CI
  (`--cov=app/services --cov-fail-under=80`); currently ~91%. Coverage evidences
  the behavioral/failure tests, not padding.

## Frontend (Vitest + React Testing Library)
- API layer mocked at the `client.js`/module boundary; RTL renders the real
  components (auth flow, OA run/submit + degraded banner, notes, history).

## E2E / browser testing — explicit decision (§9.2)
**Decided: omit a per-PR Playwright suite; substitute documented manual
verification.** Rationale: a meaningful browser E2E needs the full stack live
(backend + real Gemini + real Judge0 + Postgres), which isn't available in CI
without burning free CI minutes and real API quota, and mocking the whole stack
in a browser adds fragility for little gain over the RTL component tests +
backend integration tests already covering both key journeys
(interview start→answer→summary; OA problem→run→submit). The seam is left open:
`e2e/` + an `e2e-nightly` workflow can be added later to run against a deployed
preview.

### Manual verification checklist (run against the deployed app after each deploy)
1. Guest: Home loads; start a Mock Interview → answer → see summary.
2. Guest: OA → generate problem → Run (visible tests) → Submit → see pass-rate
   ring + AI review; confirm hidden-case I/O is not shown.
3. Register → confirm history now lists the interview/OA done as guest (claimed).
4. Log in as the bootstrap admin → Notes → Admin panel → publish a note →
   confirm it appears on the public Notes page.
5. Resume: upload a text PDF → analysis renders; upload a non-PDF → clean error.
6. Kill the execution provider key → Submit → confirm the "AI-review-only"
   degraded banner (never a silent pass).
