from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..config import get_settings
from ..database import get_db
from ..models import User, SubscriptionTier
from ..schemas import UserRegister, UserLogin, Token, UserResponse
from ..auth import (
    verify_password, get_password_hash, create_access_token,
    set_auth_cookie, clear_auth_cookie, get_current_user
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed,
        full_name=user_data.full_name,
        subscription_tier=SubscriptionTier.FREE,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Registration failed")

    token = create_access_token({"sub": user.id, "email": user.email})
    set_auth_cookie(response, token)

    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    token = create_access_token({"sub": user.id, "email": user.email})
    set_auth_cookie(response, token)

    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/logout")
def logout(response: Response):
    clear_auth_cookie(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.delete("/account")
def delete_account(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete the account and ALL its data (irreversible)."""
    from ..models import (
        AthleteProfile, CompetitionGoal, MacrocyclePlan,
        TrainingSession, StrengthSession, DailyFeedback, ExerciseLog,
    )
    uid = user.id
    db.query(ExerciseLog).filter(ExerciseLog.user_id == uid).delete(synchronize_session=False)
    db.query(DailyFeedback).filter(DailyFeedback.user_id == uid).delete(synchronize_session=False)
    db.query(TrainingSession).filter(TrainingSession.user_id == uid).delete(synchronize_session=False)
    db.query(StrengthSession).filter(StrengthSession.user_id == uid).delete(synchronize_session=False)
    db.query(MacrocyclePlan).filter(MacrocyclePlan.user_id == uid).delete(synchronize_session=False)
    db.query(CompetitionGoal).filter(CompetitionGoal.user_id == uid).delete(synchronize_session=False)
    db.query(AthleteProfile).filter(AthleteProfile.user_id == uid).delete(synchronize_session=False)
    db.query(User).filter(User.id == uid).delete(synchronize_session=False)
    db.commit()
    clear_auth_cookie(response)
    return {"message": "Account deleted"}