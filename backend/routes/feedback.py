from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import User, DailyFeedback, TrainingSession, StrengthSession
from backend.schemas import DailyFeedbackCreate, DailyFeedbackResponse, FeedbackHistoryResponse
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