# Components (usage + do's and don'ts)

Conventions: views are functions `renderX(app)` that set
`#app.innerHTML` then wire events. Copy the snippet, adapt text only.

## card
```html
<article class="card" style="padding: 1.5rem; margin-bottom: 1rem;">
  <h2>Title</h2>
  <p>Body.</p>
</article>
```
- DO use for content blocks (How-it-works, FAQ, session blocks).
- DON'T nest cards more than one level; DON'T set background (comes from theme).

## big-btn (primary action)
```html
<button class="big-btn" id="generate-btn" onclick="completeOnboarding()">Generate My Plan</button>
<button class="big-btn secondary" id="exlog-back">←</button>
```
- DO give async buttons disabled+label states (`Generating…`, restore on every exit — see 07/10 `_generating` incident).
- DON'T leave a dead button: every guard clause must restore or explain.

## bottomnav
Fixed 5 tabs (`Today/Week/Plan/Log/Profile`), `data-route` driven, hidden on public routes (`app.js:updateNav`, exact-match `'#/'`).
- DO keep labels + order stable (muscle memory).
- DON'T add a 6th tab without updating the tour + specs.

## pills (multi-select)
```html
<label style="display:flex;align-items:center;gap:0.5rem;padding:0.5rem 1rem;border:1px solid var(--border-color);border-radius:0.5rem;cursor:pointer;" onclick="pillClick(event, this)">
  <input type="checkbox" name="swim_equip" value="fins" onchange="toggleEquipment(this)"> Fins
</label>
```
- DO single-tap toggle with visual feedback (`pillClick` + `:has`).
- DON'T use raw checkboxes/radios for option grids.

## overlays (rpe / exlog)
`.registro-overlay` (base `pointer-events:none`) + `.open` to show; bottom-sheet modal on mobile.
- DO trap the required input (effort 1-5; free tier cannot skip, Pro can).
- DON'T add a new overlay without a close path on every branch.

## tour (coach-marks)
`maybeAutoTour('dashboard'|'session')` once per screen (localStorage `swimcoach_tour_seen_v1`); Skip/Next/Esc/arrows; `? Guide` removed — tour is auto only.
- DO add steps via selector fallback chains (`[primary, fallback]`).
- DON'T auto-tour public pages (login/landing) — overlays would eat taps.

## ad-slot (free tier only)
```html
<div class="ad-banner" style="margin-top: 2rem; text-align: center; min-height: 90px;">
  <div style="font-size: 10px; color: var(--muted-color); text-transform: uppercase; letter-spacing: .08em;">Advertisement</div>
  <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-4540036176937342" data-ad-slot="7276396302" data-ad-format="auto" data-full-width-responsive="true"></ins>
</div>
```
- DO use `class="ad-banner"` (never `id` — duplicates broke rendering 30/09).
- DO render only when `app.state.tier === 'free'`; push via `window.refreshAds()` (safe: unfilled slots only).
- DON'T `push({})` blindly on route change (double-fill errors).

## forms
Labels above inputs; min/max/step set (`min="20" max="120"` for strokes); server re-validates everything (422 friendly).
- DO prefill from server (`getLatestTest`) so users never retype.
- DON'T trust client validation alone.

## field-error (inline, under the field)
```html
<input type="password" id="login-password" oninput="hideFieldError('login-error')">
<p class="field-error" id="login-error"></p>
```
```js
showFieldError('login-error', 'Incorrect email or password.'); // helpers in utils.js
```
- DO use for credential/field errors (login, register, change-password): they render under the field in `var(--error-color)`.
- DO clear on input (`oninput="hideFieldError('…')"`).
- DON'T replace the top toast: network/500/unknown errors still go to `app.showError`.
- Form containers (onboarding, profile) stack label-above-input at every width (`.onboarding-container .grid, .profile-view .grid { 1fr }`) so long options/placeholders never truncate.

## service-error (full screen)
`app.state.profileError` is set for any profile load failure that is **not**
404 (no profile yet) or 401 (redirected to login). The router renders a card
with the error, **Try again** (`app.retryProfile()`) and **Log out** instead of
redirecting to onboarding. `api.js` attaches `status`/`data` to errors so
views can tell 404 from 500. A server outage must never look like a new user.

## switch + push flow (Phase 1)
```html
<label class="switch">
  <input type="checkbox" id="push-toggle" onchange="togglePush(this)">
  <span class="slider"></span>
</label>
```
- DO pair the switch with a status line (`#push-status`) refreshed on paint: On / Off / Blocked (browser denied) / Not supported / Unavailable.
- DO revert `checkbox.checked` on failure and explain (denied → browser settings path; empty VAPID → "not configured", never a dead toggle).
- Flow: toggle → `requestPermission()` → `pushManager.subscribe(VAPID)` → `POST /subscribe` (upsert) → `refreshPushStatus()`. Off unsubscribes server + browser. Admin test: `POST /notifications/test` → SW `push` event → notification (click → `#/session/today`).
- Scheduler + time-picker are Phase 2 (`reminder_time`/`reminder_tz` already modeled in migration h8).
- Reminder time-picker (Settings): `input[type=time]` + IANA select (browser zone pre-detected); saves via `PUT /api/profile`; server revalidates format + zone (422).
