# SwimCoach design principles (infrastructure, not decoration)

> Article model: Smashing Magazine "How To Make Your Design System AI-Ready"
> (3 layers: spec files + token layer + audit). Every decision below is
> binding for humans and AI agents alike. Change a decision => update this
> file in the same commit (CONTRIBUTING sync rule).

## Product
1. **Competition-first.** Every plan ends in a goal race; Base → Build → Peak → Taper → Race. No generic "fitness" mode. (2026-09)
2. **English UI.** All user-facing strings in English. (decision 2026-09, RETOMAR)
3. **Recovery is part of the program.** Rest days render as explicit rest-day cards, never as gaps. (2026-09)
4. **Free tier is complete, Pro removes friction.** Free generates full plans with ads; Pro ($100 MXN/mo) unlocks rescheduling/regeneration + no ads. Free trial 1 month where offered. (2026-09)

## Visual
5. **Dark ocean theme.** Deep `#061a2e`, cards `#0e2b45cc`, single aqua accent `#3fd0e6`. No second accent color. (2026-09, fused with entrenamiento-app)
6. **Closed token set.** All color/spacing/radius/shadow values live in `frontend/css/tokens.css`. No new literals in code — audit fails CI. (2026-10)
7. **Bottom-nav mobile pattern.** 5 tabs (Today/Week/Plan/Log/Profile); top navbar hides links on mobile. Navbar max-width 860px, content 600-860px. (2026-09)

## Training methodology (mirror: docs/specs/training.md)
8. **ML applies.** Tier calibrates level (tier→level) and scales base volume; factor modulates reps. (user decision 2026-09)
9. **Single CSS retest cadence.** Retest every 6 weeks; dashboard owns the reminder. (2026-09)
10. **General KB/TRX templates.** Strength uses general implement templates + A/B/C split, mixed round-robin — never per-exercise bespoke plans. (2026-09)
11. **Lost volume is never restacked.** Missed sessions are marked, never rescheduled; only future volume/intensity modulates. (Salo, 2026-09)
12. **Multiples of 25.** Every distance (reps×dist, sets, totals) is a 25m multiple. (2026-09)
13. **Days are Mon=0…Sun=6.** Sunday no longer collides; week views are Lun–Dom; dates 100% local `en-CA`. (2026-09)
14. **One prescription per card.** Scale composite book sets by reps/minutes, never by rep distance; the original book text is provenance and is never rendered. (2026-10)

## Engineering (mirror: docs/specs/patterns.md)
14. **Idempotent generation.** Generating deletes the previous plan; button locks during ~60s. (2026-09)
15. **SW bump rule.** Any change to cached JS/CSS (`STATIC_ASSETS` in `sw.js`) requires a `CACHE_VERSION` bump in the same commit — the PWA serves stale code otherwise (bit us 04/10 router + 07/10 onboarding). (2026-10)
16. **Server truth, client cache.** Dashboard/onboarding prefill read the server (`swim_tests`, profile); localStorage is scratch only. (2026-09)
17. **Silent failures are bugs.** Anti-double-click guards must release + re-enable on every exit path (bit us 07/10 `_generating`). Errors always surface via `showError`. (2026-10)

## Legal / trust
18. **Ads are labeled.** Every ad slot carries an "Advertisement" caption. Free tier only. (2026-09)
19. **Privacy/Terms/Contact are public.** No-login routes `#/privacy`, `#/terms`; contact `swimcoach.app@gmail.com` (verified 04/10). (2026-09)
20. **Consent-gated research.** Anonymous training data used for research only with explicit opt-in consent. (2026-09)
