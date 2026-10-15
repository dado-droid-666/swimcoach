# CONTRIBUTING

## Conventions (binding — see `docs/specs/principles.md`)
- **UI English only.** Dark ocean theme, single aqua accent, closed token set.
- **No new color literals** outside `frontend/css/tokens.css` (`audit_ui.py` fails CI).
- **Spec sync:** frontend change → `docs/specs/{components,patterns,tokens}.md`;
  methodology change → `docs/specs/training.md`; new decision → `principles.md`.
- **Dates:** local `en-CA`, weeks Mon=0…Sun=6, Monday-anchored `week_start`.
- **Distances:** multiples of 25, always.
- **No silent failures:** every user action surfaces errors; locks/buttons restored on all exits.
- **Passwords:** bcrypt only; resets via admin endpoint (never read hashes).

## How to add…
- **Endpoint:** route in `backend/routes/<domain>.py` + schemas + `require_pro` if Pro;
  register router in `main.py`; cover in `tests/test_<domain>.py` (isolated sqlite pattern).
- **Migration:** new file in `migrations/versions/` (linear chain, never edit applied ones);
  apply on Supabase only (`docs/ops.md`); patch local sqlite by hand if needed for tests.
- **View:** `renderX(app)` in `frontend/js/<view>.js` (guards → paint → wire → ads);
  route entry in `app.js` (**`'/'` LAST**); script tag in `index.html` if new file;
  add to `sw.js` `STATIC_ASSETS`.
- **Push/ads/tiers:** follow existing patterns in `notifications.js`/`upgrade.js`;
  free tier degrades gracefully (`.catch(() => null)`), Pro gates server-side.

## Pre-push checklist
- [ ] `node --check frontend/js/*.js frontend/sw.js`
- [ ] `python tools/audit_ui.py` (clean) + spec updated if UI/methodology touched
- [ ] `python -m tests.test_final_all` in parity (only expected 400/404)
- [ ] New/changed tests for new behavior (`tests/README.md` runner patterns)
- [ ] **`CACHE_VERSION` bumped** if any cached static file changed (rule 04/10)
- [ ] Migration file included if models changed (never run it locally)
- [ ] Commit scoped (docs / tests / attic / feature separately); push `main` → Render deploys

## Repo hygiene
- Nothing deleted: obsolete → `tests/attic/`, `tools/attic/`, or `attic_*` prefix + README row.
- Pendings live in `RETOMAR.md` (user decision). Session notes appended per work session.
- Never commit: `.env`, `*.db`, cookies/tokens, VAPID keys (see `.gitignore`).
