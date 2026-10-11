# frontend/ — PWA shell (vanilla JS SPA, no build step)

- `index.html` — shell regions (navbar → `#app` outlet → bottomnav → overlays → footer). Styles: `pico.min.css`, then `style.css` (legacy), then `css/tokens.css` (canonical, loads last).
- `js/app.js` — router (hash routes; `'/'` LAST, `'#/'` exact-match — see docs/specs/patterns.md) + global state.
- `js/api.js` — fetch wrapper (no timeout; 401→login redirect).
- `js/*.js` — one global per view: `renderX(app)` paints `#app.innerHTML`, then wires events, then `refreshAds` (free tier).
- `sw.js` — cache-first `STATIC_ASSETS`. **RULE: any change to a listed file needs a `CACHE_VERSION` bump in the same commit**, and new static files must be added to the list.
- `ml/` — client ML JSONs (M1 tree, M2 forest fallback); server M2 lives in `backend/services/load_model.py`.
- UI source of truth: `docs/specs/` (principles, tokens, components, patterns). No new color literals outside `css/tokens.css` (audit fails CI).
