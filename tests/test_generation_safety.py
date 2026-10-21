"""Plan generation safety: atomic replace + legacy NULL profile fields.

Covers the 500 incident where a failed generation could delete the athlete's
existing plan, and old rows with NULL JSON/integer columns crashed the
generators. Isolated sqlite file, removed afterwards.

Run from repo root:
    .\\venv\\Scripts\\python.exe tests/test_generation_safety.py
"""
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_generation_test.db")
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

from backend.database import Base, get_db  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models import (  # noqa: E402
    AthleteProfile, MacrocyclePlan, StrengthSession, TrainingSession, User,
)
import backend.routes.competition as competition  # noqa: E402

engine = create_engine(f"sqlite:///{TEST_DB}", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app, raise_server_exceptions=False)

PASS, FAIL = [], []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" ({extra})" if extra else ""))


def user_id(email):
    db = TestingSession()
    try:
        return db.query(User).filter(User.email == email).first().id
    finally:
        db.close()


def plan_state(email):
    uid = user_id(email)
    db = TestingSession()
    try:
        macro = db.query(MacrocyclePlan).filter(MacrocyclePlan.user_id == uid).first()
        return {
            "macro_id": macro.id if macro else None,
            "weeks": macro.total_weeks if macro else None,
            "swim": db.query(TrainingSession).filter(TrainingSession.user_id == uid).count(),
            "strength": db.query(StrengthSession).filter(StrengthSession.user_id == uid).count(),
        }
    finally:
        db.close()


EMAIL = "gen-safety@test.com"
r = client.post("/api/auth/register", json={
    "email": EMAIL, "password": "password123", "full_name": "Gen",
})
check("register", r.status_code == 201, r.status_code)

profile = {
    "level": "intermediate",
    "swim_days_per_week": 4,
    "target_volume_per_session": 2500,
    "preferred_strokes": ["freestyle"],
    "available_equipment": ["bodyweight", "bands"],
    "primary_goal": "endurance",
    "available_days": [1, 3, 5, 6],
    "strength_days": [2, 4],
    "session_duration_min": 90,
}
r = client.put("/api/profile", json=profile)
check("profile create", r.status_code == 200, r.status_code)

goal = {
    "competition_date": (date.today() + timedelta(weeks=8)).isoformat(),
    "competition_type": "pool",
    "pool_events": ["100_free"],
    "strength_days_per_week": 2,
}
r = client.post("/api/competition", json=goal)
check("competition create", r.status_code == 201, r.status_code)

# A) happy path builds a complete plan
r = client.post("/api/competition/generate")
check("first generate 201", r.status_code == 201, r.status_code)
first = plan_state(EMAIL)
check("plan has swim sessions", first["swim"] > 0, first)
check("plan has strength sessions", first["strength"] > 0, first)
check("macrocycle saved", first["macro_id"] is not None, first)

# B) a generator crash must not delete or replace the existing plan
original = competition.generate_weekly_swim_plan
calls = {"n": 0}


def boom(*args, **kwargs):
    calls["n"] += 1
    if calls["n"] == 2:
        raise RuntimeError("forced generator failure")
    return original(*args, **kwargs)


competition.generate_weekly_swim_plan = boom
try:
    r = client.post("/api/competition/generate")
finally:
    competition.generate_weekly_swim_plan = original

check("failed generate returns 500", r.status_code == 500, r.status_code)
after_failure = plan_state(EMAIL)
check("old plan kept after failure", after_failure == first,
      {"before": first, "after": after_failure})

# C) legacy NULL profile columns are normalized, not a 500
db = TestingSession()
db.query(AthleteProfile).filter(AthleteProfile.user_id == user_id(EMAIL)).update({
    "level": None,
    "swim_days_per_week": None,
    "target_volume_per_session": None,
    "preferred_strokes": None,
    "available_equipment": None,
    "available_days": None,
    "strength_days": None,
    "session_duration_min": None,
})
db.commit()
db.close()

r = client.post("/api/competition/generate")
check("legacy NULL profile generates", r.status_code == 201,
      f"{r.status_code} {r.text[:120]}")
rebuilt = plan_state(EMAIL)
check("rebuilt plan has sessions", rebuilt["swim"] > 0 and rebuilt["strength"] > 0, rebuilt)

# D) legacy strings / mixed-case level must not reach the generators raw
db = TestingSession()
db.query(AthleteProfile).filter(AthleteProfile.user_id == user_id(EMAIL)).update({
    "level": "Intermediate",
    "available_days": ["1", "3", "bogus"],
    "strength_days": ["2", "9"],
})
db.commit()
db.close()

r = client.post("/api/competition/generate")
check("legacy string weekdays generate", r.status_code == 201,
      f"{r.status_code} {r.text[:120]}")
string_plan = plan_state(EMAIL)
check("string-weekday plan has sessions",
      string_plan["swim"] > 0 and string_plan["strength"] > 0, string_plan)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed: {FAIL}")
engine.dispose()
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
sys.exit(1 if FAIL else 0)
