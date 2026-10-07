# SwimCoach — Retomar después (actualizado 30/09/2026)

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

## Sesión 23/09 — idempotencia, días, CSS persistente, volumen (`e2618cb`)
- Generate idempotente (borra plan previo) + botón con lock + 163
  duplicados limpiados en Supabase (users 3 y 4).
- Días Lun=0…Dom=6 en onboarding + profile (domingo ya no colisiona).
- `swim_tests` (migración c3d4e5f6a7b8 en Supabase): guarda test al
  completar, precarga en paso 1, dashboard lee servidor. Ojo gotcha Python:
  `date: Optional[date]` se auto-sombrea → campo `test_date`.
- Volumen: estimado en vivo en paso 1 + aviso sobre tope (12k/16k/25k);
  todo múltiplo de 25 verificado (reps×dist, sets, totales).
- Conteos exactos: días entreno == días nado; fuerza vacío/auto o exacto.
- Logout visible (profile + settings) + fix rebote post-Generate (recarga
  estado antes del dashboard).
- Cuentas prod: moconette (id 3,temporal Temporal-1234 puesta y verificada),
  daniel (id 4, OW 28feb2027). Debug users borrados.
- Tests 14 PASS (400/404 esperados). SW v1.0.6.

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

## Sesión 26-27/09 — Salo + planes adaptativos (commits b4adb5c, 4076fb4, 30716b1)
- Clon local: `C:\Users\mocon\OneDrive\Documentos\APP SWIM\swimcoach`
  (venv local con deps modernas solo para tests; prod usa Dockerfile py3.13;
  en local NO instalar psycopg2, usar sqlite o psycopg v3).
- Libro Salo integrado: `data/salo_swim.json` (MIX EN1/EN2/SP por
  pool_sprint/mid/im/distance + ow_short/long/ultra, recovery, tecnica_ch1)
  y `data/salo_dryland.json` (core/power/prehab/flex/warmup). Taper 2 +
  Race 1 fijas (ya existían). `get_event_category()` intacto.
- Fuerza mix: plantillas TRX/KB/BW/bands + splits A/B/C intactos; se mezcla
  core/power/prehab/flex Salo (`strength_generator.py`). Youth <14 sin power
  con peso (nuevo campo perfil `edad` + migración d4e5f6a7b8c9). Prehab Ch8
  si feeling<=2 o injury_notes con hombro/rodilla.
- Planes vivos: `adaptive_state.py` (feeling min nado+fuerza, adherencia,
  perdidas contadas SIN reapilar volumen, esfuerzo+trend) + `load_model.py`
  (M2 en servidor con `frontend/ml/modelo2_bosque.json`, clamp ±25%,
  fallback conservador; sin historial manda 1.0). `POST /competition/generate`
  aplica estado solo semana actual/futuras; `POST /plan/week/regenerate`
  regenera la semana en foco con estado completo. Schemas/API/frontend de
  sesiones intactos.
- Descripciones visibles en lenguaje simple (sin EN/SP/Ch): `notes` de ambos
  JSON reescritos; `fuente_pag` + MIX quedan en datos/snapshot.
- Días: sesiones ancladas al lunes dentro de cada bloque de 7 días
  (generadores normalizan `week_start`; antes `inicio_bloque + offset`
  corría todo si el bloque no empezaba en lunes). Regenerate ya recibía lunes.
- Frontend: campo `edad` en onboarding (viene de `ath_age`) + profile;
  aviso "¿Ajustamos la semana?" en `week.js` (≥2 perdidas o feeling≤2,
  llama al regen existente, nunca bloquea).
- Migraciones nuevas aplicadas en Supabase (head `e5f6a7b8c9d0`):
  d4 `edad` en athlete_profiles + e5 `focus`→String(100) en ambas tablas
  (los sufijos Salo pasaban VARCHAR 50 en Postgres; SQLite no valida).
- Tests nuevos: `test_salo_mix.py` + `test_adaptive.py` 18/18 PASS.
  E2E `test_final_all.py` igual que baseline (fallan solo 3 esperados).
  Lección: correr siempre `alembic current` en prod tras push con migración;
  probar generate contra Postgres, no solo sqlite.
- ML retrain: `backend/scripts/export_training_data.py` (CSV anonimizado
  para M1/M2 con datos reales cuando haya historial). Entrenamiento sigue en
  entrenamiento-app-cuentas/ml. `technique_flag` Ch1 pendiente: SwimTest no
  guarda stroke count.
- OJO seguridad: el password del pooler se expuso en un chat el 27/09 —
  el usuario lo rotó (verificar que DATABASE_URL en Render quedó con el nuevo).
- Estado al 27/09 noche: deploy `30716b1` live; usuario hizo "Start new plan"
  (borró competition+plan, perfil/feedback intactos) y el onboarding Generate
  se colgó por reinicio de Render a mitad (04:45). PENDIENTE INMEDIATO:
  onboarding → Generate 1 vez (~60s) → verificar nado Mar/Sáb/Dom +
   fuerza Lun–Jue, Peak con SP, Taper sin SP, prehab donde toque.

## Sesión 30/09 — AdSense aprobación + verificación prod (`782ba5c`)
- `frontend/ads.txt` creado (`google.com, pub-4540036176937342, DIRECT,
  f08c47fec0942fa0`); servido en `/ads.txt` vía StaticFiles. Verificado live.
- Páginas públicas nuevas `frontend/js/public.js`: `#/` landing con contenido
  real (cómo funciona, CSS zones, strength, FAQ, 1 banner) + `#/privacy`
  (cláusula AdSense/cookies, opt-out, derechos, contacto) + `#/terms`
  (Pro $100 MXN, liability natación, leyes México). Sin login → crawler OK.
- Router `app.js`: rutas `/`, `/privacy`, `/terms` públicas; default `#/` si no
  hay sesión; bottomnav oculto en públicas; `renderLanding` redirige a
  dashboard si ya hay usuario.
- Fix anuncios: eliminado `div#ad-banner` duplicado oculto de `index.html`;
  CSS `#ad-banner`→`.ad-banner`; vistas usan `class`; `pushUnfilledAds()`
  (solo `ins:not([data-ad-status])`, delay 100/300ms) en dashboard/session/
  feedback/landing. Antes session/feedback nunca hacían push (vacíos).
- Footer con Home/Privacy/Terms/Contact (`swimcoach.app@gmail.com` —
  cuenta real del usuario, verificada 04/10: recibe correos OK).
- Verificación prod 30/09: `/api/health` ok, `/ads.txt` correcto,
  `/` + `/js/public.js` nuevos live, head Alembic local `e5f6a7b8c9d0`.
  Usuario confirmó Generate OK (nado Mar/Sáb/Dom + fuerza Lun–Jue).
- Usuario solicitó revisión AdSense el 30/09. No clicar anuncios propios.
  Si rechazan, corregir según motivo exacto.

## Sesión 30/09 noche — SW v1.0.8 + stroke count Ch1 (`b029d6a`)
- `frontend/sw.js` → `v1.0.8` + `/js/public.js` al cache (PWA no sirve viejo).
- `register.js`: consentimiento con links Terms/Privacy.
- Stroke count cerrado: migración `f6a7b8c9d0e1` (`stroke_count_50m` en
  swim_tests) + schema 20-120 + ruta + campo onboarding paso 1 (prefill,
  guardado). `adaptive_state`: ≥50 brazadas/50m → `technique_flag=True`,
  generador agrega sets Ch1 drills+DPS (verificado 58→True, 40→None).
- Tests: 5 adaptive + 13 salo OK; E2E paridad baseline (400/404 esperados).
- PENDIENTE USUARIO tras deploy: `alembic upgrade head` en Supabase/Render
  (head `f6a7b8c9d0e1`) + `alembic current`. NO correr alembic en sqlite
  local (sello viejo `b2c3`, falla; dev usa create_all + ALTER manual).

## Incidente 04/10 — router tragaba todas las rutas (`0f66228`, SW `9f4972c`)
- Causa: landing `'/'` primera en tabla `routes` + match por prefijo
  (`startsWith`) → TODA la app renderizaba landing; login/register
  inalcanzables, taps "muertos", sin POST en logs. Gemelo en `updateNav`
  (`startsWith('#/')` ocultaba bottomnav siempre). Introducido en cambio
  AdSense del 30/09.
- Fix: `'/'`, `'/privacy'`, `'/terms'` al final de `routes`; `'#/'`
  exact-match en `updateNav`. Verificado con simulación (8 rutas OK).
- Lección PWA: el fix estuvo live pero el SW `v1.0.8` seguía sirviendo el
  `app.js` roto desde cache (sw.js sin cambios → navegador no actualiza).
  Bump a `v1.0.9` para forzar refresh. REGLA: todo cambio de JS cacheado
  (`app.js` y cía.) exige bump de `CACHE_VERSION` en `sw.js`.
