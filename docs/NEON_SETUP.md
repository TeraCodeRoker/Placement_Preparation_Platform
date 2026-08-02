# `DATABASE_URL` — Neon Postgres, step by step

The one database step, start to finish. **Free forever**, no card. Steps marked
🧑 are yours (they need your account); everything else is already built.

Why Neon and not Render's own Postgres: Render's free Postgres **expires after 30
days**. Neon's free tier doesn't expire — it just auto-suspends when idle and
wakes on the next query. See [ADR-002](ADRS/002-database.md).

---

## 1 · 🧑 Create the Neon project

1. Go to **<https://neon.tech>** → **Sign up** (GitHub login is quickest).
2. On the "Create project" screen:
   - **Name:** `prepstack`
   - **Postgres version:** leave the default
   - **Region:** pick the one nearest your Render region — for India, `Asia
     Pacific (Singapore)`; keeping DB and app on the same continent avoids
     ~200 ms of round-trip on every query.
3. Click **Create project**.

## 2 · 🧑 Copy the connection string

Neon drops you on a **Connection Details** panel (or: **Dashboard → Connect**).

1. Make sure the **Database** dropdown says `neondb` and the role is
   `neondb_owner` (the defaults).
2. Leave **"Pooled connection" ticked** — the pooled host handles many short-lived
   connections, which is exactly what Render's Gunicorn workers do.
3. Click **📋 Copy snippet**. You get something like:

```
postgresql://neondb_owner:npg_XXXXXXXX@ep-still-frost-a1b2c3d4-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

> ⚠️ **That string contains your database password.** Treat it like a password:
> paste it only into Render's dashboard, never into a file you commit, a chat, or
> a screenshot. It is *not* in `.env.example` and must never be.

## 3 · Do **not** reshape the string

Paste it **exactly as copied**. Verified against this project's parser:

| What Neon gives you | Result |
|---|---|
| `postgresql://…?sslmode=require` | ✅ → `django.db.backends.postgresql`, `sslmode` preserved |
| `postgres://…` | ✅ identical |
| extra `&channel_binding=require` | ✅ passed through |

No scheme rewriting, no stripping the query string. Keep `?sslmode=require` —
Neon requires TLS and the connection fails without it.

## 4 · 🧑 Put it into Render

**Render dashboard → `prepstack-api` → Environment → Add Environment Variable**

| Key | Value |
|---|---|
| `DATABASE_URL` | *(paste the Neon string)* |

Save. Render redeploys, and the build step runs `python manage.py migrate`, which
creates all tables in Neon. Nothing else to run.

## 5 · Verify it worked

**a. From the app** — `GET https://prepstack-api.onrender.com/health/detailed`

```json
{ "status": "healthy", "db": "up", ... }
```

`"db": "up"` means Django connected to Neon and ran `SELECT 1`.

**b. From Neon** — **Dashboard → Tables**. You should see the schema:
`users`, `guest_sessions`, `refresh_tokens`, `interview_sessions`,
`interview_results`, `mcq_sets`, `mcq_questions`, `mcq_attempts`,
`resume_analyses`, `oa_problems`, `oa_submissions`, `notes`.

**c. Persistence (the point of all this)** — register an account, then in Render
hit **Manual Deploy → Deploy latest commit**. Log in again after it restarts: if
your account survived, durable state is real.

---

## Optional: point your local machine at Neon

Only if you want to test against Postgres locally. Everyday local dev is fine on
the default SQLite.

In `backend/.env` (**gitignored — never `.env.example`**):

```
DATABASE_URL=postgresql://neondb_owner:npg_XXXX@ep-….neon.tech/neondb?sslmode=require
```

```bash
cd backend && python manage.py migrate
```

To go back to SQLite, restore `DATABASE_URL=sqlite:///db.sqlite3`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Boot fails: `DATABASE_URL (must be Postgres in production, not SQLite)` | `APP_ENV=prod` with a SQLite URL | Set the real Neon URL. This guard is deliberate — it stops a "working" deploy that silently loses all data on restart. |
| `password authentication failed` | Snippet copied while the password was still masked | In Neon click **Show password** (or **Reset password**), re-copy the whole string. |
| `SSL connection is required` | `?sslmode=require` got trimmed | Re-paste the full string including the query. |
| `could not translate host name` | Partial paste | Confirm the host ends in `.neon.tech`. |
| First request after idle takes ~1 s | Neon auto-suspend on free tier | Expected. It compounds with Render's ~30–60 s cold start; the frontend already shows a "waking up" banner. |
| Tables missing but `db: up` | `migrate` didn't run | Check the Render **build** log; re-run from Render **Shell**: `python manage.py migrate`. |

## Rotating the password later

Neon **Dashboard → Roles → Reset password** → copy the new string → update
`DATABASE_URL` in Render → redeploy. No code change ([ADR-016](ADRS/016-security.md)).
