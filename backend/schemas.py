from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from enum import Enum


class UserRole(str, Enum):
    ATHLETE = "athlete"


class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"


class SubscriptionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class CompetitionType(str, Enum):
    POOL = "pool"
    OPEN_WATER = "open_water"


class Level(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PrimaryGoal(str, Enum):
    ENDURANCE = "endurance"
    SPEED = "speed"
    TECHNIQUE = "technique"
    MIXED = "mixed"


class OWConditions(str, Enum):
    POOL_LIKE = "pool_like"
    CHOPPY = "choppy"
    COLD = "cold"
    WARM = "warm"


# Auth
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    subscription_tier: SubscriptionTier
    subscription_status: Optional[SubscriptionStatus] = None
    current_period_end: Optional[datetime] = None

    class Config:
        from_attributes = True


# Profile
class AthleteProfileBase(BaseModel):
    level: Level = Level.INTERMEDIATE
    swim_days_per_week: int = Field(ge=3, le=6, default=4)
    target_volume_per_session: int = Field(ge=1500, le=8000, default=3000)
    preferred_strokes: List[str] = Field(default=["freestyle"])
    available_equipment: List[str] = Field(default=[])
    primary_goal: PrimaryGoal = PrimaryGoal.ENDURANCE
    available_days: List[int] = Field(default=[1, 3, 5])
    strength_days: List[int] = Field(default=[])
    session_duration_min: int = Field(ge=45, le=150, default=90)
    ftp_pace_per_100: Optional[int] = Field(default=None, ge=60, le=300)
    injury_notes: str = ""


class AthleteProfileCreate(AthleteProfileBase):
    pass


class AthleteProfileUpdate(AthleteProfileBase):
    level: Optional[Level] = None
    swim_days_per_week: Optional[int] = Field(default=None, ge=3, le=6)
    target_volume_per_session: Optional[int] = Field(default=None, ge=1500, le=8000)
    preferred_strokes: Optional[List[str]] = None
    available_equipment: Optional[List[str]] = None
    primary_goal: Optional[PrimaryGoal] = None
    available_days: Optional[List[int]] = None
    strength_days: Optional[List[int]] = None
    session_duration_min: Optional[int] = Field(default=None, ge=45, le=150)
    ftp_pace_per_100: Optional[int] = Field(default=None, ge=60, le=300)
    injury_notes: Optional[str] = None


class AthleteProfileResponse(AthleteProfileBase):
    id: int
    user_id: int
    strength_days: Optional[List[int]] = None

    class Config:
        from_attributes = True


# Competition
class CompetitionGoalBase(BaseModel):
    competition_date: date
    competition_type: CompetitionType
    pool_events: List[str] = Field(default=[])
    ow_distance_km: Optional[float] = Field(default=None, ge=1.5, le=50)
    ow_conditions: Optional[OWConditions] = None
    target_times: Dict[str, int] = Field(default={})
    strength_days_per_week: int = Field(ge=1, le=4, default=2)

    @field_validator("pool_events")
    @classmethod
    def validate_pool_events(cls, v, info):
        if info.data.get("competition_type") == CompetitionType.POOL and not v:
            raise ValueError("Pool events required for pool competition")
        return v

    @field_validator("ow_distance_km")
    @classmethod
    def validate_ow_distance(cls, v, info):
        if info.data.get("competition_type") == CompetitionType.OPEN_WATER and not v:
            raise ValueError("Open water distance required")
        return v


class CompetitionGoalCreate(CompetitionGoalBase):
    pass


class CompetitionGoalUpdate(BaseModel):
    competition_date: Optional[date] = None
    competition_type: Optional[CompetitionType] = None
    pool_events: Optional[List[str]] = None
    ow_distance_km: Optional[float] = None
    ow_conditions: Optional[OWConditions] = None
    target_times: Optional[Dict[str, int]] = None
    strength_days_per_week: Optional[int] = Field(default=None, ge=1, le=4)


class CompetitionGoalResponse(CompetitionGoalBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Plan
class SetSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    set_id: str
    description: str
    meters: int
    reps: int
    distance: int
    stroke: str
    target_pace_per_100: Optional[int] = None
    rest_seconds: int
    equipment: List[str] = []
    intensity_zone: str
    notes: str = ""


class WarmupSchema(BaseModel):
    meters: int
    description: str
    drills: List[str] = []


class CooldownSchema(BaseModel):
    meters: int
    description: str


class TrainingSessionResponse(BaseModel):
    id: int
    date: date
    week_relative: int
    phase_name: str
    total_meters: int
    estimated_duration_min: int
    focus: Optional[str] = None
    rpe_target: int
    warmup: WarmupSchema
    main_set: List[SetSchema]
    cooldown: CooldownSchema
    is_completed: bool

    class Config:
        from_attributes = True


class StrengthExerciseSchema(BaseModel):
    name: str
    sets: int
    reps: Optional[str] = None
    duration: Optional[int] = None
    rpe: int
    tempo: Optional[str] = None
    rest: int = 60
    progression: str = ""


class StrengthSessionResponse(BaseModel):
    id: int
    date: date
    week_relative: int
    phase_name: str
    focus: str
    exercises: List[StrengthExerciseSchema]
    estimated_duration_min: int
    equipment_needed: List[str]
    is_completed: bool

    class Config:
        from_attributes = True


class WeekPlanResponse(BaseModel):
    week_start: date
    swim_sessions: List[TrainingSessionResponse]
    strength_sessions: List[StrengthSessionResponse]


class TodayPlanResponse(BaseModel):
    date: date
    swim: Optional[TrainingSessionResponse] = None
    strength: Optional[StrengthSessionResponse] = None


class MacrocyclePhaseSchema(BaseModel):
    name: str
    start_week: int
    end_week: int
    swim_focus: str
    strength_focus: str
    swim_volume_mult: float
    strength_days: int


class MacrocycleResponse(BaseModel):
    id: int
    total_weeks: int
    phases: List[MacrocyclePhaseSchema]
    generated_at: datetime

    class Config:
        from_attributes = True


# Feedback
class DailyFeedbackCreate(BaseModel):
    date: date
    swim_feeling: Optional[int] = Field(default=None, ge=1, le=5)
    swim_completed: bool = False
    swim_completed_meters: Optional[int] = None
    strength_feeling: Optional[int] = Field(default=None, ge=1, le=5)
    strength_completed: bool = False
    comments: str = ""


class DailyFeedbackResponse(BaseModel):
    id: int
    date: date
    swim_feeling: Optional[int] = None
    swim_completed: bool
    swim_completed_meters: Optional[int] = None
    strength_feeling: Optional[int] = None
    strength_completed: bool
    comments: str
    readiness_score: Optional[int] = None

    class Config:
        from_attributes = True


class FeedbackHistoryResponse(BaseModel):
    items: List[DailyFeedbackResponse]
    total: int
    page: int
    page_size: int


# Stats
class StatsSummaryResponse(BaseModel):
    weekly_volume: int
    weekly_swim_sessions: int
    weekly_strength_sessions: int
    avg_swim_feeling: Optional[float] = None
    avg_strength_feeling: Optional[float] = None
    completion_rate: float


class ReadinessResponse(BaseModel):
    score: int
    breakdown: Dict[str, int]
    trend: str
    recommendation: str


# Subscription
class CheckoutResponse(BaseModel):
    init_point: str
    preapproval_id: str


class PortalResponse(BaseModel):
    portal_url: str


class TierCheckResponse(BaseModel):
    tier: SubscriptionTier
    features: Dict[str, bool]