# ADR-020 — Code execution on a free provider (Paiza replaces Judge0 as default)

**Status:** Accepted (2026-08-02) · **Amends [ADR-005](005-execution-provider.md)** · §11

## Context
ADR-005 chose **Judge0 CE via RapidAPI** as the default execution provider on the
strength of its free tier. That tier is now effectively **paid** — the Basic plan
is metered per submission ($0.0017/use) plus a bandwidth platform fee. **Payment
is not an option for this project**, so the default had to change.

The obvious fallback, the **public Piston API** (`emkc.org`), is also gone:

```
POST https://emkc.org/api/v2/piston/execute -> 401
{"message":"Public Piston API is now whitelist only as of 2/15/2026 ..."}
```

(`GET /runtimes` still returns 200 — only `/execute` is gated.)

## Decision
Default `EXECUTION_PROVIDER=paiza` — the **Paiza.io public runner**, which accepts
the literal `api_key=guest`: no account, no card, no key to leak. Verified live
against all five languages the OA page offers (`python, java, cpp, c, javascript`),
each with stdin, plus a compile-error and a wrong-answer case.

**Judge0 and Piston are kept as selectable strategies, not deleted.** That costs
one small module each and preserves the whole point of the Strategy seam (§11.2):
switching is a one-env-var change if the user later self-hosts Piston (free, via
docker) or buys a Judge0 plan. Nothing about them is *required* any more — no
key, no dashboard entry, no fail-fast.

## Why not just remove code execution?
The OA compiler is the feature that distinguishes this project — the app already
has an AI-review-only **degraded mode** and would keep "working," but every
submission would score 0/`ai_review_only` and the honest-scoring guarantee (§11.4)
would be vacuous. Free real execution was available, so the feature stays.

## Consequences
- **No paid dependency anywhere in the deploy path.** The only secret needed to
  run the full app is `GEMINI_API_KEY` (free tier).
- Paiza is an **async create → poll → details** API; the provider wraps it behind
  the same synchronous `CodeExecutionProvider.execute()` seam, with the whole
  create+poll cycle bounded by a deadline so a stuck job can't pin a Gunicorn
  worker.
- `/health/detailed` now reports `execution: ready|unconfigured` (readiness)
  rather than `execution_key: configured|unconfigured` (key presence), because
  the default provider legitimately has no key.
- Degraded mode is unchanged and still the safety net if the provider is down.
- **Third-party free service, no SLA.** Accepted for an interview-showcase
  project; the mitigation is the Strategy seam + degraded mode, and a self-hosted
  Piston is the documented upgrade path.
