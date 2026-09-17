from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, MacrocyclePlan, TrainingSession, StrengthSession
from backend.schemas import (
    WeekPlanResponse, TodayPlanResponse, MacrocycleResponse,
    MacrocyclePhaseSchema, TrainingSessionResponse, StrengthSessionResponse
)
from backend.auth import get_current_user

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
