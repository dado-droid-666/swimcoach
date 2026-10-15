# SwimCoach

Competition-focused swim periodization PWA. Generates integrated Swim + Strength
macrocycles from a goal race date. Free tier with ads + Pro ($100 MXN/mo) via MercadoPago.

- **Prod:** https://swimcoach-ss5j.onrender.com (Render Free + sleep; Supabase Postgres via pooler `:6543`)
- **Docs for humans & AI:** `docs/specs/` (principles, tokens, components, patterns, training) + `docs/llms.txt` index + `docs/ops.md` runbooks
- **Session log + live pendings:** `RETOMAR.md`

## Stack
- **Backend:** FastAPI + SQLAlchemy 2 + Pydantic v2 + Alembic (Python 3.13, pinned in `backend/requirements.txt`)
- **Frontend:** Vanilla JS SPA (hash router, no build step) + Pico.css + custom `style.css` + closed token set (`css/tokens.css`)
- **PWA:** hand-rolled `sw.js` (cache-first static, network-first API)
- **Auth:** JWT in HttpOnly cookies (`Secure` in prod, `SameSite=Lax`) + bcrypt
- **DB:** SQLite locally (`create_all`), Supabase Postgres in prod (alembic)
- **Payments:** MercadoPago preapproval · **Ads:** AdSense (free tier) · **Push:** Web Push + VAPID (Phase 1)

## Repo map
```
swimcoach/
├── frontend/            # PWA: index.html shell, js/ (one global per view), css/, ml/, sw.js
├── backend/             # main.py, config.py, database.py, models.py, schemas.py, auth.py
│   ├── routes/          # auth, profile, competition, plan, feedback, stats, subscription, swimtests, notifications
│   ├── services/        # swim/strength generators, adaptive_state, salo_mix, css_zones, load_model (M2), macrocycle, mercadopago
│   └── scripts/         # export_training_data.py (ML retrain CSV)
├── data/                # salo_swim.json + salo_dryland.json (book MIX), drill_library.json, swim_templates/
├── migrations/versions/ # linear alembic chain (prod head: see docs/ops.md)
├── tests/               # live suite (test_final_all E2E + adaptive/salo/password/notifications) + attic/
├── tools/               # audit_ui.py (strict), audit_spec.py, gen_vapid.py + attic/
├── docs/                # specs/, ops.md, llms.txt
├── .github/workflows/ci.yml  # non-blocking: node --check, audits, suite
├── render.yaml          # Render config (commented) · Dockerfile · alembic.ini
└── RETOMAR.md           # session log + live pendings
```

## Quickstart (local, Windows PowerShell)
```powershell
cd "C:\Users\mocon\OneDrive\swimcoach"
Copy-Item .env.example .env   # then fill SECRET_KEY + MP TEST keys
.\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
# App: http://localhost:8000  ·  Docs: http://localhost:8000/docs (dev only)
```
Tests (from root): `.\venv\Scripts\python.exe -m tests.test_final_all`
Unit funcs: see `tests/README.md`. Full checks: `node --check frontend/js/*.js` + `python tools/audit_ui.py`.

## Environments & deploys
| | Local | Prod |
|---|---|---|
| URL | http://localhost:8000 | https://swimcoach-ss5j.onrender.com |
| DB | sqlite (auto `create_all`; **never run alembic locally**) | Supabase pooler `:6543` (IPv4; no IPv6 on Free) |
| Sleep | n/a | Free sleeps ~15 min idle; cold boot ~17s — warm via `/api/health` |
Push to `main` → Render autoDeploy (~2 min) → hard-refresh (Ctrl+Shift+R).

## Rules every engineer (and agent) must know
1. **SW bump rule:** any change to a file in `sw.js` `STATIC_ASSETS` needs a `CACHE_VERSION` bump in the same commit.
2. **No new color literals** outside `frontend/css/tokens.css` (audit fails CI).
3. **Spec sync:** UI change → update `docs/specs/*`; methodology change → `docs/specs/training.md`.
4. **No silent failures:** user-initiated actions always surface errors; guards release locks.
5. **Passwords are bcrypt hashes** — irreversible by design; resets go through admin endpoint (docs/ops.md).
See `CONTRIBUTING.md` (conventions + pre-push checklist) and `ARCHITECTURE.md` (system map).
