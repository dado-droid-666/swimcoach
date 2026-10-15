"""Notification endpoints (Phase 1): subscribe/upsert, unsubscribe, vapid-key,
admin test-push gating. Isolated sqlite file, removed afterwards.

Run from repo root:
    .\\venv\\Scripts\\python.exe tests/test_notifications.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_push_test.db")
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

from backend.database import Base, get_db  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models import User  # noqa: E402

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
# Fresh jar for anonymous assertions (TestClient reuses login cookies).
anon = TestClient(app, raise_server_exceptions=False)

PASS, FAIL = [], []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" ({extra})" if extra else ""))


SUB = {"endpoint": "https://push.example.com/sub/abc123",
       "keys": {"p256dh": "p256dh-value", "auth": "auth-value"}}

r = client.post("/api/auth/register", json={"email": "owner2@test.com", "password": "ownerpass1", "full_name": "O"})
check("register owner", r.status_code == 201, r.status_code)
r = client.post("/api/auth/register", json={"email": "user2@test.com", "password": "userpass1", "full_name": "U"})
check("register user", r.status_code == 201, r.status_code)

db = TestingSession()
db.query(User).filter(User.email == "owner2@test.com").update({"is_admin": True})
db.commit()
db.close()


def login(email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login {email}: {r.status_code}"
    return {"Cookie": f"access_token={r.cookies.get('access_token')}"}


owner_h = login("owner2@test.com", "ownerpass1")
user_h = login("user2@test.com", "userpass1")

# vapid-key is public (empty here: no keys in test env)
r = client.get("/api/notifications/vapid-key")
check("vapid-key public 200", r.status_code == 200, r.status_code)
check("vapid-key has public_key field", "public_key" in r.json(), r.text[:80])

# subscribe requires auth
r = anon.post("/api/notifications/subscribe", json=SUB)
check("subscribe anon -> 401", r.status_code == 401, r.status_code)

# subscribe + idempotent re-subscribe
r = client.post("/api/notifications/subscribe", headers=user_h, json=SUB)
check("subscribe 201", r.status_code == 201, r.status_code)
r = client.post("/api/notifications/subscribe", headers=user_h, json=SUB)
check("re-subscribe idempotent 201", r.status_code == 201, r.status_code)
db = TestingSession()
n = db.query(__import__("backend.models", fromlist=["PushSubscription"]).PushSubscription).filter_by(
    endpoint=SUB["endpoint"]).count()
db.close()
check("single row after re-subscribe", n == 1, f"rows={n}")

# bad payload -> 422 (missing keys), 400 (empty keys)
r = client.post("/api/notifications/subscribe", headers=user_h, json={"endpoint": "x"})
check("missing keys -> 422", r.status_code == 422, r.status_code)
r = client.post("/api/notifications/subscribe", headers=user_h,
                json={"endpoint": "https://push.example.com/sub/zzz", "keys": {"p256dh": "", "auth": ""}})
check("empty keys -> 400", r.status_code == 400, r.status_code)

# unsubscribe requires auth + only removes own row
r = anon.request("DELETE", "/api/notifications/subscribe", json={"endpoint": SUB["endpoint"]})
check("unsubscribe anon -> 401", r.status_code == 401, r.status_code)
r = client.request("DELETE", "/api/notifications/subscribe", headers=user_h, json={"endpoint": SUB["endpoint"]})
check("unsubscribe 200", r.status_code == 200, r.status_code)

# admin test-push gating (no VAPID keys in test env -> 503 after passing gates,
# so exercise gates with a fresh subscription)
r = client.post("/api/notifications/subscribe", headers=user_h, json=SUB)
check("re-subscribe for gating", r.status_code == 201, r.status_code)
r = client.post("/api/notifications/test", headers=user_h)
check("non-admin test -> 403", r.status_code == 403, r.status_code)
r = anon.post("/api/notifications/test")
check("anon test -> 401", r.status_code == 401, r.status_code)
r = client.post("/api/notifications/test", headers=owner_h)
check("admin w/o own subs -> 404", r.status_code == 404, r.status_code)

# --- 8. push-receipt beacon (diagnostic): anon POST accepted, admin-only GET ---
r = anon.post("/api/notifications/push-receipt", json={"at": 123456789, "had_data": True})
check("receipt anon POST -> 202", r.status_code == 202, r.status_code)
r = anon.post("/api/notifications/push-receipt", json={"at": "nan"})
check("receipt bad shape -> 422", r.status_code == 422, r.status_code)
r = anon.get("/api/notifications/push-receipts")
check("receipts anon -> 401", r.status_code == 401, r.status_code)
r = client.get("/api/notifications/push-receipts", headers=user_h)
check("receipts non-admin -> 403", r.status_code == 403, r.status_code)
r = client.get("/api/notifications/push-receipts", headers=owner_h)
check("receipts admin 200 + sees beacon", r.status_code == 200 and any(
    x.get("at") == 123456789 for x in r.json().get("receipts", [])), r.text[:100])

print(f"\n{len(PASS)} passed, {len(FAIL)} failed: {FAIL}")
os.remove(TEST_DB)
sys.exit(1 if FAIL else 0)
