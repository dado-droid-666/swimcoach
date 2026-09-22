from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import User, DailyFeedback, TrainingSession, StrengthSession, ExerciseLog
from backend.schemas import (
    DailyFeedbackCreate, DailyFeedbackResponse, FeedbackHistoryResponse,
    ExerciseLogBatch, ExerciseLogResponse,
)
from backend.auth import get_current_user

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=DailyFeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    data: DailyFeedbackCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit or update daily feedback (swim + strength)."""
    # Check if feedback already exists for this date
    existing = db.query(DailyFeedback).filter(
        DailyFeedback.user_id == user.id,
        DailyFeedback.date == data.date
    ).first()
    
    if existing:
        # Update existing
        existing.swim_feeling = data.swim_feeling
        existing.swim_completed = data.swim_completed
        existing.swim_completed_meters = data.swim_completed_meters
        existing.strength_feeling = data.strength_feeling
        existing.strength_completed = data.strength_completed
        existing.comments = data.comments
        db.commit()
        db.refresh(existing)
        return DailyFeedbackResponse.model_validate(existing)
    
    # Create new
    feedback = DailyFeedback(
        user_id=user.id,
        date=data.date,
        swim_feeling=data.swim_feeling,
        swim_completed=data.swim_completed,
        swim_completed_meters=data.swim_completed_meters,
        strength_feeling=data.strength_feeling,
        strength_completed=data.strength_completed,
        comments=data.comments
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return DailyFeedbackResponse.model_validate(feedback)


@router.get("/history", response_model=FeedbackHistoryResponse)
def get_feedback_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated feedback history."""
    from backend.models import User as UserModel
    
    # Free tier: last 30 days only
    is_pro = user.subscription_tier.value == "pro"
    
    query = db.query(DailyFeedback).filter(DailyFeedback.user_id == user.id)
    
    if not is_pro:
        from datetime import date, timedelta
        cutoff = date.today() - timedelta(days=30)
        query = query.filter(DailyFeedback.date >= cutoff)
    
    total = query.count()
    
    items = query.order_by(desc(DailyFeedback.date)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return FeedbackHistoryResponse(
        items=[DailyFeedbackResponse.model_validate(f) for f in items],
        total=total,
        page=page,
        page_size=page_size
    )


# NOTE: /logs/* must be declared BEFORE /{date} or the path param swallows them.
@router.post("/logs", response_model=List[ExerciseLogResponse], status_code=status.HTTP_201_CREATED)
def submit_exercise_logs(
    data: ExerciseLogBatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit per-exercise logs (weight/reps/time + effort 1-5). ML data."""
    out = []
    for item in data.logs:
        row = ExerciseLog(
            user_id=user.id,
            date=item.date,
            session_type=item.session_type,
            exercise_name=item.exercise_name,
            weight_kg=item.weight_kg,
            reps=item.reps,
            time_seg=item.time_seg,
            effort=item.effort,
        )
        db.add(row)
        out.append(row)
    db.commit()
    for row in out:
        db.refresh(row)
    return [ExerciseLogResponse.model_validate(r) for r in out]


@router.get("/logs/history", response_model=List[ExerciseLogResponse])
def get_exercise_logs(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recent per-exercise logs (newest first)."""
    q = db.query(ExerciseLog).filter(ExerciseLog.user_id == user.id)
    if date_from:
        q = q.filter(ExerciseLog.date >= date_from)
    if date_to:
        q = q.filter(ExerciseLog.date <= date_to)
    rows = q.order_by(desc(ExerciseLog.date), desc(ExerciseLog.id)).limit(limit).all()
    return [ExerciseLogResponse.model_validate(r) for r in rows]


@router.get("/{date}", response_model=DailyFeedbackResponse)
def get_feedback(
    date: date,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get feedback for a specific date."""
    feedback = db.query(DailyFeedback).filter(
        DailyFeedback.user_id == user.id,
        DailyFeedback.date == date
    ).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="No feedback for this date")
    
    return DailyFeedbackResponse.model_validate(feedback)