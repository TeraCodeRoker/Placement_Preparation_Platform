# Definition of Done — verification (§13)

Each item is checked against repository state. **Two items require your Render/
Neon accounts** and are marked 🧑 USER-ACTION — everything needed for them is
built and committed; only the live click-through is yours. (No execution-provider
account is needed — see [ADR-020](ADRS/020-free-code-execution.md).)

| # | DoD item | Status | Evidence |
|---|---|---|---|
| 1 | Blueprint + full MECE roadmap produced and approved before code | ✅ | `docs/BLUEPRINT.md`, `docs/ROADMAP.md`; approved before T1 |
| 2 | Every atomic task implemented, validated, committed | ✅ | T1–T37 all ☑; one commit per task (Conventional Commits) |
| 3 | Live on Render via committed `render.yaml`, free-tier only | 🧑 | `render.yaml` + `docs/DEPLOYMENT.md` ready; **live deploy = your accounts/keys** |
| 4 | Both Gemini call sites via one shared layer on modern SDK; no legacy SDK | ✅ | `integrations/gemini/`; `app_legacy_ref/` deleted; `google-generativeai` absent |
| 5 | MCQ + OA both call Gemini per §10 (structured output, prompts, reliability, caching, error taxonomy) | ✅ | `mcq_service` (TTL cache) + `oa_service`; `test_gemini_reliability` |
| 6 | OA executes real code via provider abstraction; honest non-conflated results; degraded mode | ✅ | `integrations/execution/` Strategy; `test_oa_service` (grading + degraded); real run at deploy |
| 7 | Durable state survives spin-down/restart/redeploy; no SQLite-on-disk for durable | ✅ | Postgres via `DATABASE_URL` (ADR-002); SQLite only in tests |
| 8 | Execution provider confirmed accessible at build time; deployed `/run` `/submit` run real code | 🧑 | Paiza (free, keyless) verified live across python/java/cpp/c/js; **verify live at deploy** |
| 9 | Auth (registered+guest+admin) end-to-end; Notes admin wired; JWT-storage ADR | ✅ | Phase 4 + notes module; ADR-004; `test_auth`/`test_guards`/`test_notes` |
| 10 | CORS locked to explicit origins; rate limiting on every AI + exec endpoint | ✅ | `main.py` CORS = `ALLOWED_ORIGINS`; `rate_limit.py`; `test_security` |
| 11 | Secret scanning + dep-vuln checks in CI; blocking-vs-reported stated | ✅ | `ci.yml`: gitleaks blocking, pip-audit/npm audit reported-only (ADR-013) |
| 12 | PII/data-retention policy + working account-deletion cascade | ✅ | ADR-010; `DELETE /users/me`; `test_users` cascade |
| 13 | Backend tests pass w/ meaningful coverage bar; frontend passes; 5 failure-mode tests at module level; no real network; E2E decision documented | ✅ | 143 backend + 15 frontend tests; 93% services coverage; 5 failure modes; `docs/TESTING.md` |
| 14 | `INTERVIEW_PREP.md` exists, non-trivial, traceable | ✅ | 11 modules, each grounded in real files |
| 15 | Frontend single-integration-point intact + extended; OA editor code-split | ✅ | `client.js`/`endpoints.js`; Monaco verified absent from main bundle |

## Remaining (yours)
1. **Rotate** the leaked Gemini key; create a **Neon** DB. (No execution key —
   ADR-020.)
2. Deploy via the Render Blueprint and set the secrets (`docs/DEPLOYMENT.md`).
3. Run the manual verification checklist (`docs/TESTING.md`) against the live app,
   including confirming `/run` + `/submit` execute real code (item 8).

Everything else is done, tested, and committed.
