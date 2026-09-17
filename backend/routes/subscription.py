from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.models import User, SubscriptionTier, SubscriptionStatus
from backend.schemas import CheckoutResponse, PortalResponse, TierCheckResponse
from backend.auth import get_current_user, require_pro
from backend.services.mercadopago_service import (
    create_checkout_preference, process_webhook, get_billing_portal_url,
    verify_webhook_signature, cancel_preapproval, get_or_create_preapproval_plan
)

router = APIRouter(prefix="/api/subscription", tags=["subscription"])


class CheckoutRequest(BaseModel):
    pass


class CancelRequest(BaseModel):
    pass


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create MercadoPago checkout for Pro subscription."""
    if user.subscription_tier == SubscriptionTier.PRO:
        raise HTTPException(status_code=400, detail="Already on Pro plan")
    
    # Get preapproval plan ID from settings
    plan_id = get_or_create_preapproval_plan()
    
    checkout = create_checkout_preference(user, plan_id)
    if not checkout:
        raise HTTPException(status_code=500, detail="Failed to create checkout")
    
    return CheckoutResponse(
        init_point=checkout.get("init_point") or checkout.get("sandbox_init_point"),
        preapproval_id=checkout.get("preapproval_id")
    )


@router.get("/portal", response_model=PortalResponse)
def get_portal(
    user: User = Depends(get_current_user)
):
    """Get MercadoPago billing portal URL."""
    portal_url = get_billing_portal_url(user)
    if not portal_url:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    return PortalResponse(portal_url=portal_url)


@router.post("/cancel")
def cancel_subscription(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel Pro subscription."""
    if user.subscription_tier != SubscriptionTier.PRO:
        raise HTTPException(status_code=400, detail="No active Pro subscription")
    
    if not user.mp_preapproval_id:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    success = cancel_preapproval(user.mp_preapproval_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")
    
    # Update user status (will be finalized by webhook)
    user.subscription_status = SubscriptionStatus.CANCELLED
    db.commit()
    
    return {"message": "Subscription cancelled. Pro features remain until period ends."}


@router.get("/status", response_model=TierCheckResponse)
def get_tier_status(
    user: User = Depends(get_current_user)
):
    """Get current tier and available features."""
    is_pro = user.subscription_tier == SubscriptionTier.PRO
    
    features = {
        "unlimited_history": is_pro,
        "readiness_score": is_pro,
        "advanced_charts": is_pro,
        "regenerate_week": is_pro,
        "export_csv": is_pro,
        "no_ads": is_pro,
        "multiple_goals": is_pro,
        "priority_support": is_pro
    }
    
    return TierCheckResponse(
        tier=user.subscription_tier,
        features=features
    )


@router.post("/webhook")
async def mercadopago_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None),
    x_request_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """MercadoPago webhook endpoint."""
    body = await request.body()
    
    # Verify signature
    if not verify_webhook_signature(body, x_signature or ""):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        import json
        webhook_data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Process webhook
    success = process_webhook(webhook_data, db)
    
    if not success:
        raise HTTPException(status_code=500, detail="Webhook processing failed")
    
    return {"status": "ok"}


@router.post("/webhook/test")
async def test_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Test webhook endpoint (for development)."""
    try:
        import json
        webhook_data = await request.json()
        process_webhook(webhook_data, db)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))