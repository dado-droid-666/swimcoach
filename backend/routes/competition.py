import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CompetitionGoal, User, MacrocyclePlan, TrainingSession, StrengthSession
from ..schemas import CompetitionGoalCreate, CompetitionGoalUpdate, CompetitionGoalResponse
from ..auth import get_current_user
from ..services.macrocycle_calculator import calculate_macrocycle
from ..services.swim_generator import generate_weekly_swim_plan
from ..services.strength_generator import generate_weekly_strength_plan

router = APIRouter(prefix="/api/competition", tags=["competition"])
logger = logging.getLogger(__name__)


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


def _as_list(value, default):
    """Legacy rows may hold NULL where the model expects JSON arrays."""
    return value if isinstance(value, list) and value else list(default)


def _as_weekdays(value, default):
    """Keep only valid Mon=0..Sun=6 ints (legacy rows may hold strings)."""
    if not isinstance(value, list):
        return list(default)
    days = []
    for raw in value:
        try:
            day = int(raw)
        except (TypeError, ValueError):
            continue
        if 0 <= day <= 6 and day not in days:
            days.append(day)
    return days or list(default)


def _as_level(value):
    level = str(value or "intermediate").lower()
    return level if level in ("beginner", "intermediate", "advanced") else "intermediate"


def _profile_snapshot(profile) -> dict:
    """Normalize profile fields the generators read.

    Old accounts can have NULL JSON/integer columns (defaults only apply on
    INSERT, not to rows created before the column existed). Never let a
    legacy row turn plan generation into a 500.
    """
    return {
        "level": _as_level(profile.level),
        "swim_days_per_week": profile.swim_days_per_week or 4,
        "target_volume_per_session": profile.target_volume_per_session or 3000,
        "available_equipment": _as_list(profile.available_equipment, []),
        "preferred_strokes": _as_list(profile.preferred_strokes, ["freestyle"]),
        "ftp_pace_per_100": profile.ftp_pace_per_100,
        "session_duration_min": profile.session_duration_min or 90,
        "available_days": _as_weekdays(profile.available_days, [1, 3, 5]),
        "strength_days": _as_weekdays(profile.strength_days, []),
    }


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_macrocycle(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a full macrocycle atomically.

    All sessions are built in memory first. Only when every week generated
    successfully do we replace the old plan in a single transaction. A
    generator bug can no longer wipe the athlete's existing plan or leave a
    half-populated macrocycle behind.
    """
    goal = db.query(CompetitionGoal).filter(CompetitionGoal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="No competition goal set")

    profile = user.profile
    if not profile:
        raise HTTPException(status_code=400, detail="Complete profile first")

    macro = calculate_macrocycle(
        competition_date=goal.competition_date,
        competition_type=goal.competition_type,
        pool_events=goal.pool_events or [],
        ow_distance_km=goal.ow_distance_km,
    )
    profile_data = _profile_snapshot(profile)

    logger.info(
        "macrocycle_generate_start user_id=%s weeks=%s competition=%s",
        user.id, macro.total_weeks, goal.competition_date.isoformat(),
    )
    try:
        swim_rows, strength_rows = _build_all_sessions(
            user, macro, profile, profile_data, goal, db
        )

        # Replace atomically: delete + insert + macrocycle in one commit.
        # If anything fails before this point, the old plan is untouched.
        db.query(TrainingSession).filter(
            TrainingSession.user_id == user.id
        ).delete(synchronize_session=False)
        db.query(StrengthSession).filter(
            StrengthSession.user_id == user.id
        ).delete(synchronize_session=False)
        existing = db.query(MacrocyclePlan).filter(
            MacrocyclePlan.user_id == user.id
        ).first()
        if existing:
            db.delete(existing)

        db.add(MacrocyclePlan(
            user_id=user.id,
            competition_goal_id=goal.id,
            total_weeks=macro.total_weeks,
            phases=macro.phases,
        ))
        db.add_all(swim_rows)
        db.add_all(strength_rows)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "macrocycle_generate_failed user_id=%s weeks=%s",
            user.id, macro.total_weeks,
        )
        raise

    logger.info(
        "macrocycle_generate_done user_id=%s swim=%s strength=%s",
        user.id, len(swim_rows), len(strength_rows),
    )
    return {
        "message": "Macrocycle generated",
        "total_weeks": macro.total_weeks,
        "phases": len(macro.phases),
    }


def _build_all_sessions(
    user: User,
    macro: MacrocyclePlan,
    profile,
    profile_data: dict,
    goal: CompetitionGoal,
    db: Session,
):
    """Build every swim/strength row in memory without touching the old plan."""
    today = date.today()
    week_start = macro.start_date
    swim_rows = []
    strength_rows = []

    from ..services.adaptive_state import build_week_adaptive

    for week_offset in range(macro.total_weeks):
        week_relative = week_offset - macro.total_weeks

        # Los generadores normalizan al lunes dentro de cada bloque de 7
        # dias (los dias del atleta son weekdays y la vista es Lun-Dom).
        # El estado adaptativo usa el mismo lunes para decidir si la semana
        # es actual/futura (aplica) o pasada (planificada).
        week_monday = week_start + timedelta(days=(7 - week_start.weekday()) % 7)
        adaptive = build_week_adaptive(
            db, user.id, profile, goal, week_monday, today
        )

        swim_sessions = generate_weekly_swim_plan(
            week_start=week_start,
            week_relative=week_relative,
            macrocycle_phases=macro.phases,
            profile=profile_data,
            competition_type=goal.competition_type,
            pool_events=goal.pool_events or [],
            ow_distance_km=goal.ow_distance_km,
            adaptive=adaptive,
        )
        for sess in swim_sessions:
            swim_rows.append(TrainingSession(
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
                parameters_snapshot=sess["parameters_snapshot"],
            ))

        swim_days = [date.fromisoformat(s["date"]).weekday() for s in swim_sessions]
        strength_sessions = generate_weekly_strength_plan(
            week_start=week_start,
            week_relative=week_relative,
            macrocycle_phases=macro.phases,
            profile={
                "available_equipment": profile_data["available_equipment"],
                "level": profile_data["level"],
                "strength_days": profile_data["strength_days"],
            },
            swim_days=swim_days,
            requested_per_week=goal.strength_days_per_week or 2,
            adaptive=adaptive,
        )
        for sess in strength_sessions:
            strength_rows.append(StrengthSession(
                user_id=user.id,
                date=date.fromisoformat(sess["date"]),
                week_relative=sess["week_relative"],
                phase_name=sess["phase_name"],
                focus=sess["focus"],
                exercises=sess["exercises"],
                estimated_duration_min=sess["estimated_duration_min"],
                equipment_needed=sess["equipment_needed"],
            ))

        week_start += timedelta(weeks=1)

    return swim_rows, strength_rows