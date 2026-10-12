"""Web Push subscriptions (Phase 1: storage + manual test sends).

- GET  /api/notifications/vapid-key  (public; empty key = not configured)
- POST /api/notifications/subscribe  (auth; upsert by endpoint)
- DELETE /api/notifications/subscribe (auth; body {endpoint})
- POST /api/notifications/test       (admin; sends a test push to OWN subs)

Phase 2 adds the daily scheduler (reminder_time/reminder_tz already modeled).
"""
import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

log = logging.getLogger("swimcoach.push")

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


def send_push(subscription: PushSubscription, title: str, body: str, url: str = "/#/session/today") -> tuple[bool, str]:
    """Send one Web Push message. Returns (ok, reason) where reason is a
    short, secret-free diagnostic (e.g. 'unauthorized', 'gone', 'no-lib').
    Callers count; 404/410 subscriptions should be pruned by Phase 2."""
    try:
        from pywebpush import webpush
    except ImportError:
        return False, "no-lib: pywebpush not installed"
    if not _vapid_configured():
        return False, "no-vapid: keys missing"
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
        return True, "sent"
    except Exception as exc:  # noqa: BLE001 — diagnostic path, never secrets
        reason = _push_error_reason(exc)
        log.warning("push failed sub=%s reason=%s", subscription.id, reason)
        return False, reason


def _keypair_info() -> dict:
    """Non-secret metadata: do the configured keys form a valid pair?
    Returns {configured, keypair_match, endpoint_host} — never key material."""
    if not _vapid_configured():
        return {"configured": False}
    try:
        from cryptography.hazmat.primitives.asymmetric import ec

        def b64url(data: bytes) -> str:
            import base64
            return base64.urlsafe_b64encode(data).decode().rstrip("=")

        def unb64url(data: str) -> bytes:
            import base64
            return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))

        priv = int.from_bytes(unb64url(settings.vapid_private_key.strip()), "big")
        derived = ec.derive_private_key(priv, ec.SECP256R1())
        nums = derived.public_key().public_numbers()
        derived_pub = b64url(b"\x04" + nums.x.to_bytes(32, "big") + nums.y.to_bytes(32, "big"))
        return {"configured": True, "keypair_match": derived_pub == settings.vapid_public_key.strip()}
    except Exception:
        return {"configured": True, "keypair_match": False, "keys_parseable": False}


def _push_error_reason(exc: Exception) -> str:
    resp = getattr(exc, "response", None)
    status_code = getattr(resp, "status_code", None)
    # pywebpush puts status + reason + FCM body into exc.message
    # ("Push failed: 400 ... Response body:...") — secret-free, most exact.
    msg = ""
    try:
        raw = getattr(exc, "message", "") or str(exc)
        msg = re.sub(r"\s+", " ", raw).strip()[:200]
    except Exception:
        msg = ""
    if not msg:
        try:
            if resp is not None and hasattr(resp, "text"):
                msg = re.sub(r"\s+", " ", resp.text or "").strip()[:200]
        except Exception:
            msg = ""
    suffix = f" :: {msg}" if msg else ""
    if status_code == 404 or status_code == 410:
        return f"gone: endpoint expired ({status_code}){suffix}"
    if status_code == 401 or status_code == 403:
        return f"unauthorized: bad VAPID signature ({status_code}){suffix}"
    if status_code:
        return f"push-service-{status_code}: {type(exc).__name__}{suffix}"
    return f"transport: {type(exc).__name__}{suffix}"


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
    details: list[str] = []
    hosts: list[str] = []
    for sub in subs:
        try:
            from urllib.parse import urlparse
            hosts.append(urlparse(sub.endpoint).hostname or "?")
        except Exception:
            hosts.append("?")
        ok, reason = send_push(sub, "SwimCoach test 🏊", "Push notifications are working.")
        if ok:
            sent += 1
        else:
            failed += 1
            details.append(f"sub {sub.id}: {reason}")
    return TestPushResponse(sent=sent, failed=failed, details=details,
                            keypair=_keypair_info(), endpoint_hosts=sorted(set(hosts)))
