# ADR-017 — CI/CD

**Status:** Accepted · **Relates to:** §9.3

## Decision
GitHub Actions runs on every PR and on push to `main`
(`.github/workflows/ci.yml`), with four jobs.

### Blocking gates (a red check blocks merge)
- **Ruff** — lint (`E`,`F`,`I`,`B`,`UP`) on backend.
- **mypy** — strict on `services/`,`integrations/`,`schemas/` (per ADR-013).
- **import-linter** — the dependency-inversion contract: routers must not
  *directly* import a provider SDK (`google`) or a raw HTTP client (`httpx`).
  DIP is a checked property, not a comment.
- **pytest + coverage** — full suite; `--cov-fail-under=80` on `app/services`.
- **Frontend** — `npm ci`, Vitest, production build (fails on a broken build).
- **gitleaks** — secret scanning, **blocking** (§9.1).

### Reported-only (advisory, never blocks — ADR-013)
- **pip-audit** and **npm audit** run in an `continue-on-error` job. Transient
  upstream advisories on transitive deps shouldn't block an unrelated PR;
  findings are visible in the job log and triaged deliberately.

## Tool + strictness summary (§9.3)
| Concern | Tool | Level |
|---|---|---|
| Python lint | Ruff | E,F,I,B,UP — blocking |
| Python types | mypy | strict on business layers — blocking |
| Architecture | import-linter | DIP contract — blocking |
| Backend tests | pytest | full suite + 80% services coverage — blocking |
| Frontend | Vitest + vite build | blocking |
| Secrets | gitleaks | blocking |
| Vulns | pip-audit / npm audit | reported-only |

## Deploy + rollback
Render **auto-deploys** the connected branch on merge to `main` (no bespoke
deploy workflow to maintain — documented, not reinvented). On a failed deploy,
Render keeps the **previous successful deploy live** — so a bad build never takes
the site down. E2E is intentionally not on the per-PR path (see `docs/TESTING.md`).
