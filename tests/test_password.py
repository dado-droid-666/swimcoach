"""Password endpoints: change-password (self) + admin-reset-password (owner).

Run from repo root (isolated sqlite file, removed afterwards):
    .\\venv\\Scripts\\python.exe tests/test_password.py
Uses TestClient with get_db overridden so the real swim_coach.db is untouched.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pw_test.db")
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

from backend.database import Base, get_db  # noqa: E402
from backend.main import app  # noqa: E402

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

PASS = []
FAIL = []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" ({extra})" if extra else ""))


# --- fixture: owner (admin) + regular user ---
r = client.post("/api/auth/register", json={"email": "owner@test.com", "password": "ownerpass1", "full_name": "Owner"})
check("register owner", r.status_code == 201, r.status_code)
r = client.post("/api/auth/register", json={"email": "user@test.com", "password": "userpass1", "full_name": "User"})
check("register user", r.status_code == 201, r.status_code)

# grant admin directly (mirrors the Supabase one-time step)
db = TestingSession()
from backend.models import User  # noqa: E402
db.query(User).filter(User.email == "owner@test.com").update({"is_admin": True})
db.commit()
db.close()


def login(email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text[:120]}"
    return {"Cookie": f"access_token={r.cookies.get('access_token')}"}


owner_h = login("owner@test.com", "ownerpass1")
user_h = login("user@test.com", "userpass1")

# --- 1. change-password OK ---
r = client.post("/api/auth/change-password", headers=user_h,
                json={"current_password": "userpass1", "new_password": "newpass99"})
check("change OK 200", r.status_code == 200, r.status_code)
r = client.post("/api/auth/login", json={"email": "user@test.com", "password": "newpass99"})
check("login with new password", r.status_code == 200, r.status_code)
user_h = login("user@test.com", "newpass99")
r = client.post("/api/auth/login", json={"email": "user@test.com", "password": "userpass1"})
check("old password rejected", r.status_code == 401, r.status_code)

# --- 2. wrong current -> 401 ---
r = client.post("/api/auth/change-password", headers=user_h,
                json={"current_password": "wrongpass", "new_password": "another99"})
check("wrong current -> 401", r.status_code == 401, r.status_code)

# --- 3. short new -> 422 ---
r = client.post("/api/auth/change-password", headers=user_h,
                json={"current_password": "newpass99", "new_password": "short"})
check("short new -> 422", r.status_code == 422, r.status_code)

# --- 4. anonymous -> 401 ---
r = client.post("/api/auth/change-password",
                json={"current_password": "x", "new_password": "yyyyyyyy"})
check("anonymous change -> 401", r.status_code == 401, r.status_code)

# --- 5. non-admin reset -> 403 ---
r = client.post("/api/auth/admin-reset-password", headers=user_h,
                json={"email": "owner@test.com"})
check("non-admin reset -> 403", r.status_code == 403, r.status_code)

# --- 6. admin reset OK + temp works once shown ---
r = client.post("/api/auth/admin-reset-password", headers=owner_h,
                json={"email": "user@test.com"})
check("admin reset 200", r.status_code == 200, r.status_code)
temp = r.json().get("temp_password", "")
check("temp length >= 12", len(temp) >= 12, f"len={len(temp)}")
r = client.post("/api/auth/login", json={"email": "user@test.com", "password": temp})
check("login with temp password", r.status_code == 200, r.status_code)

# --- 7. unknown user -> 404 ---
r = client.post("/api/auth/admin-reset-password", headers=owner_h,
                json={"email": "ghost@test.com"})
check("unknown user -> 404", r.status_code == 404, r.status_code)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed: {FAIL}")
os.remove(TEST_DB)
sys.exit(1 if FAIL else 0)
