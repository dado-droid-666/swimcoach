# SwimCoach Programming Rules (metodología v2)

Aprobada 18/09/2026. Referencia de ejemplo: `data.js` de entrenamiento-app
(bloques con drills, split A/B/C). Fuentes abiertas (link, no copia):
goswimfast, phase.fitness, PoinT GO, LiftStrong, Swimming Science,
SwimSwam SURGE, Faster Swimming, TrainingZones.io, TritonWear, SportPlan,
MyProCoach, SwimmingRegimen. Fases: las 5 inglesas (Base→Build→Peak→
Taper→Race). Benchmark único: CSS (retest cada 6 semanas).

## Natación — zonas CSS ×5 (`backend/services/css_zones.py`)
- Z1 Recovery (115-130% CSS, RPE 2-3, 50-55 SPM): warm-up, cool-down, técnica.
- Z2 Endurance (105-115%, RPE 4-5, 55-60 SPM): base aeróbica.
- Z3 Threshold (95-105%, RPE 6-7, 60-65 SPM): sets @CSS.
- Z4 VO2max (85-95%, RPE 8-9, 65-70 SPM): intervalos duros.
- Z5 Sprint (75-85%, RPE 9-10, 70+ SPM): velocidad, salidas.
- Guardarraíl semanal: Z1-Z2 70-80%, Z3 15-20%, Z4-Z5 5-10%.
- Cada set lleva `css_zone` + `target_spm`; con metrónomo, Z4/Z5 (o marcado)
  suma `stroke_rate_spm` + nota de tempo trainer.
- Ancla CSS = FTP del perfil, o estimado Z3 por nivel si no hay FTP.

## Fuerza — consenso por fase (sin hipertrofia: el músculo extra es drag)
- Base: 8-12 reps adaptación general + core + hombro cada sesión.
- Build: 4-6 reps max strength; rotación semanal del orden (conjugado-lite)
  para variar el estímulo.
- Peak: 2-4 reps power en superset fuerza+velocidad; sin pierna pesada 24h
  antes de velocidad; mantener intensidad, bajar volumen.
- Taper: movilidad corta 1-2 sesiones; Race: nada. Accesorios se recortan
  primero (14 días fuera), intensidad al final, volumen fuera (~7 días).
- Split A/B/C por días disponibles (A tracción+core/TRX, B pierna+cadera/KB,
  C stamina); mezcla round-robin por implemento propio (bands/KB/TRX).
- Orden en sesión: skill → speed → strength → conditioning.

## Progresión y mejora medible
- Volumen swim +5-10%/semana por fase; deload 4ª semana −30%.
- RPE>4 dos sesiones seguidas → repetir semana (Modelo 2 ±25% + fallback).
- Benchmark único: CSS cada 6 semanas (prompt en dashboard); historial en
  `swimcoach_tier_v1` local; progreso = CSS más rápido.
- Modelo 1 calibra level + volumen base; Modelo 2 ajusta carga de fuerza.
