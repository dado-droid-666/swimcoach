from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AthleteProfile, User
from ..schemas import AthleteProfileCreate, AthleteProfileUpdate, AthleteProfileResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=AthleteProfileResponse)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(AthleteProfile).filter(AthleteProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Complete onboarding.")
    return AthleteProfileResponse.model_validate(profile)


@router.put("", response_model=AthleteProfileResponse)
def update_profile(
    data: AthleteProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(AthleteProfile).filter(AthleteProfile.user_id == user.id).first()
    if not profile:
        profile = AthleteProfile(user_id=user.id, **data.model_dump(exclude_unset=True))
        db.add(profile)
    else:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return AthleteProfileResponse.model_validate(profile)


@router.post("", response_model=AthleteProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    data: AthleteProfileCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(AthleteProfile).filter(AthleteProfile.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists. Use PUT to update.")

    profile = AthleteProfile(user_id=user.id, **data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return AthleteProfileResponse.model_validate(profile)