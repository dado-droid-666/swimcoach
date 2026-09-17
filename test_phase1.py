from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

init_db()
client = TestClient(app)

# Test register
r = client.post("/api/auth/register", json={
    "email": "test2@example.com",
    "password": "password123",
    "full_name": "Test User 2"
})
print("Register:", r.status_code, r.json())

# Test login
r = client.post("/api/auth/login", json={
    "email": "test2@example.com",
    "password": "password123"
})
print("Login:", r.status_code, r.json())
print("Cookies:", client.cookies)

# Test me
r = client.get("/api/auth/me")
print("Me:", r.status_code, r.json())

# Test create profile
r = client.put("/api/profile", json={
    "level": "intermediate",
    "swim_days_per_week": 4,
    "target_volume_per_session": 3000,
    "preferred_strokes": ["freestyle"],
    "available_equipment": [],
    "primary_goal": "endurance",
    "available_days": [1, 3, 5],
    "session_duration_min": 90
})
print("Create Profile:", r.status_code, r.json())

# Test get profile
r = client.get("/api/profile")
print("Get Profile:", r.status_code, r.json())

# Test create competition
r = client.post("/api/competition", json={
    "competition_date": "2026-06-15",
    "competition_type": "pool",
    "pool_events": ["200_im", "400_free"],
    "ow_distance_km": None,
    "ow_conditions": None,
    "target_times": {"200_im": 160, "400_free": 300},
    "strength_days_per_week": 2
})
print("Create Competition:", r.status_code, r.json())

# Test get competition
r = client.get("/api/competition")
print("Get Competition:", r.status_code, r.json())

# Test update competition
r = client.put("/api/competition", json={
    "strength_days_per_week": 3
})
print("Update Competition:", r.status_code, r.json())

# Test logout
r = client.post("/api/auth/logout")
print("Logout:", r.status_code, r.json())

# Test me after logout
r = client.get("/api/auth/me")
print("Me after logout:", r.status_code, r.text)

# Test error cases
print("\n--- Error Cases ---")

# Duplicate email
r = client.post("/api/auth/register", json={
    "email": "test2@example.com",
    "password": "password123",
    "full_name": "Test User 2"
})
print("Duplicate email:", r.status_code, r.json())

# Invalid login
r = client.post("/api/auth/login", json={
    "email": "test2@example.com",
    "password": "wrongpassword"
})
print("Invalid login:", r.status_code, r.json())

# Unauthorized access
r = client.get("/api/auth/me")
print("Unauthorized me:", r.status_code, r.json())

# Missing profile
# Need to create new user
r = client.post("/api/auth/register", json={
    "email": "test3@example.com",
    "password": "password123",
    "full_name": "Test User 3"
})
r = client.post("/api/auth/login", json={
    "email": "test3@example.com",
    "password": "password123"
})
r = client.get("/api/profile")
print("Missing profile:", r.status_code, r.json())

# Validation error
r = client.post("/api/auth/register", json={
    "email": "invalid-email",
    "password": "123",
    "full_name": ""
})
print("Validation error:", r.status_code, r.json())

print("\nAll tests passed!")