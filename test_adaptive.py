"""Tests adaptativos: feeling->recovery, adherencia->volumen, perdidas no se
apilan, semana pasada planificada, ML servidor con clamp. SQLite en memoria.
Uso: python -m pytest test_adaptive.py -v
"""
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import DailyFeedback, ExerciseLog, StrengthSession, TrainingSession
from backend.services.adaptive_state import build_week_adaptive, compute_athlete_state
from backend.services.load_model import suggest_load_factor


def monday():
    d = date.today()
    return d - timedelta(days=d.weekday())


def make_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return TestingSession()


def add_week(db, uid, start, swim=True, strength=True):
    for i in range(4 if swim else 0):
        db.add(TrainingSession(user_id=uid, date=start + timedelta(days=i),
                               week_relative=-3, phase_name="Base", total_meters=3000))
    for i in range(2 if strength else 0):
        db.add(StrengthSession(user_id=uid, date=start + timedelta(days=i),
                               week_relative=-3, phase_name="Base", focus="x",
                               exercises=[], estimated_duration_min=30,
                               equipment_needed=[]))
    db.commit()


def test_recovery_por_feeling():
    db = make_db()
    start = monday() - timedelta(days=14)
    add_week(db, 1, start)
    db.add(DailyFeedback(user_id=1, date=date.today() - timedelta(days=1),
                         swim_feeling=2, swim_completed=True,
                         strength_feeling=4, strength_completed=True))
    db.commit()
    st = compute_athlete_state(db, 1)
    assert st["recovery"] is True
    assert st["volume_factor"] == 0.7
    assert st["min_feeling"] == 2


def test_adherencia_alta_sube_y_baja_resta():
    db = make_db()
    start = monday() - timedelta(days=14)
    add_week(db, 2, start)  # 6 planeadas
    for i in range(6):
        db.add(DailyFeedback(user_id=2, date=start + timedelta(days=i),
                             swim_feeling=4, swim_completed=True,
                             strength_feeling=4, strength_completed=True))
    db.commit()
    st = compute_athlete_state(db, 2)
    assert st["completion_rate"] >= 0.8
    assert st["volume_factor"] == 1.05

    db2 = make_db()
    add_week(db2, 3, start)
    db2.add(DailyFeedback(user_id=3, date=start, swim_feeling=4,
                          swim_completed=True, strength_completed=False))
    db2.commit()
    st2 = compute_athlete_state(db2, 3)
    assert st2["completion_rate"] < 0.5
    assert st2["volume_factor"] == 0.85
    assert st2["missed"] == 5  # 6 planeadas - 1 hecha; no se reapilan, solo se cuentan


def test_semana_pasada_planificada_y_actual_adaptativa():
    db = make_db()
    start = monday() - timedelta(days=14)
    add_week(db, 4, start)
    db.add(DailyFeedback(user_id=4, date=date.today() - timedelta(days=1),
                         swim_feeling=2, swim_completed=True,
                         strength_feeling=2, strength_completed=True))
    db.commit()
    profile = type("P", (), {"edad": 30, "injury_notes": ""})()
    goal = type("G", (), {})()
    past = build_week_adaptive(db, 4, profile, goal, monday() - timedelta(days=21))
    assert past["salo"] is True and past["recovery"] is False
    assert past["volume_factor"] == 1.0
    cur = build_week_adaptive(db, 4, profile, goal, monday())
    assert cur["recovery"] is True and cur["volume_factor"] == 0.7
    assert cur["edad"] == 30


def test_ml_servidor_con_clamp():
    state_ok = {"avg_effort": 2.0, "completion_rate": 1.0, "planned": 10}
    r = suggest_load_factor(state_ok, tier=3)
    assert 0.75 <= r["factor"] <= 1.25 and "source" in r
    state_empty = {"avg_effort": None, "completion_rate": None, "planned": 0}
    r2 = suggest_load_factor(state_empty)
    assert r2["factor"] == 1.0 and r2["source"] == "conservative_rules_v1"


def test_effort_trend_presente():
    db = make_db()
    for i in range(6):
        db.add(ExerciseLog(user_id=5, date=date.today() - timedelta(days=6 - i),
                           session_type="strength", exercise_name="TRX Row",
                           reps="10", effort=2 if i < 3 else 4))
    db.commit()
    st = compute_athlete_state(db, 5)
    assert st["effort_trend"] == 2.0
