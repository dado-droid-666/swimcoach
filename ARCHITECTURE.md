# ARCHITECTURE

```
┌─────────────┐      HTTPS       ┌──────────────────┐     pooler :6543    ┌──────────────┐
│ PWA (Edge/  │ ──────────────▶ │ FastAPI (Render) │ ──────────────────▶ │ Supabase PG  │
│ Chrome, SW) │ ◀────────────── │ StaticFiles+API  │                     └──────────────┘
└─────────────┘   cookie auth   └────────┬─────────┘
                                         │ HTTPS
                              ┌──────────┼───────────┐
                              ▼          ▼           ▼
                        MercadoPago  AdSense JS   Web Push
                        (preapproval) (free tier) (VAPID+FCM/WNS)
```

## Request flow
1. Browser loads `/` (same-origin; no CORS in prod). SW serves cached shell.
2. `app.js`: `checkAuth()` → `GET /api/auth/me` (401 → `#/login`).
3. Onboarding (5 steps, `localStorage` scratch) → `POST /competition/generate`
   (idempotent, ~60s, button locked) → dashboard.
4. Dashboard/week/session read `/api/plan/*`; feedback writes RPE + exercise logs;
   adaptive state modulates current/future weeks only (lost volume never restacked).

## Backend domains (`backend/routes/` → `services/`)
| Route | Purpose | Key service |
|---|---|---|
| `auth` | register/login/logout/me + change-password + admin-reset | `auth.py` (JWT cookie, bcrypt) |
| `profile` / `competition` | athlete profile + goal CRUD | models/schemas |
| `plan` | macrocycle/week/today/overview + Pro move/regenerate | `swim_generator`, `strength_generator`, `adaptive_state` |
| `feedback` | daily RPE + exercise logs (ML data) | models |
| `swimtests` | persisted CSS tests (server truth for prefill/dashboard) | — |
| `stats` | summary (all) + readiness/progress (Pro `require_pro`) | `load_model` (M2 server, clamp ±25%) |
| `subscription` | MP checkout/portal/cancel/webhook + tier status | `mercadopago_service` |
| `notifications` | VAPID key, subscribe/upsert, test (admin), receipts (debug) | `pywebpush` |

## Plan generation pipeline
`macrocycle_calculator` (phases Base→Build→Peak→Taper→Race, volume caps
12k/16k/25k) → per-session `swim_generator` (Salo MIX by event category from
`data/salo_swim.json`, CSS Z1–Z5 + SPM, `snap_25` multiples, scaled titles +
`method` provenance) + `strength_generator` (TRX/KB/BW templates, A/B/C split,
caps 4/4/3/1/0) → `adaptive_state` (feeling≤2→recovery×0.7, adherence ±,
strokes≥50→Ch1 drills, youth/prehab rules) → stored as JSON columns.
Generation is atomic: all rows are built in memory, then the old plan is
replaced in one transaction. Failures roll back and keep the previous plan.

## Data & ML
- `SwimTest` persists CSS tests (never retyped); RPE + `ExerciseLog` feed M2.
- Client M1 (tier→level calibration) in `frontend/ml/` + `tier_model.js`;
  server M2 (`load_model.py`) modulates volume; `export_training_data.py`
  produces anonymized retrain CSVs (consent-gated research only).

## Cross-cutting decisions (see `docs/specs/principles.md` for dates)
English UI · dark ocean + aqua accent · ML applies tier→level · Mon=0…Sun=6,
local `en-CA` dates · multiples of 25 · idempotent generate · free ads/Pro clean ·
public privacy/terms · consent-gated research.

## Operational notes
- Prod DB head tracked in `docs/ops.md`; local sqlite uses `create_all` + manual
  ALTERs (stale alembic stamp by design — never run alembic locally).
- Render Free sleeps; `/api/health` is DB-free (green ≠ DB healthy).
- `render.yaml` declares a Render DB but live traffic uses Supabase (dashboard override).
