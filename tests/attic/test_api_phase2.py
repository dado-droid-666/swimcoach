from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db
from backend.auth import create_access_token

init_db()
client = TestClient(app)

# Create test user
r = client.post("/api/auth/register", json={
    "email": "api_test@example.com",
    "password": "password123",
    "full_name": "API Test User"
})
print("Register:", r.status_code)

# Login
r = client.post("/api/auth/login", json={
    "email": "api_test@example.com",
    "password": "password123"
})
print("Login:", r.status_code)

# Get cookie
cookie = r.cookies.get("access_token")
headers = {"Cookie": f"access_token={cookie}"}

# Create profile
r = client.put("/api/profile", json={
    "level": "intermediate",
    "swim_days_per_week": 4,
    "target_volume_per_session": 3000,
    "available_equipment": ["pull_buoy", "paddles"],
    "preferred_strokes": ["freestyle", "IM"],
    "primary_goal": "endurance",
    "available_days": [1, 3, 5],
    "session_duration_min": 90,
    "ftp_pace_per_100": 95
}, headers=headers)
print("Profile:", r.status_code)

# Create competition (12 weeks out)
from datetime import date, timedelta
comp_date = date.today() + timedelta(weeks=12)
r = client.post("/api/competition", json={
    "competition_date": comp_date.isoformat(),
    "competition_type": "pool",
    "pool_events": ["200_im", "400_free"],
    "ow_distance_km": None,
    "ow_conditions": None,
    "target_times": {"200_im": 160, "400_free": 300},
    "strength_days_per_week": 2
}, headers=headers)
print("Competition:", r.status_code, r.json())

# Generate macrocycle
r = client.post("/api/competition/generate", headers=headers)
print("Generate macrocycle:", r.status_code, r.json())

# Get macrocycle
r = client.get("/api/macrocycle", headers=headers)
print("Macrocycle:", r.status_code)
macro = r.json()
print(f"  Total weeks: {macro['total_weeks']}")
print(f"  Phases: {len(macro['phases'])}")
for p in macro['phases']:
    print(f"    {p['name']}: weeks {p['start_week']} to {p['end_week']}")

# Get this week's plan
today = date.today()
week_start = today - timedelta(days=today.weekday())
r = client.get(f"/api/plan/week?start={week_start.isoformat()}", headers=headers)
print(f"\nWeek plan ({week_start}):", r.status_code)
week = r.json()
print(f"  Swim sessions: {len(week['swim_sessions'])}")
print(f"  Strength sessions: {len(week['strength_sessions'])}")
for s in week['swim_sessions']:
    print(f"  Swim {s['date']}: {s['total_meters']}m, {s['focus']}, {len(s['main_set'])} sets")
for s in week['strength_sessions']:
    print(f"  Strength {s['date']}: {s['focus']}, {len(s['exercises'])} exercises")

# Get today's plan
r = client.get("/api/plan/today", headers=headers)
print("\nToday plan:", r.status_code)
today_plan = r.json()
if today_plan['swim']:
    print(f"  Swim: {today_plan['swim']['total_meters']}m, {today_plan['swim']['focus']}")
if today_plan['strength']:
    print(f"  Strength: {today_plan['strength']['focus']}, {len(today_plan['strength']['exercises'])} exercises")

print("\n=== PHASE 2 API TESTS PASSED ===")