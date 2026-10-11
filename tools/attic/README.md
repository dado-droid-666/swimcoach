# tools/attic/ — archived one-offs (moved from root 2026-10-11, Session B)

Nothing here runs in CI or prod. Kept for history; do not extend.

| File | Why archived |
|---|---|
| `check_tables.py` | Local sqlite table lister; superseded by `alembic current` + Supabase dashboard. |
| `generate_icons.py` / `generate_icons_simple.py` | One-shot PWA icon generators (need `cairosvg`); icons already in `frontend/assets/icons/`. |
| `cookies.txt` | Curl Netscape cookie file from manual API probing. **Never commit cookies/tokens again** (now in `.gitignore`). If it held a real session, assume expired; rotate if unsure. `deploy.sh` referenced it for local curl tests. |
| `railway.toml` | Railway deploy config; dead — prod deploys on **Render** via `render.yaml` + dashboard autod deploy. |
| `.env.production.example` | Superseded by the unified `.env.example` (dev defaults + commented prod values in one file). |
| `deploy.sh` | Multi-target (local/docker/railway/render) bash helper; stale paths (root `test_final_all.py`, railway CLI). Local flow now lives in README/CONTRIBUTING runbooks. |
