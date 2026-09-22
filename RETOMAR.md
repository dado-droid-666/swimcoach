# SwimCoach — Retomar después (guardado 21/09/2026 noche)

## Producción
- LIVE: https://swimcoach-ss5j.onrender.com (plan Free + Supabase pooler 6543).
  Nombre del sitio se queda así (decisión usuario).
- Repo: https://github.com/dado-droid-666/swimcoach (main, todo pusheado).
- Cuenta real del usuario existe; perfil reparado (swim 2→3).

## Sesión 18-19/09 — todo lo hecho (commits viejos → nuevos)
- Restyle dark oceánico + bottomnav + olas + player con timer/RPE modal.
- Fase A ML cliente: tier_model/load_model/trees + JSONs, CSS test en
  onboarding (tier APLICA level + escala volumen), badge + ritmo en dashboard,
  factor ML suave en player.
- AdSense real: `ca-pub-4540036176937342`, banner `7276396302`,
  contenido `2885278049` (meta de verificación puesta).
- Pro a **$100 MXN/mes** (backend MXN + upgrade.js). Free trial 1 mes intacto.
- Equipo: metronome (sets ritmo + SPM), kettlebell_general + trx_general,
  mezcla round-robin por implemento + rotación semanal, split A/B/C
  (A=Pull+Core TRX, B=Legs+Hips KB, C=Stamina BW).
- Metodología v2: `css_zones.py` Z1-Z5 + SPM + guardarraíles, retest CSS 6sem
  en dashboard, `PROGRESSION.md`, `drill_library.json` + bloques en warmup.
- Fuerza: tope 4 flexible (Base/Build 4, Peak 3, Taper 1, Race 0), respeta
  pedido (`min`), solape AM/PM sin marca.
- Bugs prod corregidos: pooler IPv4 (gratis no habla IPv6), bcrypt==4.0.1,
  mp_webhook_secret default "", focus VARCHAR(50) (migración 7f3a2b1c9d4e),
  profile antibrick (límites Update + 422 claro + rangos frontend),
  fallback updateCompetition en 400, pills un tap (pillClick + :has),
  saveStepData sin FormData + dedup back/next, endpoint macrocycle.
- Modelo 1 reentrenado con datos reales: ancla PLOS 2025 (9369 marcas) +
  priors youngSwimmers (121) + export anonimizado con consentimiento ES+EN
  (`CONSENTIMIENTO.md`, `sql/004` pendiente de aplicar por el usuario).
  JSON `rf_v1_2026-09-18` desplegado en SwimCoach y entrenamiento-app.

## Sesión 19/09 día — navegación + Pro mover/regenerar (`3808502`)
- Vista semana Lun-Dom (`#/week`, `js/week.js`): badges por día, prev/next
  semana, tap→sesión; bottomnav Plan→semana; macrocycle week-bars→semana.
- Sesión: prev/hoy/next día, link a semana, tarjeta rest-day con cercanas
  ±14d; fechas 100% locales `en-CA` (adiós desfase UTC).
- Navbar centrado 520px; móvil sin links arriba (bottomnav manda).
- Pro: `PUT /api/plan/session/move` (409 si choca, 404 si no existe) +
  `POST /api/plan/week/regenerate`; UI drag & drop + tap-to-move + botón
  regenerar con confirm; free→upgrade. Verificado: 403/200/409/404/regen OK.
- SW v1.0.5.

## Sesión 21/09 — navegación, Pro mover, tour, logs, fixes finos (`a0c36f9`)
- Semana Lun-Dom + prev/next día + fechas locales + rest-day con cercanas.
- Navbar 860px; bottomnav compacto; topbar week con aire.
- Pro: mover (drag + modo ✥ Move con tap) + regenerar semana; free→upgrade.
- Tour guiado (spotlight scroll-then-measure + pulso + fallbacks) + ? Guide.
- `exercise_logs` (migración b2c3d4e5f6a7 en Supabase): modal por ejercicio,
  effort obligatorio free / skip Pro; historial en feedback.
- Week-bars con ancla exacta (W-6→21sep, W-3→12oct verificado).
- Cuenta usuario: daniel.alvarado4@gmail.com (id 2), plan 6 sem 21sep→30oct.
- SW v1.0.6. Tests 14 PASS (400/404 esperados).

## Pendiente del usuario (con sus cuentas)
1. Crear cuenta real + flujo completo en prod (perfil ya reparado).
2. `npx supabase db push` (004 consentimiento) + `netlify deploy --prod`
   en entrenamiento-app.
3. Plan Pro $100 MXN manual + webhook en mercadopago.com.mx cuando venda
   (hoy: checkout funciona, webhook vacío, plan auto).
4. Revisar aprobación AdSense del sitio.
5. Confirmar FRONTEND_URL = https://swimcoach-ss5j.onrender.com en Render.

## Para retomar
- Servidor local: `cd "C:\Users\mocon\OneDrive\swimcoach"; .\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000`
- Tests: `.\venv\Scripts\python.exe test_final_all.py` (14 PASS; 400/404 esperados)
- Migraciones Supabase: `$env:DATABASE_URL="<pooler URI>"; python -m alembic upgrade head
- Esquema decisiones: inglés, dark oceánico, acento aqua #3fd0e6, ML aplica
  (tier→level, factor→reps), retest único CSS,KB/TRX plantilla general.
