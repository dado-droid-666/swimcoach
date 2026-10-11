"""Web Push subscriptions (Phase 1: storage + manual test sends).

- GET  /api/notifications/vapid-key  (public; empty key = not configured)
- POST /api/notifications/subscribe  (auth; upsert by endpoint)
- DELETE /api/notifications/subscribe (auth; body {endpoint})
- POST /api/notifications/test       (admin; sends a test push to OWN subs)

Phase 2 adds the daily scheduler (reminder_time/reminder_tz already modeled).
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth import get_current_user, require_admin
from backend.config import get_settings
from backend.database import get_db
from backend.models import PushSubscription, User
from backend.schemas import (
    PushSubscriptionCreate,
    PushUnsubscribe,
    TestPushResponse,
    VapidKeyResponse,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
settings = get_settings()


def _vapid_configured() -> bool:
    return bool(settings.vapid_public_key and settings.vapid_private_key)


def send_push(subscription: PushSubscription, title: str, body: str, url: str = "/#/session/today") -> bool:
    """Send one Web Push message. Returns True on 2xx; False otherwise
    (caller counts; 404/410 subscriptions should be pruned by Phase 2)."""
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        return False
    if not _vapid_configured():
        return False
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps({"title": title, "body": body, "url": url}),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_claims_email},
        )
        return True
    except Exception:
        return False


@router.get("/vapid-key", response_model=VapidKeyResponse)
def get_vapid_key():
    return VapidKeyResponse(public_key=settings.vapid_public_key or "")


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe(
    data: PushSubscriptionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upsert this browser's push endpoint (idempotent re-subscribes)."""
    if not data.keys.p256dh or not data.keys.auth:
        raise HTTPException(status_code=400, detail="Missing push keys")
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == data.endpoint).first()
    if sub:
        if sub.user_id != user.id:
            sub.user_id = user.id
        sub.p256dh = data.keys.p256dh
        sub.auth = data.keys.auth
    else:
        sub = PushSubscription(
            user_id=user.id,
            endpoint=data.endpoint,
            p256dh=data.keys.p256dh,
            auth=data.keys.auth,
        )
        db.add(sub)
    db.commit()
    return {"message": "Subscribed"}


@router.delete("/subscribe")
def unsubscribe(
    data: PushUnsubscribe,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(PushSubscription).filter(
        PushSubscription.user_id == user.id,
        PushSubscription.endpoint == data.endpoint,
    ).delete(synchronize_session=False)
    db.commit()
    return {"message": "Unsubscribed"}


@router.post("/test", response_model=TestPushResponse)
def test_push(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Send a test push to the ADMIN's own subscriptions (manual verify)."""
    subs = db.query(PushSubscription).filter(PushSubscription.user_id == admin.id).all()
    if not subs:
        raise HTTPException(status_code=404, detail="No subscriptions for admin — enable notifications in Settings first")
    if not _vapid_configured():
        raise HTTPException(status_code=503, detail="Push not configured (VAPID keys missing)")
    sent = failed = 0
    for sub in subs:
        if send_push(sub, "SwimCoach test 🏊", "Push notifications are working."):
            sent += 1
        else:
            failed += 1
    return TestPushResponse(sent=sent, failed=failed)
