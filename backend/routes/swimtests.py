from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import User, SwimTest
from backend.schemas import SwimTestCreate, SwimTestResponse
from backend.auth import get_current_user

router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.post("", response_model=SwimTestResponse, status_code=status.HTTP_201_CREATED)
def save_test(
    data: SwimTestCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a CSS swim test + athlete data (never retype it again)."""
    row = SwimTest(
        user_id=user.id,
        date=data.test_date or date.today(),
        tiempo_400_seg=data.tiempo_400_seg,
        tiempo_200_seg=data.tiempo_200_seg,
        tiempo_50_seg=data.tiempo_50_seg,
        css_pace_100_seg=data.css_pace_100_seg,
        edad=data.edad,
        peso_kg=data.peso_kg,
        altura_cm=data.altura_cm,
        tier=data.tier,
        modelo_version=data.modelo_version,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return SwimTestResponse.model_validate(row)


@router.get("/latest", response_model=SwimTestResponse)
def latest_test(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Latest saved CSS test (for prefill + dashboard)."""
    row = db.query(SwimTest).filter(SwimTest.user_id == user.id).order_by(
        desc(SwimTest.date), desc(SwimTest.id)).first()
    if not row:
        raise HTTPException(status_code=404, detail="No swim test saved")
    return SwimTestResponse.model_validate(row)
