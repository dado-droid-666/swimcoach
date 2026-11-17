import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.config import get_settings
from backend.database import get_db
from backend.models import SubscriptionStatus, SubscriptionTier, User
from backend.schemas import CheckoutResponse, PortalResponse, TierCheckResponse
from backend.services.mercadopago_service import (
    cancel_preapproval,
    create_checkout as create_mp_checkout,
    get_billing_portal_url,
    is_public_https_url,
    process_webhook,
    verify_webhook_signature,
)

settings = get_settings()
router = APIRouter(prefix="/api/subscription", tags=["subscription"])


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a MercadoPago recurring subscription (no plan, pending payment)."""
    if (
        user.subscription_tier == SubscriptionTier.PRO
        and user.subscription_status == SubscriptionStatus.ACTIVE
    ):
        raise HTTPException(status_code=400, detail="Already on Pro plan")

    base_url = (
        settings.backend_url or settings.frontend_url or str(request.base_url)
    ).rstrip("/")
    # MercadoPago cannot reach localhost; only register the webhook when the
    # backend has a public HTTPS URL. In local development the webhook can be
    # simulated with POST /api/subscription/webhook/test.
    notification_url = (
        f"{base_url}/api/subscription/webhook"
        if is_public_https_url(base_url)
        else None
    )

    checkout = create_mp_checkout(user, notification_url)
    if not checkout or not checkout.get("init_point"):
        raise HTTPException(
            status_code=502, detail="Could not create MercadoPago checkout"
        )

    # Persist the subscription id immediately: cancel/portal need it even if
    # the webhook is delayed or lost. Mock checkouts never touch the DB.
    if checkout.get("preapproval_id") and not checkout.get("mock"):
        user.mp_preapproval_id = checkout["preapproval_id"]
        if user.subscription_tier != SubscriptionTier.PRO:
            user.subscription_status = SubscriptionStatus.PENDING
        db.commit()

    return CheckoutResponse(
        init_point=checkout["init_point"],
        preapproval_id=checkout["preapproval_id"],
    )


@router.get("/portal", response_model=PortalResponse)
def get_portal(user: User = Depends(get_current_user)):
    """Link to the payer's MercadoPago subscriptions page."""
    portal_url = get_billing_portal_url(user)
    if not portal_url:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return PortalResponse(portal_url=portal_url)


@router.post("/cancel")
def cancel_subscription(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel the recurring charge. Pro stays until `current_period_end`."""
    if user.subscription_tier != SubscriptionTier.PRO:
        raise HTTPException(status_code=400, detail="No active Pro subscription")

    if not user.mp_preapproval_id:
        raise HTTPException(status_code=404, detail="No subscription found")

    if not cancel_preapproval(user.mp_preapproval_id):
        raise HTTPException(status_code=502, detail="MercadoPago cancel failed")

    user.subscription_status = SubscriptionStatus.CANCELLED
    if not user.current_period_end:
        # Nothing paid yet: expire on the next authenticated request.
        user.current_period_end = datetime.utcnow()
    db.commit()

    return {
        "message": "Subscription cancelled. Pro features remain until period ends.",
        "current_period_end": (
            user.current_period_end.isoformat() if user.current_period_end else None
        ),
    }


@router.get("/status", response_model=TierCheckResponse)
def get_tier_status(user: User = Depends(get_current_user)):
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
        "priority_support": is_pro,
    }

    return TierCheckResponse(tier=user.subscription_tier, features=features)


@router.post("/webhook")
async def mercadopago_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None),
    x_request_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """MercadoPago webhook endpoint."""
    body = await request.body()
    try:
        payload = json.loads(body) if body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid payload")

    # `data.id` normally comes in the body, but MercadoPago also adds it as a
    # query param; the signature manifest is defined over that query value.
    # Prefer (and process) the signed value to avoid body/query mismatches.
    query_data_id = request.query_params.get("data.id")
    body_data_id = (payload.get("data") or {}).get("id")
    data_id = query_data_id if query_data_id is not None else body_data_id

    if not verify_webhook_signature(x_signature, x_request_id, data_id):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if not payload.get("data") and query_data_id:
        # Legacy IPN: query params only, no useful body.
        payload = {
            "type": request.query_params.get("type")
            or request.query_params.get("topic"),
            "data": {"id": query_data_id},
        }
    elif query_data_id is not None:
        payload.setdefault("data", {})["id"] = query_data_id

    if not process_webhook(payload, db):
        raise HTTPException(status_code=500, detail="Webhook processing failed")

    return {"status": "ok"}


@router.post("/webhook/test")
async def test_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Simulate a webhook locally. Disabled outside development."""
    if settings.environment == "production":
        raise HTTPException(status_code=404, detail="Not found")

    try:
        webhook_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not process_webhook(webhook_data, db):
        raise HTTPException(status_code=500, detail="Webhook processing failed")
    return {"status": "ok"}
