"""Tests metodologia Salo: MIX por evento, Taper/Recovery sin SP, youth,
prehab y mezcla TRX/KB + libro. Puros unitarios, sin DB ni servidor.
Uso: python -m pytest test_salo_mix.py -v
"""
from datetime import date, timedelta

from backend.services.macrocycle_calculator import get_event_category
from backend.services.salo_mix import (
    needs_prehab,
    salo_dryland_picks,
    salo_main_sets,
    salo_mix_for,
    salo_recovery_sets,
)
from backend.services.swim_generator import generate_weekly_swim_plan
from backend.services.strength_generator import generate_weekly_strength_plan
from backend.schemas import CompetitionType

BASE_PROFILE = {
    "level": "intermediate",
    "swim_days_per_week": 4,
    "target_volume_per_session": 3000,
    "available_equipment": ["trx", "kettlebell", "bands", "bodyweight"],
    "preferred_strokes": ["freestyle"],
    "ftp_pace_per_100": 95,
    "session_duration_min": 90,
    "available_days": [0, 1, 3, 5],
}

PHASES = [
    {"name": "Base", "start_week": -6, "end_week": -4, "swim_focus": "x",
     "strength_focus": "x", "swim_volume_mult": 1.0, "strength_days": 4,
     "intensity_distribution": {}},
    {"name": "Build", "start_week": -3, "end_week": -3, "swim_focus": "x",
     "strength_focus": "x", "swim_volume_mult": 1.1, "strength_days": 4,
     "intensity_distribution": {}},
    {"name": "Peak", "start_week": -2, "end_week": -2, "swim_focus": "x",
     "strength_focus": "x", "swim_volume_mult": 1.0, "strength_days": 3,
     "intensity_distribution": {}},
    {"name": "Taper", "start_week": -1, "end_week": -1, "swim_focus": "x",
     "strength_focus": "x", "swim_volume_mult": 0.6, "strength_days": 1,
     "intensity_distribution": {}},
]


def monday():
    d = date.today()
    return d - timedelta(days=d.weekday())


def test_mix_por_evento():
    assert salo_mix_for("pool_sprint") == {"EN1": 0.3, "EN2": 0.2, "SP": 0.5}
    assert salo_mix_for("pool_mid")["SP"] == 0.25
    assert salo_mix_for("pool_distance")["EN1"] == 0.55
    assert salo_mix_for("ow_long")["EN1"] == 0.55
    assert salo_mix_for("ow_ultra")["SP"] == 0.1


def test_event_category_ow_se_queda():
    assert get_event_category(CompetitionType.OPEN_WATER, [], 2.0) == "ow_short"
    assert get_event_category(CompetitionType.OPEN_WATER, [], 10.0) == "ow_long"
    assert get_event_category(CompetitionType.POOL, ["50_free"], None) == "pool_sprint"
    assert get_event_category(CompetitionType.POOL, ["1500_free"], None) == "pool_distance"


def test_peak_lleva_sp_y_taper_no():
    peak = salo_main_sets("pool_sprint", "Peak")
    assert any(s["intensity_zone"] == "Z4" for s in peak)
    taper = salo_main_sets("pool_sprint", "Taper")
    assert taper and not any(s["intensity_zone"] == "Z4" for s in taper)


def test_recovery_sin_velocidad():
    rec = salo_recovery_sets()
    assert rec and all(s["intensity_zone"] in ("Z1", "Z2") for s in rec)


def test_youth_sin_power_con_peso():
    picks = salo_dryland_picks("Peak", feeling=5, edad=12)
    assert not any("Hang Clean" in p["name"] or "Push Press" in p["name"] for p in picks)
    adult = salo_dryland_picks("Peak", feeling=5, edad=20)
    assert any("Jump" in p["name"] or "Hang Clean" in p["name"] for p in adult)


def test_prehab_por_feeling_y_lesion():
    assert needs_prehab(2, "") is True
    assert needs_prehab(5, "hombro cargado") is True
    assert needs_prehab(5, "knee pain") is True
    assert needs_prehab(5, "") is False
    assert needs_prehab(None, "") is False
    picks = salo_dryland_picks("Base", feeling=2, edad=30)
    assert any("Retraction" in p["name"] or "Catch Position" in p["name"] for p in picks)


def test_plan_salo_trae_fuente_y_sin_sp_en_recovery():
    adapt = {"salo": True, "recovery": False, "volume_factor": 1.0, "reason": "t"}
    sessions = generate_weekly_swim_plan(
        monday(), -2, PHASES, BASE_PROFILE, CompetitionType.POOL, ["100_free"], None, adapt)
    assert sessions
    assert all(s["generated_by"] == "macrocycle_v1+salo" for s in sessions)
    assert any("Ch" in (st.get("fuente_pag") or "") for s in sessions for st in s["main_set"])
    assert any(st["intensity_zone"] == "Z4" for s in sessions for st in s["main_set"])

    adapt_r = {"salo": True, "recovery": True, "volume_factor": 0.7,
               "feeling": 2, "reason": "t"}
    rec_sessions = generate_weekly_swim_plan(
        monday(), -2, PHASES, BASE_PROFILE, CompetitionType.POOL, ["100_free"], None, adapt_r)
    assert all(s["rpe_target"] == 4 for s in rec_sessions)
    assert not any(st["intensity_zone"] == "Z4"
                   for s in rec_sessions for st in s["main_set"])


def test_fuerza_mix_trx_kb_y_salo():
    adapt = {"salo": True, "recovery": False, "volume_factor": 1.0,
             "feeling": 4, "edad": 30, "injury_notes": "", "reason": "t"}
    sessions = generate_weekly_strength_plan(
        monday(), -3, PHASES, BASE_PROFILE, [0, 1, 3], requested_per_week=2, adaptive=adapt)
    assert sessions
    names = [e["name"] for s in sessions for e in s["exercises"]]
    assert any("TRX" in n for n in names)  # plantillas existentes se quedan
    assert any(n in ("Prone Bridge", "Back Bridge", "Side Bridge") for n in names)  # core Salo


def test_focus_cabe_en_varchar_postgres():
    """Guardia durable: focus <=100 (Postgres valida, SQLite no)."""
    adapt = {"salo": True, "recovery": False, "volume_factor": 1.0,
             "feeling": 4, "edad": 30, "injury_notes": "", "reason": "t"}
    adapt_r = {"salo": True, "recovery": True, "volume_factor": 0.7,
               "feeling": 2, "edad": 30, "injury_notes": "hombro", "reason": "t"}
    for wk, ph in [(-4, "Base"), (-3, "Build"), (-2, "Peak"), (-1, "Taper")]:
        for a in (adapt, adapt_r):
            for s in generate_weekly_strength_plan(
                    monday(), wk, PHASES, BASE_PROFILE, [0, 1],
                    requested_per_week=2, adaptive=a):
                assert len(s["focus"]) <= 100, s["focus"]
            for s in generate_weekly_swim_plan(
                    monday(), wk, PHASES, BASE_PROFILE, CompetitionType.POOL,
                    ["100_free"], None, a):
                assert len(s["focus"] or "") <= 100, s["focus"]
                assert len(s["generated_by"]) <= 20, s["generated_by"]


def test_fuerza_youth_y_prehab():
    peak_phases = [dict(p, start_week=0, end_week=0) if p["name"] == "Peak" else p for p in PHASES]
    adapt_y = {"salo": True, "recovery": False, "volume_factor": 1.0,
               "feeling": 5, "edad": 12, "injury_notes": "", "reason": "t"}
    sessions = generate_weekly_strength_plan(
        monday(), 0, peak_phases, BASE_PROFILE, [0], requested_per_week=1, adaptive=adapt_y)
    names = [e["name"] for s in sessions for e in s["exercises"]]
    assert not any(n in ("Hang Clean", "Push Press") for n in names)

    adapt_p = {"salo": True, "recovery": True, "volume_factor": 0.7,
               "feeling": 2, "edad": 30, "injury_notes": "hombro", "reason": "t"}
    sessions_p = generate_weekly_strength_plan(
        monday(), -3, PHASES, BASE_PROFILE, [0], requested_per_week=1, adaptive=adapt_p)
    names_p = [e["name"] for s in sessions_p for e in s["exercises"]]
    assert any("Retraction" in n or "Catch Position" in n for n in names_p)
