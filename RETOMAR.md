# SwimCoach — Retomar después (guardado 17/09/2026)

## Dónde abrir
- App local: `http://localhost:8000` (frontend + API mismo origen)
- Docs API: `http://localhost:8000/docs`
- Salud: `http://localhost:8000/api/health`
- Arrancar: `cd "C:\Users\mocon\OneDrive\swimcoach"; .\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000`
- Detener: `Stop-Process -Name python`

## Estado: críticos UI terminados y verificados
1. Nuevos `frontend/js/login.js`, `register.js`, `utils.js`; `index.html` carga 12 módulos en orden.
2. `api.js` → `getMacrocycle()` usa `/plan/macrocycle`.
3. `sw.js` v1.0.1: sin `competition.js` fantasma, incluye login/register/settings/utils.
4. `app.js`: router sin loops, redirect `?step=4`, AdSense con llaves corregidas.
5. `onboarding.js`: steps numéricos + alias texto, fechas locales, validación anti-422.
6. `session.js`: tabs null-safe, `completeSession()` llama a la API.
7. `macrocycle.js`: `<h2>` cerrado, volumen con perfil real, `viewWeek()` → `#/session?date=`.
8. `feedback.js`: paginación `window._fb`, Load More real, XSS-safe, exports globales.
9. `profile.js`: sin ID duplicado, highlight en checkboxes, export por helper.
10. `settings.js` / `upgrade.js`: export compartido, portal y cancel implementados.
11. `backend/routes/plan.py`: eliminado duplicado `POST /api/plan/competition/generate` (vive en `competition.py`).
12. Bonus: `APP SWIM/Maincode.py` `_main_` → `__main__`.
- UI en inglés (decisión del usuario). Rediseño minimalista acuático: pendiente, fase 2.

## Verificación
- `node --check`: 13 JS + SW OK.
- `test_final_all.py`: 14 PASS. 2 "FAIL" esperados (portal 404 y cancel 400 en usuario no-Pro).
- `TestClient GET /` → 200 HTML; `/api/health` ok; `/js/app.js`, `/manifest.json` 200.

## Pendiente (tarde): fusión con la otra app
- Usuario pasará archivos de app similar (aún no local).
- Le gusta: el DISEÑO UI de la otra. Meta: FUSIONAR antes de usar.
- Flujo acordado:
  1. Recibir ruta/adjuntos + 2-3 pantallas favoritas.
  2. Comparativa visual (conservar lógica SwimCoach, traer estilos).
  3. Plan de fusión por archivo y aplicar solo con visto bueno.
- Para retomar, decir: "retomamos la fusión".

## Deploy (18/09/2026, plan gratuito $0)
- Repo: https://github.com/dado-droid-666/swimcoach (main)
- Plataforma: Render Web Service plan Free (manual, NO Blueprint).
- DB: Supabase `atypoclonwaxvukwvycy` (directa 5432). Tablas SwimCoach creadas:
  users, athlete_profiles, competition_goals, macrocycle_plans,
  training_sessions, strength_sessions, daily_feedback (+ alembic_version).
  Conviven sin colisión con las de entrenamiento-app.
- Alembic: migración inicial vacía (el esquema lo crea `init_db()` al arrancar).
  Fix aplicado en `migrations/env.py` (escape `%` para passwords con `%3F`).
- `requirements.txt`: + `psycopg2-binary==2.9.10` + `alembic==1.13.2`.
- Pendiente usuario en Render: crear Web Service Free (Build:
  `pip install -r backend/requirements.txt`, Start:
  `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`), pegar env vars
  (DATABASE_URL Supabase, SECRET_KEY, ENVIRONMENT=production, FRONTEND_URL,
  MP x4, AdSense x3). Migración futura a DB paga = cambiar 1 variable.
