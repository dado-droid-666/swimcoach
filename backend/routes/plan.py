from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, MacrocyclePlan, TrainingSession, StrengthSession
from backend.schemas import (
    WeekPlanResponse, TodayPlanResponse, MacrocycleResponse,
    MacrocyclePhaseSchema, TrainingSessionResponse, StrengthSessionResponse
)
from backend.auth import get_current_user, require_pro

router = APIRouter(prefix="/api/plan", tags=["plan"])


# NOTE: macrocycle generation lives in backend/routes/competition.py
# (POST /api/competition/generate). The duplicate POST
# /api/plan/competition/generate was removed to avoid double maintenance.


@router.get("/macrocycle", response_model=MacrocycleResponse)
def get_macrocycle(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full macrocycle overview."""
    macrocycle = db.query(MacrocyclePlan).filter(MacrocyclePlan.user_id == user.id).first()
    if not macrocycle:
        raise HTTPException(status_code=404, detail="No macrocycle generated")

    phases = []
    for p in macrocycle.phases:
        phases.append(MacrocyclePhaseSchema(
            name=p["name"],
            start_week=p["start_week"],
            end_week=p["end_week"],
            swim_focus=p["swim_focus"],
            strength_focus=p["strength_focus"],
            swim_volume_mult=p["swim_volume_mult"],
            strength_days=p["strength_days"]
        ))

    return MacrocycleResponse(
        id=macrocycle.id,
        total_weeks=macrocycle.total_weeks,
        phases=phases,
        generated_at=macrocycle.generated_at
    )


@router.get("/week", response_model=WeekPlanResponse)
def get_week_plan(
    start: date = Query(..., description="Week start date (Monday)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get swim + strength sessions for a specific week."""
    week_end = start + timedelta(days=6)

    swim_sessions = db.query(TrainingSession).filter(
        TrainingSession.user_id == user.id,
        TrainingSession.date >= start,
        TrainingSession.date <= week_end
    ).order_by(TrainingSession.date).all()

    strength_sessions = db.query(StrengthSession).filter(
        StrengthSession.user_id == user.id,
        StrengthSession.date >= start,
        StrengthSession.date <= week_end
    ).order_by(StrengthSession.date).all()

    return WeekPlanResponse(
        week_start=start,
        swim_sessions=[TrainingSessionResponse.model_validate(s) for s in swim_sessions],
        strength_sessions=[StrengthSessionResponse.model_validate(s) for s in strength_sessions]
    )


@router.get("/today", response_model=TodayPlanResponse)
def get_today_plan(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's swim + strength session."""
    today = date.today()

    swim = db.query(TrainingSession).filter(
        TrainingSession.user_id == user.id,
        TrainingSession.date == today
    ).first()

    strength = db.query(StrengthSession).filter(
        StrengthSession.user_id == user.id,
        StrengthSession.date == today
    ).first()

    return TodayPlanResponse(
        date=today,
        swim=TrainingSessionResponse.model_validate(swim) if swim else None,
        strength=StrengthSessionResponse.model_validate(strength) if strength else None
    )


@router.put("/session/move")
def move_session(
    session_type: str = Query(..., pattern="^(swim|strength)$"),
    session_id: int = Query(...),
    date: date = Query(..., description="New date (YYYY-MM-DD)"),
    user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Move a swim/strength session to another day (Pro).

    Fails with 409 if the target day already has a session of that type.
    """
    model = TrainingSession if session_type == "swim" else StrengthSession
    sess = db.query(model).filter(model.id == session_id, model.user_id == user.id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    clash = db.query(model).filter(
        model.user_id == user.id, model.date == date, model.id != session_id
    ).first()
    if clash:
        raise HTTPException(
            status_code=409,
            detail=f"Target day already has a {session_type} session",
        )
    sess.date = date
    db.commit()
    db.refresh(sess)
    if session_type == "swim":
        return TrainingSessionResponse.model_validate(sess)
    return StrengthSessionResponse.model_validate(sess)


@router.post("/week/regenerate")
def regenerate_week(
    start: date = Query(..., description="Week start date (Monday)"),
    user: User = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """Delete and regenerate one week of swim+strength sessions (Pro)."""
    from backend.models import CompetitionGoal
    from backend.services.macrocycle_calculator import calculate_macrocycle, get_phase_for_week
    from backend.services.swim_generator import generate_weekly_swim_plan
    from backend.services.strength_generator import generate_weekly_strength_plan

    goal = db.query(CompetitionGoal).filter(CompetitionGoal.user_id == user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="No competition goal set")
    profile = user.profile
    if not profile:
        raise HTTPException(status_code=400, detail="Complete profile first")
    macrocycle = db.query(MacrocyclePlan).filter(MacrocyclePlan.user_id == user.id).first()
    if not macrocycle:
        raise HTTPException(status_code=404, detail="No macrocycle generated")

    week_end = start + timedelta(days=6)
    macro = calculate_macrocycle(
        competition_date=goal.competition_date,
        competition_type=goal.competition_type,
        pool_events=goal.pool_events,
        ow_distance_km=goal.ow_distance_km,
    )
    week_offset = (start - macro.start_date).days // 7
    week_relative = week_offset - macro.total_weeks
    phase = get_phase_for_week(macro.phases, week_relative)

    db.query(TrainingSession).filter(
        TrainingSession.user_id == user.id,
        TrainingSession.date >= start,
        TrainingSession.date <= week_end,
    ).delete(synchronize_session=False)
    db.query(StrengthSession).filter(
        StrengthSession.user_id == user.id,
        StrengthSession.date >= start,
        StrengthSession.date <= week_end,
    ).delete(synchronize_session=False)

    swim_sessions = generate_weekly_swim_plan(
        week_start=start,
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
            "available_days": profile.available_days,
        },
        competition_type=goal.competition_type,
        pool_events=goal.pool_events,
        ow_distance_km=goal.ow_distance_km,
    )
    for sess in swim_sessions:
        db.add(TrainingSession(
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
        week_start=start,
        week_relative=week_relative,
        macrocycle_phases=macro.phases,
        profile={
            "available_equipment": profile.available_equipment,
            "level": profile.level,
            "strength_days": getattr(profile, "strength_days", None) or [],
        },
        swim_days=swim_days,
        requested_per_week=goal.strength_days_per_week or 2,
    )
    for sess in strength_sessions:
        db.add(StrengthSession(
            user_id=user.id,
            date=date.fromisoformat(sess["date"]),
            week_relative=sess["week_relative"],
            phase_name=sess["phase_name"],
            focus=sess["focus"],
            exercises=sess["exercises"],
            estimated_duration_min=sess["estimated_duration_min"],
            equipment_needed=sess["equipment_needed"],
        ))
    db.commit()
    return {"message": "Week regenerated", "week_start": start.isoformat(),
            "swim_sessions": len(swim_sessions), "strength_sessions": len(strength_sessions)}
