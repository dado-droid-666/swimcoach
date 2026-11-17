"""MercadoPago recurring subscriptions for the Pro plan.

Flow: **subscription without an associated plan** (pending payment).

1. `POST /preapproval` with `auto_recurring` + `status=pending` returns an
   `init_point`; the user authorises the recurring payment on MercadoPago.
2. MercadoPago calls our webhook (`subscription_preapproval` and
   `subscription_authorized_payment`). We never trust the notification body:
   the resource is re-fetched from the MercadoPago API and the user is updated
   from that response.
3. Cancelling is `PUT /preapproval/{id}` with `{"status": "cancelled"}`; Pro
   stays active until `current_period_end`.

The MercadoPago Python SDK 2.1.0 has a broken `preapproval().update()` URI and
no `cancel()`, so this module talks to the REST API directly.
"""
import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit

import requests
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.models import SubscriptionStatus, SubscriptionTier, User

settings = get_settings()
logger = logging.getLogger(__name__)

MP_API_BASE = "https://api.mercadopago.com"
PRO_AMOUNT = 100.0  # MXN / month
PRO_CURRENCY = "MXN"
REQUEST_TIMEOUT = 10  # webhook must answer MP within 22s (worst case: 2 calls)


def _utcnow() -> datetime:
    """Naive UTC, matching the DateTime columns in models."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.mp_access_token}",
        "Content-Type": "application/json",
    }


def _is_test_token() -> bool:
    return (settings.mp_access_token or "").startswith("TEST-")


def _mock_enabled() -> bool:
    """Dev-only fake checkout.

    Only for explicit opt-in or the placeholder token shipped in .env.example.
    A real TEST- token must reach the MercadoPago sandbox, not this mock.
    """
    if settings.mp_mock_checkout:
        return True
    token = (settings.mp_access_token or "").strip()
    return not token or token.startswith("TEST-x") or token == "TEST-1234567890"


def is_public_https_url(value: str) -> bool:
    """MercadoPago only accepts public HTTPS URLs for redirects/webhooks."""
    parts = urlsplit((value or "").strip())
    return parts.scheme == "https" and bool(parts.netloc)


def _back_url() -> Optional[str]:
    """Normalized `back_url` for the MercadoPago checkout.

    MercadoPago rejects `http://localhost` and any URL with a fragment. The SPA
    uses hash routing, so the fragment is dropped and recovered from the query
    params MercadoPago appends to the redirect.
    """
    raw = (settings.mp_back_url or settings.frontend_url or "").strip()
    if not is_public_https_url(raw):
        return None
    parts = urlsplit(raw)
    path = parts.path or "/"
    if not path.endswith("/"):
        path += "/"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def _request(method: str, path: str, **kwargs) -> Optional[requests.Response]:
    try:
        response = requests.request(
            method,
            f"{MP_API_BASE}{path}",
            headers=_headers(),
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )
    except requests.RequestException as exc:
        logger.error("MercadoPago %s %s failed: %s", method, path, exc)
        return None

    if response.status_code >= 400:
        logger.error(
            "MercadoPago %s %s -> %s: %s",
            method,
            path,
            response.status_code,
            response.text[:500],
        )
    return response


def create_preapproval(
    user: User, notification_url: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Create a pending subscription (no associated plan) and return MP's JSON."""
    back_url = _back_url()
    if not back_url:
        logger.error(
            "MercadoPago back_url must be a public HTTPS URL; set MP_BACK_URL "
            "(got %r)",
            settings.mp_back_url or settings.frontend_url,
        )
        return None

    payload: Dict[str, Any] = {
        "reason": "SwimCoach Pro",
        "external_reference": f"user_{user.id}",
        "payer_email": user.email,
        "back_url": back_url,
        "status": "pending",
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "transaction_amount": PRO_AMOUNT,
            "currency_id": PRO_CURRENCY,
        },
    }
    if notification_url:
        if is_public_https_url(notification_url):
            payload["notification_url"] = notification_url
        else:
            logger.warning(
                "Ignoring non-HTTPS MercadoPago notification_url: %s",
                notification_url,
            )

    response = _request("POST", "/preapproval", json=payload)
    if response is None or response.status_code not in (200, 201):
        return None
    return response.json()


def create_checkout(
    user: User, notification_url: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Return `{init_point, preapproval_id}` for the frontend redirect."""
    if _mock_enabled():
        mock_id = f"preapproval_dev_{user.id}_{int(_utcnow().timestamp())}"
        mock_url = (
            f"{settings.frontend_url.rstrip('/')}/#/upgrade"
            f"?mock_checkout=1&preapproval_id=mock_{user.id}"
        )
        logger.warning("MercadoPago checkout is MOCKED (placeholder credentials)")
        return {
            "init_point": mock_url,
            "sandbox_init_point": mock_url,
            "preapproval_id": mock_id,
            "mock": True,
        }

    preapproval = create_preapproval(user, notification_url)
    if not preapproval or not preapproval.get("id"):
        return None

    init_point = preapproval.get("init_point")
    sandbox_init_point = preapproval.get("sandbox_init_point")
    if _is_test_token() and sandbox_init_point:
        init_point = sandbox_init_point

    return {
        "init_point": init_point,
        "sandbox_init_point": sandbox_init_point,
        "preapproval_id": str(preapproval["id"]),
    }


def get_preapproval(preapproval_id: str) -> Optional[Dict[str, Any]]:
    response = _request("GET", f"/preapproval/{preapproval_id}")
    if response is None or response.status_code != 200:
        return None
    return response.json()


def get_authorized_payment(payment_id: str) -> Optional[Dict[str, Any]]:
    response = _request("GET", f"/authorized_payments/{payment_id}")
    if response is None or response.status_code != 200:
        return None
    return response.json()


def cancel_preapproval(preapproval_id: str) -> bool:
    """Cancel a subscription.

    MercadoPago's update endpoint expects `cancelled` (two Ls); sending
    `canceled` returns 400 `Invalid preapproval status param`. The resource
    then reports `cancelled` as well.
    """
    response = _request(
        "PUT", f"/preapproval/{preapproval_id}", json={"status": "cancelled"}
    )
    if response is None:
        return False
    if response.status_code in (200, 201):
        return True
    if response.status_code == 400:
        # Idempotent: already cancelled is a success for us. Do NOT trust a
        # 400 body containing the word "canceled": that is the API rejecting
        # the old one-L spelling, not a confirmation.
        preapproval = get_preapproval(preapproval_id)
        if preapproval and str(preapproval.get("status", "")).lower() in (
            "cancelled",
            "canceled",
        ):
            return True
    return False


def get_billing_portal_url(user: User) -> Optional[str]:
    """MercadoPago has no per-subscription portal; link the payer's account."""
    if not user.mp_preapproval_id:
        return None
    return settings.mp_portal_url or None


# ---------------------------------------------------------------------------
# Webhook signature
# ---------------------------------------------------------------------------

def verify_webhook_signature(
    signature: Optional[str], request_id: Optional[str], data_id: Optional[Any]
) -> bool:
    """Validate MercadoPago's `x-signature` (HMAC-SHA256 over the manifest).

    Manifest: `id:<data.id>;request-id:<x-request-id>;ts:<ts>;`
    Missing `data.id` / `x-request-id` are removed from the manifest, per docs.
    With no configured secret we accept the call, but `process_webhook` still
    re-fetches the resource from MercadoPago before changing any subscription.
    """
    secret = settings.mp_webhook_secret or ""
    if not secret:
        if settings.environment == "production":
            logger.warning(
                "MP_WEBHOOK_SECRET is empty: webhook authenticity relies on the "
                "MercadoPago API re-fetch. Configure the secret in Render."
            )
        return True

    if not signature or data_id is None or str(data_id) == "":
        return False

    ts: Optional[str] = None
    candidates = []
    for part in signature.split(","):
        key, separator, value = part.strip().partition("=")
        if not separator:
            continue
        if key == "ts":
            ts = value
        elif key == "v1":
            candidates.append(value)

    if not ts or not candidates:
        return False

    manifest_parts = [f"id:{str(data_id).lower()}"]
    if request_id:
        manifest_parts.append(f"request-id:{request_id}")
    manifest_parts.append(f"ts:{ts}")
    manifest = ";".join(manifest_parts) + ";"

    expected = hmac.new(
        secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return any(hmac.compare_digest(expected, candidate) for candidate in candidates)


# ---------------------------------------------------------------------------
# Webhook processing
# ---------------------------------------------------------------------------

def _parse_mp_datetime(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _find_user(db: Session, preapproval: Dict[str, Any]) -> Optional[User]:
    reference = str(preapproval.get("external_reference") or "")
    if reference.startswith("user_"):
        try:
            user_id = int(reference.split("_", 1)[1])
        except (IndexError, ValueError):
            user_id = None
        if user_id is not None:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return user

    preapproval_id = preapproval.get("id")
    if preapproval_id:
        return (
            db.query(User)
            .filter(User.mp_preapproval_id == str(preapproval_id))
            .first()
        )
    return None


def _apply_preapproval(db: Session, preapproval: Dict[str, Any]) -> bool:
    user = _find_user(db, preapproval)
    if not user:
        logger.warning(
            "MP preapproval %s has no matching user (external_reference=%s)",
            preapproval.get("id"),
            preapproval.get("external_reference"),
        )
        return False

    preapproval_id = str(preapproval.get("id") or "")
    if preapproval_id:
        user.mp_preapproval_id = preapproval_id
        user.mp_subscription_id = preapproval_id

    next_payment = _parse_mp_datetime(preapproval.get("next_payment_date"))
    status = str(preapproval.get("status") or "").lower()

    if status == "authorized":
        user.subscription_tier = SubscriptionTier.PRO
        user.subscription_status = SubscriptionStatus.ACTIVE
        user.current_period_end = next_payment or (_utcnow() + timedelta(days=30))
    elif status == "paused":
        user.subscription_status = SubscriptionStatus.PAUSED
        if next_payment:
            user.current_period_end = next_payment
    elif status in ("cancelled", "canceled"):
        # Keep Pro until the paid period ends; auth.py downgrades lazily.
        # MP's current API returns "cancelled" (two Ls); accept both spellings
        # for older resources and webhook payloads.
        user.subscription_status = SubscriptionStatus.CANCELLED
        if next_payment:
            user.current_period_end = next_payment
    elif status == "pending":
        if user.subscription_tier != SubscriptionTier.PRO:
            user.subscription_status = SubscriptionStatus.PENDING
        if next_payment and not user.current_period_end:
            user.current_period_end = next_payment
    else:
        logger.info("MP preapproval %s: unhandled status %r", preapproval_id, status)

    db.commit()
    return True


def _apply_authorized_payment(db: Session, payment_id: str) -> bool:
    invoice = get_authorized_payment(payment_id)
    if not invoice:
        return False

    payment = invoice.get("payment") or {}
    if payment.get("status") != "approved":
        logger.info(
            "MP invoice %s not approved (payment status=%s)",
            payment_id,
            payment.get("status"),
        )
        return True  # acknowledged, nothing to grant

    preapproval_id = invoice.get("preapproval_id")
    if not preapproval_id:
        logger.warning("MP invoice %s has no preapproval_id", payment_id)
        return False

    preapproval = get_preapproval(str(preapproval_id))
    if not preapproval:
        return False

    user = _find_user(db, preapproval)
    if not user:
        return False

    user.mp_preapproval_id = str(preapproval_id)
    user.mp_subscription_id = str(preapproval_id)

    status = str(preapproval.get("status") or "").lower()
    if status in ("authorized", "pending"):
        user.subscription_tier = SubscriptionTier.PRO
        user.subscription_status = SubscriptionStatus.ACTIVE

    next_payment = _parse_mp_datetime(preapproval.get("next_payment_date"))
    if not next_payment:
        debit_date = _parse_mp_datetime(invoice.get("debit_date"))
        base = debit_date or _utcnow()
        next_payment = base + timedelta(days=30)
    user.current_period_end = next_payment

    db.commit()
    return True


def process_webhook(webhook_data: Dict[str, Any], db: Session) -> bool:
    """Handle a MercadoPago notification. Returns False only on real failures."""
    topic = webhook_data.get("type") or webhook_data.get("topic") or ""
    data = webhook_data.get("data") or {}
    resource_id = data.get("id")

    if not topic or resource_id is None:
        logger.info("MP webhook ignored (type=%r, data.id=%r)", topic, resource_id)
        return True

    topic = str(topic)

    # Current topics + legacy aliases.
    if topic in ("subscription_preapproval", "preapproval"):
        preapproval = get_preapproval(str(resource_id))
        if not preapproval:
            return False
        return _apply_preapproval(db, preapproval)

    if topic in ("subscription_authorized_payment", "authorized_payment"):
        return _apply_authorized_payment(db, str(resource_id))

    # `payment` events are also sent for subscriptions; the preapproval and
    # authorized-payment topics are authoritative for access, so ignore these.
    logger.info("MP webhook topic %r ignored", topic)
    return True
