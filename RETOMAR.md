# SwimCoach — Retomar después (actualizado 15/11/2026)

## Producción
- LIVE: https://swimcoach-ss5j.onrender.com (plan Free + Supabase pooler 5432, session).
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
- Pro a **$100 MXN/mes** (backend MXN + upgrade.js), recurrente en MercadoPago.
  Sin free trial: el primer cobro es al autorizar el checkout (decisión 15/11).
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
- Cuentas prod: moconette (id 3, temporal puesta y verificada; valor redactado
  20/10 — rotar y no volver a escribir contraseñas en el repo),
  daniel (id 4, OW 28feb2027). Debug users borrados.
- Tests 14 PASS (400/404 esperados). SW v1.0.6.

## Pendiente del usuario (con sus cuentas)
1. Crear cuenta real + flujo completo en prod (perfil ya reparado).
2. `npx supabase db push` (004 consentimiento) + `netlify deploy --prod`
   en entrenamiento-app.
3. MercadoPago: configurar en Render `MP_WEBHOOK_SECRET` + `BACKEND_URL` y
   registrar el webhook; probar sandbox con credenciales TEST antes de cobrar.
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

## Incidente 07/10 — Generate muerto tras validación (`resetGenBtn`, SW `v1.1.0`)
- Causa: `completeOnboarding` ponía `window._generating=true` pero los 4
  `return` de validación salían sin liberarlo → todo tap posterior moría en
  silencio (`if (window._generating) return`), cero tráfico al servidor.
  Reconstruido con logs Render (reset 200, ni un POST /competition/generate).
- Fix: helper `resetGenBtn()` (flag + botón) en los 4 returns + `.finally()`
  reutilizándolo. Test Node con stubs DOM: T1/T2 validación libera flag y
  rehabilita botón; T3 retry tras fallo llega al servidor y cae en dashboard.
- Migración f6 aplicada por el usuario en Supabase (`e5→f6`, head OK).

## Sesión A (AI-ready, art. Smashing) — specs + tokens, cero visual
- `docs/specs/`: principles, tokens, components, patterns, training (espejo
  backend) + `docs/llms.txt` índice interno. `frontend/css/tokens.css` set
  cerrado (paridad 28/28 con mirror legacy verificada por script).
- `index.html` carga tokens.css; SW `v1.1.1` (+tokens en STATIC_ASSETS).

## Sesión B (orden físico) — tests/ + attic (`0a5555a`, `ab2fee6`)
- 14 `test_*.py` raíz → `tests/` (vivos: final_all, adaptive, salo_mix) y
  `tests/attic/` (11 obsoletos) + READMEs; suite vía `python -m`
  (`tests/__init__.py`); paridad E2E verificada antes/después.
- Raíz → `tools/attic/` + README (check_tables, generate_icons×2,
  cookies.txt, railway.toml muerto, deploy.sh); `cookies.txt` a `.gitignore`
  (era cookie real commiteada — asumir expirada; no repetir).
- `backend/jobs/` (vacío) eliminado; `ads_service.py` → `attic_ads_service.py`
  con nota (frontend usa IDs hardcodeados); `frontend/README.md` del shell.
- Local sqlite parchado a mano (edad, stroke_count_50m, is_admin) — documenta
  deriva dev (create_all vs migraciones); nunca alembic en local.
- PENDIENTE Plan B passwords: `models.py` is_admin + migración `g7` en
  working tree SIN commit (retomar pasos 2-5 aprobados).

## Sesión C (higiene + auditoría + CI)- `.env.example` unificado (dev + prod comentado); `.env.production.example`
  → `tools/attic/`; `render.yaml` comentado var por var (solo comentarios;
  OJO: declara Render DB pero el live es Supabase pooler vía dashboard).
- `docs/ops.md`: runbooks (migración, admin, reset, wake) + tests/CI.
- `tools/audit_ui.py` estricto + `audit_baseline.txt` (68 grandfathered):
  color fuera de tokens, console, dup-id, ad-label/client. Cazó bug real en
  desarrollo: `.strip()` se comía el espacio final de la clave → fix con
  `rstrip()` en `key_of`. Probado: pasa en limpio, falla con `#deadbe` nuevo.
- `tools/audit_spec.py`: diff-based, buckets UI→specs / training→training.md.
- `.github/workflows/ci.yml` non-blocking: node --check, audits, alembic
  heads (single head), units, E2E sqlite.

## Quick wins 26/10 — grid + errores inline (commit siguiente)
- Grid: `.onboarding-container .grid, .profile-view .grid` a 1 columna
  (labels arriba, inputs full-width; fin del truncado "Intermediat…").
- `.field-error` + `show/hideFieldError` (utils.js): login/register/
  change-password muestran error de credenciales bajo el campo; resto al toast.
- Test stubs login: T1 credenciales→inline sin toast, T2 red→toast sin inline.
- SW `v1.2.0` (login/register/settings/style/profile cacheados).

## Plan B passwords — ejecutado (commit pendiente de push con el resto)
- Migración `g7b8c9d0e1f2` (`users.is_admin`) + `require_admin` + schemas
  (`PasswordChange`, `AdminResetRequest/Response`) + `POST /auth/change-password`
  + `POST /auth/admin-reset-password` (temp 12 chars `secrets`, se muestra 1 vez).
- Frontend: `api.changePassword` + sección en Settings + SW `v1.1.2`.
- `tests/test_password.py`: 13/13 PASS (OK/401/422/anon/403/temp/404);
  E2E en paridad; audit_ui OK.
- PENDIENTE USUARIO post-deploy: `alembic upgrade head` (→`g7b8c9d0e1f2`) en
  Supabase + `is_admin=true` propio + probar change y reset.

## Push Fase 1 técnica (infra, sin scheduler)
- Migración `h8c9d0e1f2a3`: `push_subscriptions` + `reminder_time/tz` en perfil
  (hora configurable modelada ya; scheduler en Fase 2).
- `routes/notifications.py`: vapid-key (pública), subscribe upsert, unsubscribe,
  test solo-admin (404 sin subs → 503 sin VAPID). `pywebpush` en requirements.
- SW: handlers `push`/`notificationclick` (→`#/session/today`).
- Settings: toggle real con estados (On/Off/Blocked/Unsupported) + `api.js`.
- `tools/gen_vapid.py` (keys nunca en git); `tests/test_notifications.py` 16/16
  (cazó orden 404/503 + cookie-jar en asserts anón).
- Bug real tras `failed:1` mudo: `pywebpush==1.14.0` incompatible con
  `cryptography` moderno (`TypeError: curve must be an EllipticCurve
  instance` en `encode()`; reproducido local con traceback). Fix: bump a
  `pywebpush==2.5.0` (send path verificado hasta red con endpoint falso).
- Local sqlite parchado a mano (reminder_*; deriva documentada).
- PENDIENTE USUARIO: generar VAPID (`tools/gen_vapid.py`) → envs Render+local
  → toggle en Settings → `POST /notifications/test` como admin.

## Títulos escalados (bug 2 fotos: título libro vs contenido escalado)
- `summarize_set` + `apply_scaled_description`: `description` = lo que se nada
  ("40×25m freestyle"), libro intacto en `method`; sin dígitos no se toca.
- Vista: título escalado + subtítulo `method`; player: título escalado,
  desc = `method`. Planes viejos sin campos → fallback idéntico a hoy.
- `SetSchema(extra="allow")` deja pasar `method` (verificado generator→API).
- Test `test_titulo_escala_con_contenido` (14/14 salo); E2E paridad; SW `v1.3.1`.
- PENDIENTE USUARIO: regenerar plan y comparar con sus fotos.

## Cierre 26/10 noche — quick wins + saga push (aparcar)
- Quick wins prod (`54c7b71`, `e89a1ab`, SW `v1.2.1`): grid apilado onboarding/
  profile (fin truncado), `.field-error` bajo password en login/register/
  settings, login siempre-inline (todo fallo bajo el campo). Verificado por usuario.
- Push saga (Edge/Windows, endpoint WNS): TypeError→pywebpush 2.5.0; 400 vacío→
  TTL 86400 solo WNS (issue #162); instrumentación exc.message/keypair_match/
  endpoint_hosts/sub_keyfps/bare-mode. Display directo OK, permiso OK, keys OK.
- Hallazgo: `NO-SUB` en el perfil + 4 filas stale (subs 4-7); viva sub 8 con fp
  `912842796ee496e0` vs server sub 7 `27f8b1c24df02eb5` (mismatch confirmado).
  `sent:2` pero sin mostrar → pendiente comparar tras toggle fresco.

## Push Fase 2 — scheduler (Render Cron $1/mes)
- Migración `h9` (`reminder_last_sent` DATE, dedup persistente) + `reminder_time/tz`
  validados en schemas (`HH:MM`, IANA) + `CRON_SECRET` en config.
- `POST /dispatch-due` (secreto constant-time): ventana 30min por tz de usuario,
  1/día, descanso omitido, mensaje del plan de hoy, retry en siguiente tick.
- Settings: time-picker (reloj + 21 zonas + auto-detect) vía `PUT /profile`.
- `tests/test_dispatch.py` 11/11; E2E paridad; audit_ui OK; SW `v1.4.0`.
- HECHO 20/10: `h9d0e1f2a3b4` aplicada en Supabase. PENDIENTE USUARIO:
  `CRON_SECRET` en Render + crear Cron Job `*/15` → trigger manual → push real.
- PENDIENTES MAÑANA: (1) re-test push + comparar huellas → podar stale
  (`DELETE push_subscriptions` menos la viva) → cerrar Fase 1; (2) veredicto
  fotos títulos; (3) reintento AdSense → trigger Starter si falla; (4) push
  Fase 2 (scheduler) y plan C email cuando se pida.

## 20/10 — 500 al crear plan = schema drift h9 + hardening
- **Causa:** el código de Fase 2 (SW `v1.4.0`) se desplegó el 14/10 con
  `reminder_last_sent` en el modelo, pero Supabase seguía en `h8`. Cualquier
  SELECT de `athlete_profiles` daba 500 (`UndefinedColumn`). `loadProfile()`
  se tragaba el error → mandaba a onboarding → `PUT /profile` volvía a 500.
  Afectó a **todas** las cuentas; moconette solo fue la que intentó un plan.
- **Fix inmediato:** `alembic upgrade head` en Supabase (`h8`→`h9`), sin
  redeploy. Sin borrar datos: `generate` reemplaza el plan parcial al reintentar.
- **Hardening (`tests/test_generation_safety.py`, 11/11):**
  generación atómica (construye todo en memoria → delete+insert+commit único;
  si falla, rollback conserva el plan anterior), normalización de perfiles
  legacy con NULL (`_profile_snapshot`), `api.js` adjunta `status`/`data`,
  `app.js` muestra pantalla de reintento en 500 (nunca onboarding falso),
  regla migration-first en README/CONTRIBUTING/ops, SW `v1.4.1`.
  Commits `186c329` + `1ee89e0`; deploy verificado (SW `v1.4.1` en prod).
- **CERRADO 20/10:** h9 aplicada, moconette generó el plan y aparece completo.
  Queda rotar la contraseña temporal de moconette (el valor viejo sigue en el
  historial de git; el archivo ya está redactado).

## 20/10 — Main set incoherente (8x50+4x25 vs 10x100)
- **Causa:** `scale_set_meters` escalaba reps **y** distancia; un set de libro
  de 500m (`8x50 @95% + 4x25 salidas`) se convertía en `10×100m` (1000m).
  `method` conservaba el texto original sin escalar y `session.js` lo pintaba
  en cursiva como si fuera una segunda prescripción. El header sumaba los
  `meters` escalados, pero la tarjeta mostraba dos recetas distintas.
- **Fix:** `data/salo_swim.json` ahora tiene `segments` explícitos en los 16
  sets compuestos; `scale_set_meters` escala reps/minutos y **nunca cambia la
  distancia** (`8x50 + 4x25` a 2× → `16×50 + 8×25 = 1000m`). `description` se
  reconstruye desde los segmentos; `method` queda solo como provenance y ya
  no se renderiza ni en la tarjeta ni en el player. `total_meters` de sesión =
  warmup + main real + cooldown. SW `v1.4.2`. Commit `2c1453d`; deploy
  verificado (SW `v1.4.2` en prod).
- **Tests:** `test_salo_mix` (integridad de los 16 sets, escalado exacto,
  descripción por segmentos, todas las categorías/fases, UI sin `method`);
  `test_generation_safety` 13/13; E2E `Generate macrocycle: 201`; audit_ui OK.
- **CERRADO 20/10:** moconette regeneró el plan y confirmó que el set muestra
  la estructura del libro (p. ej. `16×50m @95% + 8×25m starts`), con `Set
  total` y header sumando lo mismo. Sin pendientes de este incidente.

## 13/11 — Supabase pausado (500 en dispatch) + cron Fase 2 configurado
- **Síntoma:** `POST /api/notifications/dispatch-due` con secreto correcto
  devolvía 500; con secreto incorrecto, 401. `/api/health` seguía 200 porque
  no consulta la DB (engañoso en caídas de base).
- **Causa:** proyecto Supabase `atypoclonwaxvukwvycy` pausado por inactividad.
  Dominio NXDOMAIN; pooler `FATAL: (ENOTFOUND) tenant/user ... not found`
  (puerto 5432). Afectaba login/perfil/planes, no solo el cron.
- **Fix:** el usuario restauró el proyecto desde el dashboard de Supabase;
  datos conservados. `database.py` ya tenía `pool_pre_ping=True`, no hizo
  falta reiniciar Render. Verificado: login OK y dispatch
  `200 {"checked":2,"sent":0,"skipped":2}`.
- **Cron Fase 2:** `CRON_SECRET` en Render + cron-job.org cada 15 min, método
  POST, header `X-Cron-Secret`, timeout 30 s. Test run 200. El ping mantiene
  Render y Supabase activos, así que evita otra pausa por inactividad.
- **OJO:** el `DATABASE_URL` de Render usa puerto `5432` (session pooler) y
  funciona, pero el estándar documentado del proyecto era `6543` (transaction
  pooler). **Decidido 15/11:** se deja `5432` (funciona; no tocar) y se
  actualiza la documentación. No fue lo que causó la caída.
- **Sin verificar aún:** push real end-to-end. `sent:0` fue por hora fuera de
  la ventana de 30 min (18:07 CDMX con recordatorio 07:00) o día de descanso.

## Plan para mañana — sábado 14/11
1. Cerrar Push Fase 1: toggle fresco, re-test, comparar huellas; podar
   suscripciones stale (`DELETE push_subscriptions` salvo la viva) y
   confirmar un push real a la hora configurada.
2. ~~Rotar password temporal de moconette~~ → resuelto 15/11: la temporal es
   nueva (no la expuesta en git).
3. ~~Revisar `DATABASE_URL` en Render~~ → resuelto 15/11: se deja `5432`
   documentado (session pooler; funciona).
4. AdSense: revisar estado/aprobación; si rechazaron, corregir el motivo.
5. MercadoPago: configurar `MP_WEBHOOK_SECRET` + `BACKEND_URL` en Render y
   probar sandbox (`TEST-`) antes de vender. Código ya corregido (ver 15/11).
6. entrenamiento-app: `npx supabase db push` (004 consentimiento) +
   `netlify deploy --prod`.
7. Confirmar `FRONTEND_URL` en Render =
   `https://swimcoach-ss5j.onrender.com`.
8. Hardening menor: `dispatch-due` debe devolver 401 (no 500) ante un header
   con caracteres no-ASCII (`hmac.compare_digest` sobre `.encode()` + test).
9. Opcional: limpiar los 68 avisos grandfathered de `tools/audit_baseline.txt`.

## 15/11 — Push Fase 1 cerrada (Chrome/FCM) + hardening health
- **Cron:** pasado de cada 15 min a **cada 10 min** para evitar la carrera con
  el spin-down de Render (15 min) y el timeout de 30 s de cron-job.org.
  Test run 200. El ping mantiene despiertos Render y Supabase.
- **DB:** `DATABASE_URL` sigue en puerto **5432** (session pooler); funciona y
  se deja así (decisión: no tocar lo que anda). `FRONTEND_URL`, `CRON_SECRET`
  y VAPID confirmados en Render.
- **Diagnóstico push Edge/WNS:** el servidor acepta los envíos
  (`sent:3, failed:0`) pero el SW de Edge no recibe **ni el bare**; el Push
  local de DevTools sí dispara notificación y recibo → SW y VAPID OK, el
  problema es la entrega WNS a ese perfil de Edge. No se sigue depurando.
- **Push Chrome/FCM:** resuscribir en Chrome, notificación recibida y
  `sent:1, failed:0` tras podar las suscripciones WNS (`fcm.googleapis.com`
  queda como única suscripción viva).
- **Recordatorio real:** pendiente de validar a la hora configurada (el test
  admin ya entrega; el scheduler está probado en unit tests).
- **Hardening código:**
  - `GET /api/health/db` nuevo: 200 `{"db":"ok"}` / 503 `{"db":"down"}`.
    `/api/health` queda liveness sin DB para el health check de Render.
  - `check_db_connection()` corregido (`text("SELECT 1")`; antes fallaba con
    SQLAlchemy 2.x).
  - `dispatch-due`: secreto comparado como bytes UTF-8; header no-ASCII
    devuelve **401** (antes `compare_digest` lanzaba TypeError → 500).
  - `tests/test_dispatch.py` ampliado (non-ASCII + health/db 200/503).
- **moconette:** resuelto 15/11 — el usuario confirma que la temporal que dejó
  como definitiva es **nueva** (no la expuesta en git). Se quita de pendientes.
- **AdSense:** aviso de incumplimiento de políticas; el usuario solicitó
  revisión el 15/11. Esperar ~2 días. Pendiente: capturar el motivo exacto y
  corregir `/privacy` y `/terms` (hoy 404 como URL directa; solo
  `/#/privacy` y `/#/terms`).
## 15/11 — MercadoPago Pro: flujo sin plan + webhook firmado
- **Flujo elegido:** suscripción **sin plan asociado** con pago pendiente.
  `POST /preapproval` (`auto_recurring`, `status=pending`) → `init_point`.
  Ya no se envía `preapproval_plan_id` (el setting queda ignorado) ni free
  trial; el primer cobro es al autorizar.
- **Bugs corregidos:**
  - Firma HMAC sobre el manifiesto real
    `id:<data.id>;request-id:<x-request-id>;ts:<ts>;` (antes HMAC del body).
  - Eventos reales `subscription_preapproval` /
    `subscription_authorized_payment` (antes `action` inexistentes).
  - Cancelación `PUT /preapproval/{id}` `{"status":"cancelled"}` (dos L; el SDK
    2.1.0 no tiene `cancel()` y su `update()` arma mal la URI).
  - `mp_preapproval_id` se guarda al crear el checkout (cancel/portal ya
    funcionan aunque el webhook llegue tarde).
  - Downgrade lazy al vencer `current_period_end` (solo canceladas).
  - `/api/subscription/webhook/test` → 404 en producción; portal `.mx`.
  - Mock de checkout solo con token placeholder, nunca con `TEST-` real.
- **Seguridad:** el webhook siempre re-consulta el recurso a MP y no confía en
  el body; sin secreto no se puede fabricar un Pro.
- **Tests:** `tests/test_subscription.py` 68/68 (firma, payload sin plan,
  webhook, cancelación, renovación, downgrade, mock dev).
- **Falta en Render (usuario):** `MP_WEBHOOK_SECRET` (MP → Your integrations →
  Webhooks → secret signature) y `BACKEND_URL=https://swimcoach-ss5j.onrender.com`.
  El token actual es `APP_USR-` (producción): **no hacer compras de prueba**.
- **Sandbox pendiente:** generar credenciales `TEST-` en MP y probar con
  usuarios de prueba antes de vender.

## 16/11 — MercadoPago sandbox: back_url, buyer y túnel

- **Causa del 400:** MP rechaza `http://localhost` y cualquier `back_url` con
  `#`. Se agregó `MP_BACK_URL` (HTTPS, sin fragmento); `back_url` se normaliza
  a `https://host/`. El frontend detecta `?preapproval_id=...`/`status=success`
  y enruta a `/#/upgrade` (el hash no puede ir en `back_url`).
- **notification_url:** solo se envía si `BACKEND_URL`/`FRONTEND_URL` es HTTPS;
  en local HTTP se omite y el webhook se simula con
  `POST /api/subscription/webhook/test`.
- **Token local:** es una cuenta de prueba (`/users/me` id 3844602243,
  `@testuser.com`, site MLM) aunque el prefijo sea `APP_USR-`. No es producción.
- **Comprador de prueba:** id 3844390477, usuario
  `TESTUSER7803872007605846304`; MP aceptó como `payer_email`
  `test_user_7803872007605846304@testuser.com`. Es distinto del collector
  3844602243. La contraseña está en MP → Cuentas de prueba (no se guarda acá).
- **Usuario local de prueba:** id 21, mismo email del comprador, perfil mínimo
  creado para que `/#/upgrade` no mande a onboarding.
- **Checkout:** `POST /api/subscription/checkout` devuelve 200 y crea un
  preapproval `pending` (`payer_id` 3844390477, `collector_id` 3844602243).
- **Túnel:** `cloudflared tunnel --url http://localhost:8000`; `.env` local
  apunta `BACKEND_URL` y `MP_BACK_URL` al host temporal del túnel. La URL cambia
  en cada arranque: si cambia, actualizar `.env` y reiniciar uvicorn.
- **Webhook local:** `MP_WEBHOOK_SECRET=` vacío para que el sandbox entregue
  notificaciones; el servicio igual re-consulta MP. En Render sigue pendiente
  configurar el `whsec_...`.
- **Tests:** `test_subscription.py` 78/78; regresión 13/21/15/13; E2E con
  `MP_MOCK_CHECKOUT=1` solo falla lo esperado (400/404). Sin mock, el E2E falla
  el checkout porque su email no es una cuenta MP real.
- **Limitación para producción:** MP exige `payer_email` (probado sin él:
  400 `payer_email is required`) y debe coincidir con la cuenta que paga. Antes
  de cobrar real, agregar un campo de correo MP en el perfil/upgrade o exigir
  el mismo correo; si no, usuarios con otro correo no podrán suscribirse.

## 16/11 (noche) — sandbox E2E: pago, webhook simulado y cancelación

- **Pago de prueba aprobado:** preapproval `b88509b73f0d49da8afa4c72a179e39d`
  quedó `authorized` (`payer_id` 3844390477, `collector_id` 3844602243), primer
  cobro de **100 MXN** aprobado (invoice `7034066102`, `processed/approved`);
  próximo cobro `2026-12-16T22:12:24-04:00`.
- **Webhook real:** no llegó al túnel quick de cloudflared (no se registró
  `notification_url` en el preapproval de prueba). Se sincronizó con
  `POST /api/subscription/webhook/test` → usuario `PRO/ACTIVE` hasta
  `2026-12-17 02:12:24`. La entrega real queda para validar en Render.
- **Bug de cancelación:** el código enviaba `{"status":"canceled"}` (una L) y
  MP respondía 400; el backend lo trataba como éxito. Ahora envía `cancelled`
  (dos L), ante un 400 re-consulta el recurso y solo acepta si ya está
  `cancelled`/`canceled`; los webhooks aceptan ambas grafías.
- **Cancelación verificada:** MP `cancelled`, local `PRO/CANCELLED` hasta
  `2026-12-17`; segundo intento responde 200 (idempotente).
- **Limpieza:** preapprovals `pending` de pruebas anteriores cancelados
  (`1edeacbc…`, `f9e0902e…`, `f07c6909…`, `7d283754…`).
- **Pendiente inmediato:** Render (`MP_WEBHOOK_SECRET`, `BACKEND_URL`, registrar
  webhook) y resolver `payer_email` para producción.

- **Pendiente:** MercadoPago (secret/`BACKEND_URL` + prueba sandbox),
  entrenamiento-app (`supabase db push` 004 + Netlify) y opcional limpiar
  baseline de `audit_ui`.
