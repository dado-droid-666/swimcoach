# tests/ — live test suite (run from repo root)

## The suite (3 files)
| File | What | How to run (from repo root) |
|---|---|---|
| `test_final_all.py` | E2E baseline: register → profile → competition → generate → plan → feedback → stats → subscription | `.\venv\Scripts\python.exe -m tests.test_final_all` |
| `test_adaptive.py` | Unit funcs: recovery/adherence/planned-weeks/ML-clamp/effort-trend (in-memory sqlite) | `.\venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'tests'); import test_adaptive as t; [getattr(t,n)() for n in dir(t) if n.startswith('test_')]; print('OK')"` |
| `test_salo_mix.py` | Unit funcs: Salo MIX sets (13 tests, same runner pattern) | same pattern with `test_salo_mix` |

No pytest in venv (2026-10): plain `test_*` functions, invoked ad-hoc.
E2E baseline expectation: all PASS except `400` (already-exists on re-run)
and `404` (billing portal without subscription) — see RETOMAR.

## attic/
Superseded phase/probe scripts (phase1-3, api_phase2, cookie, db, final,
subscription×3). Archived, not deleted. Do not extend; do not run in CI.
