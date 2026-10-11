from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..config import get_settings
from ..database import get_db
from ..models import User, SubscriptionTier
from ..schemas import UserRegister, UserLogin, Token, UserResponse, PasswordChange, AdminResetRequest, AdminResetResponse
from ..auth import (
    verify_password, get_password_hash, create_access_token,
    set_auth_cookie, clear_auth_cookie, get_current_user, require_admin
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


@router.post("/change-password")
def change_password(
    data: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logged-in user changes their own password (knows the current one)."""
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password updated"}


@router.post("/admin-reset-password", response_model=AdminResetResponse)
def admin_reset_password(
    data: AdminResetRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Owner generates a one-time temp password for a user (no email infra).
    Shown ONCE in the response — pass it via a secure channel; the user
    then sets their own via change-password."""
    import secrets
    import string
    target = db.query(User).filter(User.email == data.email).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    alphabet = string.ascii_letters + string.digits
    temp = "".join(secrets.choice(alphabet) for _ in range(12))
    target.hashed_password = get_password_hash(temp)
    db.commit()
    return AdminResetResponse(email=target.email, temp_password=temp)


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