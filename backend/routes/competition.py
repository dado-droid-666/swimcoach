from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date, timedelta

from ..database import get_db
from ..models import CompetitionGoal, User, CompetitionType, MacrocyclePlan, TrainingSession, StrengthSession
from ..schemas import CompetitionGoalCreate, CompetitionGoalUpdate, CompetitionGoalResponse
from ..auth import get_current_user
from ..services.macrocycle_calculator import calculate_macrocycle, get_phase_for_week
from ..services.swim_generator import generate_weekly_swim_plan
from ..services.strength_generator import generate_weekly_strength_plan
from ..models import MacrocyclePlan, TrainingSession, StrengthSession

router = APIRouter(prefix="/api/competition", tags=["competition"])


@router.get("", response_model=CompetitionGoalResponse)
def get_competition(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.query(CompetitionGoal).filter(CompetitionGoal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="No competition goal set")
    return CompetitionGoalResponse.model_validate(goal)


@router.post("", response_model=CompetitionGoalResponse, status_code=status.HTTP_201_CREATED)
def create_competition(
    data: CompetitionGoalCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(CompetitionGoal).filter(CompetitionGoal.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Competition goal already exists. Use PUT to update.")

    goal = CompetitionGoal(user_id=user.id, **data.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return CompetitionGoalResponse.model_validate(goal)


@router.put("", response_model=CompetitionGoalResponse)
def update_competition(
    data: CompetitionGoalUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(CompetitionGoal).filter(CompetitionGoal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="No competition goal to update")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return CompetitionGoalResponse.model_validate(goal)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_competition(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.query(CompetitionGoal).filter(CompetitionGoal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="No competition goal to delete")
    db.delete(goal)
    db.commit()
    return None


@router.post("/reset")
def reset_training(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Start over: delete competition goal + macrocycle + sessions.

    Keeps the profile (level, volume, equipment, days), tier/CSS stored
    client-side, feedback history and exercise logs.
    """
    db.query(TrainingSession).filter(TrainingSession.user_id == user.id).delete(synchronize_session=False)
    db.query(StrengthSession).filter(StrengthSession.user_id == user.id).delete(synchronize_session=False)
    db.query(MacrocyclePlan).filter(MacrocyclePlan.user_id == user.id).delete(synchronize_session=False)
    db.query(CompetitionGoal).filter(CompetitionGoal.user_id == user.id).delete(synchronize_session=False)
    db.commit()
    return {"message": "Training plan cleared. Profile, feedback and logs kept."}


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_macrocycle(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate full macrocycle from competition goal."""
    goal = db.query(CompetitionGoal).filter(CompetitionGoal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="No competition goal set")
    
    profile = user.profile
    if not profile:
        raise HTTPException(status_code=400, detail="Complete profile first")
    
    from ..services.macrocycle_calculator import calculate_macrocycle
    from ..services.swim_generator import generate_weekly_swim_plan
    from ..services.strength_generator import generate_weekly_strength_plan
    
    macro = calculate_macrocycle(
        competition_date=goal.competition_date,
        competition_type=goal.competition_type,
        pool_events=goal.pool_events,
        ow_distance_km=goal.ow_distance_km
    )
    
    # Save macrocycle (idempotent: wipe previous plan + sessions first so
    # retries/double-clicks never duplicate sessions)
    db.query(TrainingSession).filter(TrainingSession.user_id == user.id).delete(synchronize_session=False)
    db.query(StrengthSession).filter(StrengthSession.user_id == user.id).delete(synchronize_session=False)
    existing = db.query(MacrocyclePlan).filter(MacrocyclePlan.user_id == user.id).first()
    if existing:
        db.delete(existing)
    
    macrocycle = MacrocyclePlan(
        user_id=user.id,
        competition_goal_id=goal.id,
        total_weeks=macro.total_weeks,
        phases=macro.phases
    )
    db.add(macrocycle)
    db.commit()
    db.refresh(macrocycle)
    
    # Generate all sessions
    _generate_all_sessions(user, macro, profile, goal, db)
    
    return {"message": "Macrocycle generated", "total_weeks": macro.total_weeks, "phases": len(macro.phases)}


def _generate_all_sessions(
    user: User,
    macro: MacrocyclePlan,
    profile,
    goal: CompetitionGoal,
    db: Session
):
    """Generate all swim and strength sessions for the macrocycle."""
    today = date.today()
    week_start = macro.start_date
    
    from ..services.swim_generator import generate_weekly_swim_plan
    from ..services.strength_generator import generate_weekly_strength_plan
    
    for week_offset in range(macro.total_weeks):
        week_relative = week_offset - macro.total_weeks
        phase = get_phase_for_week(macro.phases, week_relative)
        
        # Generate swim sessions
        swim_sessions = generate_weekly_swim_plan(
            week_start=week_start,
            week_relative=week_relative,
            macrocycle_phases=macro.phases,
            profile={
                "level": profile.level,
                "swim_days_per_week": profile.swim_days_per_week,
                "target_volume_per_session": profile.target_volume_per_session,
                "available_equipment": profile.available_equipment,
                "preferred_strokes": profile.preferred_strokes,
                "ftp_pace_per_100": profile.ftp_pace_per_100,
                "session_duration_min": profile.session_duration_min,
                "available_days": profile.available_days
            },
            competition_type=goal.competition_type,
            pool_events=goal.pool_events,
            ow_distance_km=goal.ow_distance_km
        )
        
        # Save swim sessions
        for sess in swim_sessions:
            db_session = TrainingSession(
                user_id=user.id,
                date=date.fromisoformat(sess["date"]),
                week_relative=sess["week_relative"],
                phase_name=sess["phase_name"],
                total_meters=sess["total_meters"],
                estimated_duration_min=sess["estimated_duration_min"],
                focus=sess["focus"],
                rpe_target=sess["rpe_target"],
                warmup=sess["warmup"],
                main_set=sess["main_set"],
                cooldown=sess["cooldown"],
                generated_by=sess["generated_by"],
                parameters_snapshot=sess["parameters_snapshot"]
            )
            db.add(db_session)
        
        # Generate strength sessions
        swim_days = [date.fromisoformat(s["date"]).weekday() for s in swim_sessions]
        strength_sessions = generate_weekly_strength_plan(
            week_start=week_start,
            week_relative=week_relative,
            macrocycle_phases=macro.phases,
            profile={
                "available_equipment": profile.available_equipment,
                "level": profile.level,
                "strength_days": getattr(profile, "strength_days", None) or []
            },
            swim_days=swim_days,
            requested_per_week=goal.strength_days_per_week or 2
        )
        
        # Save strength sessions
        for sess in strength_sessions:
            db_session = StrengthSession(
                user_id=user.id,
                date=date.fromisoformat(sess["date"]),
                week_relative=sess["week_relative"],
                phase_name=sess["phase_name"],
                focus=sess["focus"],
                exercises=sess["exercises"],
                estimated_duration_min=sess["estimated_duration_min"],
                equipment_needed=sess["equipment_needed"]
            )
            db.add(db_session)
        
        week_start += timedelta(weeks=1)
    
    db.commit()