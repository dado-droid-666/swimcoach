# Frontend patterns (shell SPA)

## Shell regions (`frontend/index.html`)
`navbar` (brand + hidden links) → `main#app` (router outlet) →
`bottomnav` → `flash-overlay` → `rpe-overlay` / `exlog-overlay` → `footer`
(Home/Privacy/Terms/Contact) → scripts (`api, utils, public, …, app` last).

## Router (`frontend/js/app.js:handleRoute`)
- Hash routes (`#/week`, `#/session/today`); query via `?step=`.
- Matching is **prefix-based, insertion-ordered**: `'/'`, `'/privacy'`,
  `'/terms'` live **LAST** — putting `'/'` first swallowed every route
  (04/10 incident: login/register unreachable, zero server traffic).
- Public (no login): `/`, `/login`, `/register`, `/privacy`, `/terms`.
  Protected list redirects to `#/login`; logged-in users bounce `/`→dashboard.
- `updateNav`: `'#/'` is **exact-match** (`startsWith('#/')` is true for
  everything and hid the bottomnav — same incident).

## View convention
```js
function renderX(app) {
    if (app.state.user) { window.location.hash = '#/dashboard'; return; } // guards first
    document.getElementById('app').innerHTML = html;   // then paint
    document.getElementById('x-form').addEventListener('submit', …); // then wire
    if (window.refreshAds) setTimeout(window.refreshAds, 100);       // ads last (free only)
}
```
- Guards → paint → wire → ads. Never wire before paint (elements don't exist).
- Form data: collect named inputs directly (FormData throws on bare `<fieldset>` — 09/26 incident).

## State & server truth
- `app.state {user, profile, competition, macrocycle, tier}` loads post-login
  (`checkAuth` → profile → competition). Views redirect to onboarding when
  profile/competition are missing (fresh accounts).
- `localStorage.onboarding_data` is scratch; `first()` wins on re-saves
  (Back/Next dedup). Server (`swim_tests`, profile) is truth for prefill.

## Free / Pro gating
- Client: `app.state.tier === 'free'` shows ads + lock icons (`🔒 Move`).
- Server: `require_pro` on move/regenerate + pro stats. Never gate on client alone.

## Dates
- 100% local `en-CA` (`YYYY-MM-DD`); weeks Lun–Dom with Monday-anchored
  `week_start`; rest-day cards link ±14d neighbors.

## Errors
- User-facing failures always `app.showError(msg)` (5s toast). No silent
  `return` on user-initiated actions (07/10 `_generating` incident).
- `api.js` 401 → redirect login (except login/register calls); 403 → upgrade
  message; 422 array details flattened to `field: msg`.

## Caching (PWA)
- `sw.js` `STATIC_ASSETS` is cache-first. **Any change to a listed file
  requires a `CACHE_VERSION` bump in the same commit** (04/10 + 07/10).
- New static file? Add it to `STATIC_ASSETS` too.

## Reminder dispatch (Phase 2)
`POST /api/notifications/dispatch-due` (header `X-Cron-Secret`, constant-time)
every ~15 min: users with subs + `reminder_time` inside [now-30min, now] in
their `reminder_tz` + `reminder_last_sent != today` + session today (rest days
skipped) → `send_push` → stamp date. Idempotent; failures retry next tick.
`CRON_SECRET` empty = 401 to everything.
