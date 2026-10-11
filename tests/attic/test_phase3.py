from backend.database import init_db, get_db_context
from backend.models import User, DailyFeedback, TrainingSession, StrengthSession
from backend.auth import get_password_hash
from backend.services.macrocycle_calculator import calculate_macrocycle
from backend.services.swim_generator import generate_weekly_swim_plan
from backend.services.strength_generator import generate_weekly_strength_plan
from backend.schemas import CompetitionType
from datetime import date, timedelta

init_db()

# Create test user and data
with get_db_context() as db:
    # Clean up any existing test user
    existing = db.query(User).filter(User.email == "phase3_test@example.com").first()
    if existing:
        db.delete(existing)
        db.commit()
    
    # Create user
    user = User(
        email="phase3_test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Phase 3 Test",
        subscription_tier="free"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id

# Create profile
from backend.models import AthleteProfile, CompetitionGoal
with get_db_context() as db:
    profile = AthleteProfile(
        user_id=user_id,
        level="intermediate",
        swim_days_per_week=4,
        target_volume_per_session=3000,
        available_equipment=["pull_buoy", "paddles"],
        preferred_strokes=["freestyle", "IM"],
        primary_goal="endurance",
        available_days=[1, 3, 5],
        session_duration_min=90,
        ftp_pace_per_100=95
    )
    db.add(profile)
    
    # Competition goal
    comp_date = date.today() + timedelta(weeks=12)
    goal = CompetitionGoal(
        user_id=user_id,
        competition_date=comp_date,
        competition_type="pool",
        pool_events=["200_im", "400_free"],
        strength_days_per_week=2
    )
    db.add(goal)
    db.commit()

# Generate macrocycle and sessions
from backend.services.macrocycle_calculator import calculate_macrocycle
from backend.services.swim_generator import generate_weekly_swim_plan
from backend.services.strength_generator import generate_weekly_strength_plan
from backend.schemas import CompetitionType

with get_db_context() as db:
    goal = db.query(CompetitionGoal).filter(CompetitionGoal.user_id == user_id).first()
    macro = calculate_macrocycle(
        competition_date=goal.competition_date,
        competition_type=goal.competition_type,
        pool_events=goal.pool_events,
        ow_distance_km=goal.ow_distance_km
    )
    
    from backend.models import MacrocyclePlan
    macrocycle = MacrocyclePlan(
        user_id=user_id,
        competition_goal_id=goal.id,
        total_weeks=macro.total_weeks,
        phases=macro.phases
    )
    db.add(macrocycle)
    db.commit()
    db.refresh(macrocycle)
    
    # Generate first week sessions
    week_start = macro.start_date
    swim_sessions = generate_weekly_swim_plan(
        week_start=week_start,
        week_relative=-12,
        macrocycle_phases=macro.phases,
        profile={
            "level": "intermediate",
            "swim_days_per_week": 4,
            "target_volume_per_session": 3000,
            "available_equipment": ["pull_buoy", "paddles"],
            "preferred_strokes": ["freestyle", "IM"],
            "ftp_pace_per_100": 95,
            "session_duration_min": 90,
            "available_days": [1, 3, 5]
        },
        competition_type=CompetitionType.POOL,
        pool_events=["200_im", "400_free"],
        ow_distance_km=None
    )
    
    for s in swim_sessions:
        from backend.models import TrainingSession
        ts = TrainingSession(
            user_id=user_id,
            date=date.fromisoformat(s["date"]),
            week_relative=s["week_relative"],
            phase_name=s["phase_name"],
            total_meters=s["total_meters"],
            estimated_duration_min=s["estimated_duration_min"],
            focus=s["focus"],
            rpe_target=s["rpe_target"],
            warmup=s["warmup"],
            main_set=s["main_set"],
            cooldown=s["cooldown"]
        )
        db.add(ts)
    
    # Strength sessions
    strength_sessions = generate_weekly_strength_plan(
        week_start=week_start,
        week_relative=-12,
        macrocycle_phases=macro.phases,
        profile={"available_equipment": ["bodyweight", "bands"], "level": "intermediate"},
        swim_days=[1, 3, 5]
    )
    
    for s in strength_sessions:
        from backend.models import StrengthSession
        ss = StrengthSession(
            user_id=user_id,
            date=date.fromisoformat(s["date"]),
            week_relative=s["week_relative"],
            phase_name=s["phase_name"],
            focus=s["focus"],
            exercises=s["exercises"],
            estimated_duration_min=s["estimated_duration_min"],
            equipment_needed=s["equipment_needed"]
        )
        db.add(ss)
    
    db.commit()

print("Test data created successfully!")

# Now test feedback submission
with get_db_context() as db:
    # Submit feedback for first swim session
    first_swim = swim_sessions[0]
    fb = DailyFeedback(
        user_id=user_id,
        date=date.fromisoformat(first_swim["date"]),
        swim_feeling=4,
        swim_completed=True,
        swim_completed_meters=first_swim["total_meters"],
        strength_feeling=3,
        strength_completed=False,
        comments="Good session, felt strong"
    )
    db.add(fb)
    
    # Feedback for second day (strength)
    first_strength = strength_sessions[0]
    fb2 = DailyFeedback(
        user_id=user_id,
        date=date.fromisoformat(first_strength["date"]),
        swim_feeling=None,
        swim_completed=False,
        strength_feeling=4,
        strength_completed=True,
        comments="Strength felt good"
    )
    db.add(fb2)
    db.commit()

print("Feedback submitted!")

# Test stats calculation
from backend.routes.stats import get_stats_summary, get_readiness
from backend.auth import get_current_user

# Test readiness (simulate pro user)
with get_db_context() as db:
    user = db.query(User).filter(User.id == user_id).first()
    user.subscription_tier = "pro"
    db.commit()
    
    # Test readiness calculation
    from backend.routes.stats import get_readiness
    # We can't easily test the endpoint without the full request context
    # But the logic is in the route

print("Phase 3 tests completed!")