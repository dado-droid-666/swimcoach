# Training methodology (backend mirror)

Source of truth for plan generation. Change a rule => update this file +
the generator in the same commit (sync rule).

## Event categories (`get_event_category`, Salo book MIX)
`pool_sprint / pool_mid / pool_im / pool_distance` + `ow_short / ow_long /
ow_ultra`, plus `recovery` and `tecnica_ch1`. Data: `data/salo_swim.json`
(MIX EN1/EN2/SP per event, Ch3/Ch4), `data/salo_dryland.json`
(core/power/prehab/flex/warmup). Taper = 2 weeks, Race = 1 (fixed).

## Session structure
- Volume split: warmup 20% (drill blocks from `drill_library.json`) /
  main 70% / cooldown 10%. **Every distance is a 25m multiple** (`snap_25`).
- Set titles always match scaled content: numeric template descriptions are
  rewritten to `description` ("40×25m freestyle") with book text preserved in
  `method` (10/26 title/content mismatch incident). Non-numeric keep text.
- CSS zones Z1–Z5 + SPM per zone (`css_zones.py`); FTP pace ≈ CSS anchor;
  metronome sets surface exact SPM.
- Generation is **idempotent and atomic**: all rows are built in memory first,
  then the previous plan is replaced in one transaction (`competition/generate`);
  a failure rolls back and keeps the old plan. Button locks during ~60s.
  Legacy NULL/string profile fields are normalized before the generators run.

## Strength
- Templates TRX/KB/BW/bands + split A/B/C (A=Pull+Core TRX, B=Legs+Hips KB,
  C=Stamina BW), round-robin per implement + weekly rotation
  (`strength_generator.py`).
- Cap flexible: Base/Build 4, Peak 3, Taper 1, Race 0 per week; honors
  requested `min`; AM/PM overlap allowed.
- Youth <14 (`edad`): no weighted power (Salo Ch11). Prehab (Ch8) when
  `feeling<=2` or shoulder/knee in `injury_notes`.

## Adaptive state (`adaptive_state.py`, Salo methodology)
Computed on current/future weeks only; past weeks stay as planned.
| Signal | Rule | Effect |
|---|---|---|
| `min(feeling swim, strength) <= 2` | recovery | volume ×0.7, no SP, RPE 4, +prehab |
| adherence ≥ 80% | bonus | volume ×1.05 |
| adherence < 50% | cut + technique | volume ×0.85 |
| `stroke_count_50m >= 50` (latest SwimTest) | `technique_flag` | +Ch1 drills/DPS sets (skip if recovery) |
| ML load factor (`load_model.py`, M2 server) | clamp ±25% | overrides rules factor; no history → 1.0 |
| missed sessions | **never restacked** | counted only; future modulates |

## Volume guardrails
Weekly caps by level: beginner 12k / intermediate 16k / advanced 25k (m);
onboarding shows live estimate + over-cap warning. Tier calibrates level
and scales base volume (user decision: ML applies).

## Testing & retest
- CSS retest every 6 weeks (dashboard reminder); tests persist in
  `swim_tests` (server truth; `test_date` field — Python shadows `date`).
- `test_salo_mix.py` (13) + `test_adaptive.py` (5) + `test_final_all.py`
  E2E (baseline: only expected 400/404).
