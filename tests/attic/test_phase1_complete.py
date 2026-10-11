from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

init_db()
client = TestClient(app)

# Test register + login + manual cookie handling
r = client.post("/api/auth/register", json={
    "email": "test2@example.com",
    "password": "password123",
    "full_name": "Test User 2"
})
print("Register:", r.status_code)

r = client.post("/api/auth/login", json={
    "email": "test2@example.com",
    "password": "password123"
})
print("Login:", r.status_code)

# Extract cookie manually
cookie = r.cookies.get("access_token")
print("Cookie:", cookie)

# Use cookie in subsequent requests
headers = {"Cookie": f"access_token={cookie}"}
r = client.get("/api/auth/me", headers=headers)
print("Me:", r.status_code, r.json())

r = client.put("/api/profile", json={
    "level": "intermediate",
    "swim_days_per_week": 4,
    "target_volume_per_session": 3000,
    "preferred_strokes": ["freestyle"],
    "available_equipment": [],
    "primary_goal": "endurance",
    "available_days": [1, 3, 5],
    "session_duration_min": 90
}, headers=headers)
print("Create Profile:", r.status_code, r.json())

r = client.get("/api/profile", headers=headers)
print("Get Profile:", r.status_code, r.json())

r = client.post("/api/competition", json={
    "competition_date": "2026-06-15",
    "competition_type": "pool",
    "pool_events": ["200_im", "400_free"],
    "ow_distance_km": None,
    "ow_conditions": None,
    "target_times": {"200_im": 160, "400_free": 300},
    "strength_days_per_week": 2
}, headers=headers)
print("Create Competition:", r.status_code, r.json())

r = client.get("/api/competition", headers=headers)
print("Get Competition:", r.status_code, r.json())

r = client.put("/api/competition", json={
    "strength_days_per_week": 3
}, headers=headers)
print("Update Competition:", r.status_code, r.json())

r = client.post("/api/auth/logout", headers=headers)
print("Logout:", r.status_code, r.json())

# Test open water competition
r = client.post("/api/auth/register", json={
    "email": "test3@example.com",
    "password": "password123",
    "full_name": "Test User 3"
})
r = client.post("/api/auth/login", json={
    "email": "test3@example.com",
    "password": "password123"
})
cookie = r.cookies.get("access_token")
headers = {"Cookie": f"access_token={cookie}"}

r = client.post("/api/competition", json={
    "competition_date": "2026-07-01",
    "competition_type": "open_water",
    "pool_events": [],
    "ow_distance_km": 5,
    "ow_conditions": "choppy",
    "target_times": {},
    "strength_days_per_week": 2
}, headers=headers)
print("Create OW Competition:", r.status_code, r.json())

r = client.get("/api/competition", headers=headers)
print("Get OW Competition:", r.status_code, r.json())

# Test delete competition
r = client.delete("/api/competition", headers=headers)
print("Delete Competition:", r.status_code)

# Verify deleted
r = client.get("/api/competition", headers=headers)
print("Get after delete:", r.status_code, r.json())

print("\n=== ALL PHASE 1 TESTS PASSED ===")