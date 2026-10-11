from backend.database import init_db
from backend.auth import create_access_token
from backend.services.macrocycle_calculator import calculate_macrocycle, get_event_category
from backend.services.swim_generator import generate_weekly_swim_plan
from backend.services.strength_generator import generate_weekly_strength_plan
from backend.schemas import CompetitionType, Level
from datetime import date, timedelta

init_db()

# Test macrocycle calculation
print("=== Testing Macrocycle Calculation ===")
competition_date = date.today() + timedelta(weeks=12)
macro = calculate_macrocycle(
    competition_date=competition_date,
    competition_type=CompetitionType.POOL,
    pool_events=["200_im", "400_free"],
    ow_distance_km=None
)
print(f"Total weeks: {macro.total_weeks}")
print(f"Start date: {macro.start_date}")
print("Phases:")
for p in macro.phases:
    print(f"  {p['name']}: weeks {p['start_week']} to {p['end_week']} (swim_mult={p['swim_volume_mult']}, str_days={p['strength_days']})")

# Test event category
cat = get_event_category(CompetitionType.POOL, ["200_im", "400_free"], None)
print(f"\nEvent category: {cat}")

cat = get_event_category(CompetitionType.OPEN_WATER, [], 5.0)
print(f"OW category: {cat}")

# Test swim plan generation
print("\n=== Testing Swim Plan Generation ===")
profile = {
    "level": "intermediate",
    "swim_days_per_week": 4,
    "target_volume_per_session": 3000,
    "available_equipment": ["pull_buoy", "paddles"],
    "preferred_strokes": ["freestyle", "IM"],
    "ftp_pace_per_100": 95,
    "session_duration_min": 90,
    "available_days": [1, 3, 5]
}

week_start = date.today() - timedelta(days=date.today().weekday())
swim_sessions = generate_weekly_swim_plan(
    week_start=week_start,
    week_relative=-12,
    macrocycle_phases=macro.phases,
    profile=profile,
    competition_type=CompetitionType.POOL,
    pool_events=["200_im", "400_free"],
    ow_distance_km=None
)

print(f"Generated {len(swim_sessions)} swim sessions:")
for s in swim_sessions:
    print(f"  {s['date']} ({s['day_name']}): {s['total_meters']}m, {s['focus']}, {len(s['main_set'])} main sets")

# Test strength plan
print("\n=== Testing Strength Plan Generation ===")
strength_sessions = generate_weekly_strength_plan(
    week_start=week_start,
    week_relative=-12,
    macrocycle_phases=macro.phases,
    profile={"available_equipment": ["bodyweight", "bands"], "level": "intermediate"},
    swim_days=[0, 2, 4]  # Mon, Wed, Fri
)

print(f"Generated {len(strength_sessions)} strength sessions:")
for s in strength_sessions:
    print(f"  {s['date']} ({s['day_name']}): {s['focus']}, {len(s['exercises'])} exercises, {s['estimated_duration_min']}min")

print("\n=== ALL TESTS PASSED ===")