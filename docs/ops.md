# Ops runbook (envs, deploys, DB, runbooks)

## Environments
| | Local dev | Prod (Render) |
|---|---|---|
| URL | http://localhost:8000 | https://swimcoach-ss5j.onrender.com |
| DB | `sqlite:///./swim_coach.db` (auto-created via `create_all`) | Supabase Postgres via pooler `:5432` (session; live; IPv4; Render Free has no IPv6) |
| Migrations | **Never run alembic locally** (stamp stale by design) | `alembic upgrade head` against pooler URI, then `alembic current` |
| Sleep | n/a | Free plan sleeps ~15 min idle; cold boot ~17s; `/api/health` warms it |

Env source of truth: `.env.example` (copy to `.env` locally). Dashboard vars in
`render.yaml` (commented). App refuses to boot without `SECRET_KEY`,
`MP_ACCESS_TOKEN`, `MP_PUBLIC_KEY`.

## Deploy
Push to `main` → Render autoDeploy (~2 min). After deploy, hard-refresh
(Ctrl+Shift+R) — SW serves cached JS otherwise. **Any change to a file in
`sw.js` STATIC_ASSETS needs a `CACHE_VERSION` bump in the same commit.**

## Runbooks
### Apply a migration on prod
```powershell
$env:DATABASE_URL="postgresql://postgres.REF:PASSWORD@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
.\venv\Scripts\python.exe -m alembic current   # expect previous head
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m alembic current   # expect new head
```
Live prod uses `:5432` (session pooler); `:6543` (transaction) also works for
migrations. Don't switch a working `DATABASE_URL` mid-week.
Never paste the URI in chat. Prod head history: `e5f6a7b8c9d0` (27/09) →
`f6a7b8c9d0e1` (07/10) → `g7b8c9d0e1f2` → `h8c9d0e1f2a3` (11/10) →
`h9d0e1f2a3b4` (20/10, applied: reminder_last_sent).

**Order matters.** Render autoDeploys `main`. Apply the migration *before*
merging/pushing code that selects the new column; otherwise every
`AthleteProfile` query returns 500 (`UndefinedColumn`) and the app bounces
users to onboarding. If already deployed, run `alembic upgrade head` — no
redeploy needed. The 20/10 plan-generation 500 was this drift: prod served
Fase 2 code (SW `v1.4.0`) while Supabase was still at `h8`.

### Grant admin (one-time per owner)
Supabase → Table Editor → `users` → your row → `is_admin = true`.
Requires migration `g7` applied first. Nobody can self-promote (only admins can).

### Owner password reset (no email infra)
```bash
curl -X POST https://swimcoach-ss5j.onrender.com/api/auth/admin-reset-password \
  -H "Content-Type: application/json" -H "Cookie: access_token=<YOUR_ADMIN_JWT_OR_SESSION>" \
  -d '{"email":"user@example.com"}'
# => {"email": "...", "temp_password": "..."} — shown ONCE, pass via secure channel
```
User logs in with it, then sets their own via Settings → Change password.

### Wake prod before demos/crawls
Open `/api/health` (200 fast = awake), `/`, `/ads.txt`. Keep traffic flowing
for ~2h around AdSense resubmits.
DB readiness: `GET /api/health/db` → 200 `{"db":"ok"}`; **503 `{"db":"down"}`
means the DB is unreachable (e.g. Supabase paused), even if `/api/health` is
green. `/api/health` stays DB-free on purpose: Render's health check must not
restart-loop during a DB outage.

### Web Push VAPID (one-time setup)
```powershell
.\venv\Scripts\python.exe tools/gen_vapid.py   # prints 2 lines, keep secret
```
Put both lines in Render dashboard → Environment (`VAPID_PUBLIC_KEY`,
`VAPID_PRIVATE_KEY`) + local `.env`. Never commit them. Verify:
`GET /api/notifications/vapid-key` returns the public key; as admin,
`POST /api/notifications/test` sends a live push to your own subscriptions
(requires enabling the toggle in Settings first).

### Reminder cron (Phase 2, Render Cron Job ~$1/mo, needs card on file)
1. Generate a secret (32 hex chars, same recipe as SECRET_KEY) and set
   `CRON_SECRET` in Render env vars (+ local `.env` for manual triggers).
2. Render dashboard → New → **Cron Job** → same repo → command: ignored
   (Render calls a URL, not code) — set **Schedule** `*/15 * * * *` and
   **URL**: `POST https://swimcoach-ss5j.onrender.com/api/notifications/dispatch-due`
   with header `X-Cron-Secret: <secret>`. (If the cron UI only supports GET,
   keep the external-cron fallback: cron-job.org → same URL+header every 15 min.)
3. Verify: trigger once manually and check `{checked, sent, skipped}`;
   user rows get `reminder_last_sent = today` (Supabase) only on success —
   failures retry on the next tick inside the 30-min window.
4. Rotate the secret like a password if ever exposed (Render env + cron job).

### MercadoPago Pro (recurring $100 MXN/month)
Flow: subscription **without an associated plan** (`POST /preapproval`,
`status=pending`) → MercadoPago returns `init_point`; after payment the webhook
re-fetches the resource from the MP API before granting access. No
`MP_PREAPPROVAL_PLAN_ID` is needed (the setting is ignored).

1. MP panel → **Your integrations** → app → **Webhooks**: URL
   `https://swimcoach-ss5j.onrender.com/api/subscription/webhook`; enable
   `subscription_preapproval`, `subscription_authorized_payment` and `payment`.
   Copy the **secret signature** (`whsec_…`).
2. Render → Environment: `MP_ACCESS_TOKEN` (`APP_USR-…` prod, `TEST-…` only
   sandbox), `MP_PUBLIC_KEY`, `MP_WEBHOOK_SECRET=whsec_…` and (recommended)
   `BACKEND_URL=https://swimcoach-ss5j.onrender.com`; it defaults to
   `FRONTEND_URL` when empty. `MP_BACK_URL` is optional: it defaults to
   `FRONTEND_URL`, must be HTTPS and cannot contain `#`. Redeploy.
3. Sandbox test (never with the production token): use MP **test users**, buy
   Pro from `/#/upgrade`, then verify in Supabase:
   `select subscription_tier, subscription_status, current_period_end,
   mp_preapproval_id from users where email='…';`
   The payer must be a **buyer** test account, different from the collector
   (the account that owns the app). The email registered in SwimCoach must
   match the buyer's MercadoPago email; otherwise MP returns
   `Payer and collector cannot be the same user` or `User bad request`.
   **Production limitation:** MP requires `payer_email` and validates it
   against the paying account. Before charging real users, add an MP payer
   email field to the profile/upgrade flow (or require the same email in both
   accounts); a SwimCoach email that differs from the MP account cannot pay.
4. Cancel from `/#/upgrade` → `PUT /preapproval/{id}` with
   `{"status":"cancelled"}` (two Ls; `canceled` is rejected with 400). Pro
   remains until `current_period_end` and `get_current_user` downgrades lazily
   after that date. Cancelling is idempotent: a 400 is treated as success only
   when the resource is already `cancelled`.
5. `/api/subscription/webhook/test` is dev-only (404 in production).
   The webhook is idempotent and always re-reads MP, never the request body.

#### Local sandbox (no real charges)

MercadoPago rejects `http://localhost` and any `back_url` containing `#`.
For local testing use a public HTTPS tunnel and two different test accounts:

1. Start the API on `127.0.0.1:8000` and a tunnel:
   `cloudflared tunnel --url http://localhost:8000` (or ngrok).
2. In `.env`:
   `BACKEND_URL=https://<tunnel-host>`
   `MP_BACK_URL=https://<tunnel-host>/`
   `MP_WEBHOOK_SECRET=` (empty is OK locally; the webhook still re-fetches MP).
   Restart uvicorn after changing `.env`.
3. In SwimCoach register the **buyer** test account's email (not the
   collector/app owner). MP validates `payer_email` against the account that
   pays and rejects payer == collector.
4. Open the **tunnel URL**, not localhost, so the session cookie and the
   return redirect use the same host. Buy Pro from `/#/upgrade`.
5. MP returns to `https://<tunnel-host>/?preapproval_id=...`; `app.js` routes
   that to `/#/upgrade` automatically (the `back_url` cannot carry a hash).
6. If the real webhook does not reach the tunnel, simulate it:
   `POST /api/subscription/webhook/test` with
   `{"type":"subscription_preapproval","data":{"id":"<preapproval_id>"}}`.
7. Cancel with `{"status":"cancelled"}` (two Ls). Sending the old one-L
   `canceled` returns 400 (`Invalid preapproval status param: canceled`); the
   code verifies the resource before trusting a 400, so a rejected request is
   never reported as success. Pending and authorized preapprovals can both be
   cancelled.

## Tests & CI
- Suite: `python -m tests.test_final_all` (E2E; only expected 400/404) + unit
  funcs in `tests/test_adaptive.py`, `tests/test_salo_mix.py` (no pytest in venv).
- CI (`.github/workflows/ci.yml`, non-blocking): `node --check` on frontend JS,
  `audit_ui` (strict), `audit_spec` (diff-based), E2E suite on sqlite.
