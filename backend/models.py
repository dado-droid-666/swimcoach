from datetime import datetime, date
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Boolean,
    ForeignKey, Enum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship

from .database import Base


class UserRole(str, PyEnum):
    ATHLETE = "athlete"


class SubscriptionTier(str, PyEnum):
    FREE = "free"
    PRO = "pro"


class SubscriptionStatus(str, PyEnum):
    PENDING = "pending"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class CompetitionType(str, PyEnum):
    POOL = "pool"
    OPEN_WATER = "open_water"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    mp_customer_id = Column(String(255), nullable=True)
    mp_preapproval_id = Column(String(255), nullable=True)
    mp_subscription_id = Column(String(255), nullable=True)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING)
    current_period_end = Column(DateTime, nullable=True)

    profile = relationship("AthleteProfile", back_populates="user", uselist=False)
    competition_goal = relationship("CompetitionGoal", back_populates="user", uselist=False)
    macrocycle = relationship("MacrocyclePlan", back_populates="user", uselist=False)
    swim_sessions = relationship("TrainingSession", back_populates="user")
    strength_sessions = relationship("StrengthSession", back_populates="user")
    feedback = relationship("DailyFeedback", back_populates="user")


class AthleteProfile(Base):
    __tablename__ = "athlete_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    level = Column(String(20), default="intermediate")
    swim_days_per_week = Column(Integer, default=4)
    target_volume_per_session = Column(Integer, default=3000)
    preferred_strokes = Column(JSON, default=["freestyle"])
    available_equipment = Column(JSON, default=[])
    primary_goal = Column(String(20), default="endurance")
    available_days = Column(JSON, default=[1, 3, 5])
    strength_days = Column(JSON, default=[])  # preferred strength weekdays Mon=0..Sun=6; [] = auto
    session_duration_min = Column(Integer, default=90)
    ftp_pace_per_100 = Column(Integer, nullable=True)
    injury_notes = Column(Text, default="")

    user = relationship("User", back_populates="profile")


class CompetitionGoal(Base):
    __tablename__ = "competition_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    competition_date = Column(Date, nullable=False)
    competition_type = Column(Enum(CompetitionType), nullable=False)
    pool_events = Column(JSON, default=[])
    ow_distance_km = Column(Integer, nullable=True)
    ow_conditions = Column(String(20), nullable=True)
    target_times = Column(JSON, default={})
    strength_days_per_week = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="competition_goal")


class MacrocyclePlan(Base):
    __tablename__ = "macrocycle_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competition_goal_id = Column(Integer, ForeignKey("competition_goals.id"), nullable=False)

    total_weeks = Column(Integer, nullable=False)
    phases = Column(JSON, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="macrocycle")
    competition_goal = relationship("CompetitionGoal")


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    week_relative = Column(Integer, nullable=False)
    phase_name = Column(String(20), nullable=False)

    total_meters = Column(Integer, default=0)
    estimated_duration_min = Column(Integer, default=0)
    focus = Column(String(50), nullable=True)
    rpe_target = Column(Integer, default=6)

    warmup = Column(JSON, default={})
    main_set = Column(JSON, default=[])
    cooldown = Column(JSON, default={})

    generated_by = Column(String(20), default="macrocycle_v1")
    parameters_snapshot = Column(JSON, default={})
    is_completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="swim_sessions")


class StrengthSession(Base):
    __tablename__ = "strength_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    week_relative = Column(Integer, nullable=False)
    phase_name = Column(String(20), nullable=False)

    focus = Column(String(50), nullable=False)
    exercises = Column(JSON, default=[])
    estimated_duration_min = Column(Integer, default=30)
    equipment_needed = Column(JSON, default=[])
    is_completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="strength_sessions")


class DailyFeedback(Base):
    __tablename__ = "daily_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    swim_feeling = Column(Integer, nullable=True)
    swim_completed = Column(Boolean, default=False)
    swim_completed_meters = Column(Integer, nullable=True)

    strength_feeling = Column(Integer, nullable=True)
    strength_completed = Column(Boolean, default=False)

    comments = Column(Text, default="")
    readiness_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feedback")