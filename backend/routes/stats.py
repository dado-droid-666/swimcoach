from datetime import date, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from backend.database import get_db
from backend.models import User, DailyFeedback, TrainingSession, StrengthSession, MacrocyclePlan
from backend.schemas import StatsSummaryResponse, ReadinessResponse
from backend.auth import get_current_user, require_pro

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary", response_model=StatsSummaryResponse)
def get_stats_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly summary stats (available to all tiers)."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Weekly volume (swim)
    swim_sessions = db.query(TrainingSession).filter(
        TrainingSession.user_id == user.id,
        TrainingSession.date >= week_start,
        TrainingSession.date <= week_end
    ).all()
    
    weekly_volume = sum(s.total_meters for s in swim_sessions)
    weekly_swim_sessions = len(swim_sessions)
    
    # Weekly strength sessions
    strength_sessions = db.query(StrengthSession).filter(
        StrengthSession.user_id == user.id,
        StrengthSession.date >= week_start,
        StrengthSession.date <= week_end
    ).all()
    weekly_strength_sessions = len(strength_sessions)
    
    # Feedback this week
    feedback = db.query(DailyFeedback).filter(
        DailyFeedback.user_id == user.id,
        DailyFeedback.date >= week_start,
        DailyFeedback.date <= week_end
    ).all()
    
    swim_feelings = [f.swim_feeling for f in feedback if f.swim_feeling is not None]
    strength_feelings = [f.strength_feeling for f in feedback if f.strength_feeling is not None]
    
    avg_swim_feeling = sum(swim_feelings) / len(swim_feelings) if swim_feelings else None
    avg_strength_feeling = sum(strength_feelings) / len(strength_feelings) if strength_feelings else None
    
    # Completion rate (planned vs completed)
    planned_swim = len([s for s in swim_sessions if not s.is_completed])
    completed_swim = len([s for s in swim_sessions if s.is_completed])
    total_planned = planned_swim + completed_swim
    
    planned_strength = len([s for s in strength_sessions if not s.is_completed])
    completed_strength = len([s for s in strength_sessions if s.is_completed])
    total_planned += planned_strength + completed_strength
    
    completed = completed_swim + completed_strength
    
    completion_rate = completed / total_planned if total_planned > 0 else 0.0
    
    return StatsSummaryResponse(
        weekly_volume=weekly_volume,
        weekly_swim_sessions=weekly_swim_sessions,
        weekly_strength_sessions=weekly_strength_sessions,
        avg_swim_feeling=round(avg_swim_feeling, 1) if avg_swim_feeling else None,
        avg_strength_feeling=round(avg_strength_feeling, 1) if avg_strength_feeling else None,
        completion_rate=round(completion_rate, 2)
    )


@router.get("/readiness", response_model=ReadinessResponse)
def get_readiness(
    user: User = Depends(require_pro),
    db: Session = Depends(get_db)
):
    """Get readiness score (Pro only)."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_ago = today - timedelta(days=28)
    
    # Get last 4 weeks of feedback
    feedback = db.query(DailyFeedback).filter(
        DailyFeedback.user_id == user.id,
        DailyFeedback.date >= month_ago
    ).order_by(DailyFeedback.date).all()
    
    if not feedback:
        return ReadinessResponse(
            score=50,
            breakdown={},
            trend="insufficient_data",
            recommendation="Complete at least 3 sessions with feedback to get readiness score"
        )
    
    # Calculate components
    recent = [f for f in feedback if f.date >= week_start]
    older = [f for f in feedback if f.date < week_start]
    
    # 1. Feeling trend (40%)
    recent_swim = [f.swim_feeling for f in recent if f.swim_feeling]
    recent_str = [f.strength_feeling for f in recent if f.strength_feeling]
    older_swim = [f.swim_feeling for f in older if f.swim_feeling]
    older_str = [f.strength_feeling for f in older if f.strength_feeling]
    
    recent_avg = 0
    if recent_swim or recent_str:
        recent_avg = (sum(recent_swim) + sum(recent_str)) / (len(recent_swim) + len(recent_str))
    
    older_avg = 0
    if older_swim or older_str:
        older_avg = (sum(older_swim) + sum(older_str)) / (len(older_swim) + len(older_str))
    
    feeling_score = min(100, max(0, recent_avg * 20))  # 1-5 -> 0-100
    trend_score = 50
    if older_avg > 0:
        if recent_avg > older_avg + 0.3:
            trend_score = 80
        elif recent_avg < older_avg - 0.3:
            trend_score = 30
        else:
            trend_score = 50
    
    # 2. Completion rate (30%)
    total_feedback = len(feedback)
    completed_sessions = sum(1 for f in feedback if f.swim_completed or f.strength_completed)
    completion_rate = completed_sessions / total_feedback if total_feedback > 0 else 0
    completion_score = completion_rate * 100
    
    # 3. Volume consistency (20%)
    # Check if volume is within ±20% of target
    macrocycle = db.query(MacrocyclePlan).filter(MacrocyclePlan.user_id == user.id).first()
    if macrocycle:
        # Simplified: assume on track if completed sessions match planned
        volume_score = 70  # Placeholder
    else:
        volume_score = 50
    
    # 4. Injury/illness flags (10%)
    injury_notes = [f.comments for f in feedback if f.comments and any(w in f.comments.lower() for w in ["dolor", "lesion", "injury", "pain", "hombro", "rodilla", "shoulder", "knee", "sick", "enfermo"])]
    injury_score = 100 if not injury_notes else 50
    
    # Weighted score
    score = int(
        feeling_score * 0.4 +
        trend_score * 0.15 +
        completion_score * 0.25 +
        volume_score * 0.15 +
        injury_score * 0.05
    )
    score = max(0, min(100, score))
    
    # Trend
    if recent_avg > older_avg + 0.2:
        trend = "improving"
    elif recent_avg < older_avg - 0.2:
        trend = "declining"
    else:
        trend = "stable"
    
    # Recommendation
    if score >= 80:
        recommendation = "Excellent readiness. Push hard this week!"
    elif score >= 65:
        recommendation = "Good readiness. Stick to the plan."
    elif score >= 50:
        recommendation = "Moderate readiness. Consider reducing intensity if feeling fatigued."
    else:
        recommendation = "Low readiness. Prioritize recovery, consider deload week."
    
    breakdown = {
        "feeling": int(feeling_score),
        "trend": int(trend_score),
        "completion": int(completion_score),
        "volume": int(volume_score),
        "injury_risk": int(injury_score)
    }
    
    return ReadinessResponse(
        score=score,
        breakdown=breakdown,
        trend=trend,
        recommendation=recommendation
    )


@router.get("/progress")
def get_progress(
    user: User = Depends(require_pro),
    db: Session = Depends(get_db)
):
    """Get progress charts data (Pro only)."""
    today = date.today()
    month_ago = today - timedelta(days=28)
    
    # Weekly volume trend (last 8 weeks)
    volume_data = []
    for i in range(8):
        week_start = today - timedelta(weeks=i+1, days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        sessions = db.query(TrainingSession).filter(
            TrainingSession.user_id == user.id,
            TrainingSession.date >= week_start,
            TrainingSession.date <= week_end
        ).all()
        
        week_volume = sum(s.total_meters for s in sessions)
        volume_data.append({
            "week_start": week_start.isoformat(),
            "volume": week_volume,
            "sessions": len(sessions)
        })
    
    # Feeling trend (last 4 weeks)
    feedback = db.query(DailyFeedback).filter(
        DailyFeedback.user_id == user.id,
        DailyFeedback.date >= month_ago
    ).order_by(DailyFeedback.date).all()
    
    feeling_data = []
    for f in feedback:
        if f.swim_feeling or f.strength_feeling:
            vals = []
            if f.swim_feeling: vals.append(f.swim_feeling)
            if f.strength_feeling: vals.append(f.strength_feeling)
            feeling_data.append({
                "date": f.date.isoformat(),
                "avg_feeling": round(sum(vals) / len(vals), 1),
                "swim_completed": f.swim_completed,
                "strength_completed": f.strength_completed
            })
    
    # Completion rate trend
    completion_data = []
    for i in range(4):
        week_start = today - timedelta(weeks=i+1, days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        week_feedback = [f for f in feedback if week_start <= f.date <= week_end]
        total = len(week_feedback)
        completed = sum(1 for f in week_feedback if f.swim_completed or f.strength_completed)
        rate = completed / total if total > 0 else 0
        
        completion_data.append({
            "week_start": week_start.isoformat(),
            "completion_rate": round(rate, 2),
            "total_sessions": total
        })
    
    return {
        "volume_trend": list(reversed(volume_data)),
        "feeling_trend": feeling_data,
        "completion_trend": list(reversed(completion_data))
    }