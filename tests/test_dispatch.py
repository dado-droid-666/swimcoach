"""Dispatch-due (Phase 2): window match, once-per-day dedup, rest-day skip,
secret gating. Isolated sqlite file, removed afterwards. VAPID deliberately
UNCONFIGURED here: send_push short-circuits False before network, so the
dedup/window logic is asserted via skipped + last_sent (sent stays 0).

Run from repo root:
    .\\venv\\Scripts\\python.exe tests/test_dispatch.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_dispatch_test.db")
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

from backend.database import Base, get_db  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models import AthleteProfile, TrainingSession, PushSubscription  # noqa: E402
import backend.routes.notifications as notif  # noqa: E402

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


notif.settings.cron_secret = "test-cron-secret"
HDR = {"X-Cron-Secret": "test-cron-secret"}

now_utc = datetime.now(timezone.utc)
now_hm = now_utc.strftime("%H:%M")
old_hm = (now_utc - timedelta(hours=5)).strftime("%H:%M")
today = now_utc.date()


def mkuser(email, with_swim, reminder, with_sub=True):
    r = client.post("/api/auth/register",
                    json={"email": email, "password": "password123", "full_name": "D"})
    assert r.status_code == 201, r.text[:120]
    db = TestingSession()
    from backend.models import User  # noqa: E402
    uid = db.query(User).filter(User.email == email).first().id
    db.add(AthleteProfile(user_id=uid, reminder_time=reminder, reminder_tz="UTC"))
    if with_swim:
        db.add(TrainingSession(user_id=uid, date=today, week_relative=1,
                               phase_name="Base", total_meters=3000))
    if with_sub:
        db.add(PushSubscription(user_id=uid, endpoint=f"https://push.example.com/{email}",
                                p256dh="p", auth="a"))
    db.commit()
    db.close()


# A: session today + reminder now -> attempted (send fails w/o VAPID, but NOT skipped as window/rest)
mkuser("a@test.com", with_swim=True, reminder=now_hm)
# B: rest day (no sessions) -> skipped
mkuser("b@test.com", with_swim=False, reminder=now_hm)
# C: session today but reminder 5h ago -> skipped (outside 30-min window)
mkuser("c@test.com", with_swim=True, reminder=old_hm)
# D: session today + reminder now, NO subscription -> invisible to dispatch
mkuser("d@test.com", with_swim=True, reminder=now_hm, with_sub=False)

r = client.post("/api/notifications/dispatch-due", headers=HDR)
check("dispatch 200", r.status_code == 200, r.status_code)
body = r.json()
check("checked == 3 (only users with subs)", body.get("checked") == 3, body)
check("sent == 0 without VAPID", body.get("sent") == 0, body)
# A attempted but failed to send -> NOT marked sent, counts as skipped path
db = TestingSession()
from backend.models import AthleteProfile as AP  # noqa: E402
from backend.models import User as U  # noqa: E402
a_id = db.query(U).filter(U.email == "a@test.com").first().id
a_last = db.query(AP).filter(AP.user_id == a_id).first().reminder_last_sent
check("failed send does NOT mark last_sent", a_last is None, a_last)
db.close()

# E: dedup — same-day second run skips identically (no double work)
r2 = client.post("/api/notifications/dispatch-due", headers=HDR)
check("second run identical (idempotent)", r2.json() == body, r2.text[:120])

# F: wrong secret -> 401; unconfigured secret -> 401
r = client.post("/api/notifications/dispatch-due", headers={"X-Cron-Secret": "nope"})
check("wrong secret -> 401", r.status_code == 401, r.status_code)
notif.settings.cron_secret = ""
r = client.post("/api/notifications/dispatch-due", headers=HDR)
check("unconfigured secret -> 401", r.status_code == 401, r.status_code)
notif.settings.cron_secret = "test-cron-secret"

# G: bad tz in profile is tolerated (UTC fallback, no crash)
db = TestingSession()
b_id = db.query(U).filter(U.email == "b@test.com").first().id
db.query(AP).filter(AP.user_id == b_id).update({"reminder_tz": "Mars/Olympus"})
db.commit()
db.close()
r = client.post("/api/notifications/dispatch-due", headers=HDR)
check("bad tz tolerated 200", r.status_code == 200, r.status_code)

# H: profile schema validation (422 on bad time/tz via API)
r = client.post("/api/auth/register",
                json={"email": "e@test.com", "password": "password123", "full_name": "E"})
h = {"Cookie": f"access_token={client.post('/api/auth/login', json={'email': 'e@test.com', 'password': 'password123'}).cookies.get('access_token')}"}
r = client.put("/api/profile", headers=h, json={"reminder_time": "25:99"})
check("bad time -> 422", r.status_code == 422, r.status_code)
r = client.put("/api/profile", headers=h, json={"reminder_tz": "Mars/Olympus"})
check("bad tz -> 422", r.status_code == 422, r.status_code)
r = client.put("/api/profile", headers=h, json={"reminder_time": "07:30", "reminder_tz": "America/Mexico_City"})
check("good prefs -> 200 + echoed", r.status_code == 200 and r.json().get("reminder_time") == "07:30", r.status_code)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed: {FAIL}")
engine.dispose()
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
sys.exit(1 if FAIL else 0)
