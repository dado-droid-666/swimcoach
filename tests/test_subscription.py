"""MercadoPago Pro subscription: no-plan pending flow, signed webhooks,
real cancellation and lazy downgrade.

Isolated sqlite; no network (MP API calls are stubbed).

Run from repo root:
    .\\venv\\Scripts\\python.exe tests/test_subscription.py
"""
import hashlib
import hmac
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_subscription_test.db"
)
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

from backend.auth import create_access_token, get_password_hash  # noqa: E402
from backend.database import Base, get_db  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models import SubscriptionStatus, SubscriptionTier, User  # noqa: E402
import backend.routes.subscription as subroutes  # noqa: E402
import backend.services.mercadopago_service as mp  # noqa: E402

engine = create_engine(f"sqlite:///{TEST_DB}", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app, raise_server_exceptions=False)

PASS, FAIL = [], []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" ({extra})" if extra else ""))


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def mkuser(
    email,
    tier=SubscriptionTier.FREE,
    status=SubscriptionStatus.PENDING,
    period_end=None,
    preapproval_id=None,
):
    db = TestingSession()
    user = User(
        email=email,
        hashed_password=get_password_hash("password123"),
        full_name="T",
        subscription_tier=tier,
        subscription_status=status,
        current_period_end=period_end,
        mp_preapproval_id=preapproval_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    uid = user.id
    db.close()
    token = create_access_token({"sub": str(uid)})
    return uid, {"Cookie": f"access_token={token}"}


def get_user(uid):
    db = TestingSession()
    user = db.query(User).filter(User.id == uid).first()
    db.expunge(user)
    db.close()
    return user


def process(payload):
    db = TestingSession()
    try:
        return mp.process_webhook(payload, db)
    finally:
        db.close()


def sign(secret, data_id, request_id="req-1", ts="1704908010", include_request_id=True):
    if include_request_id:
        manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    else:
        manifest = f"id:{data_id};ts:{ts};"
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return f"ts={ts},v1={digest}"


# ---------------------------------------------------------------------------
# Signature
# ---------------------------------------------------------------------------
SECRET = "whsec_test_123"
mp.settings.mp_webhook_secret = SECRET

good = sign(SECRET, "pre-1")
check("signature: valid manifest", mp.verify_webhook_signature(good, "req-1", "pre-1"))
check(
    "signature: uppercase data.id accepted",
    mp.verify_webhook_signature(good, "req-1", "PRE-1"),
)
check(
    "signature: altered data.id rejected",
    not mp.verify_webhook_signature(good, "req-1", "pre-2"),
)
check(
    "signature: altered request-id rejected",
    not mp.verify_webhook_signature(good, "req-2", "pre-1"),
)
check(
    "signature: missing header rejected",
    not mp.verify_webhook_signature(None, "req-1", "pre-1"),
)
check(
    "signature: missing request-id is dropped from manifest",
    mp.verify_webhook_signature(
        sign(SECRET, "pre-1", include_request_id=False), None, "pre-1"
    ),
)

mp.settings.mp_webhook_secret = ""
check(
    "signature: no secret accepts (resource is re-fetched)",
    mp.verify_webhook_signature(None, None, None),
)
mp.settings.mp_webhook_secret = SECRET

# ---------------------------------------------------------------------------
# create_preapproval payload (no plan, no free trial)
# ---------------------------------------------------------------------------
uid, headers = mkuser("payload@test.com")
captured = {}


class FakeResponse:
    status_code = 201
    text = ""

    def json(self):
        return {"id": "pre-payload", "init_point": "https://mp.test/checkout"}


def fake_request(method, url, **kwargs):
    captured["method"] = method
    captured["url"] = url
    captured.update(kwargs)
    return FakeResponse()


orig_request = mp.requests.request
orig_back_url = mp.settings.mp_back_url
orig_frontend_url = mp.settings.frontend_url
mp.settings.mp_back_url = "https://swimcoach.test/return#fragment"
mp.requests.request = fake_request
try:
    created = mp.create_preapproval(
        get_user(uid), "https://swimcoach.test/api/subscription/webhook"
    )
finally:
    mp.requests.request = orig_request

body = captured.get("json", {})
check("create: preapproval returned", created and created["id"] == "pre-payload")
check("create: no preapproval_plan_id", "preapproval_plan_id" not in body)
check("create: status pending", body.get("status") == "pending")
check("create: amount/currency", body.get("auto_recurring", {}).get("transaction_amount") == 100.0 and body.get("auto_recurring", {}).get("currency_id") == "MXN")
check("create: no free_trial", "free_trial" not in body.get("auto_recurring", {}))
check("create: no repetitions", "repetitions" not in body.get("auto_recurring", {}))
check(
    "create: back_url normalized HTTPS without fragment",
    body.get("back_url") == "https://swimcoach.test/return/",
)
check("create: back_url has no fragment", "#" not in body.get("back_url", ""))
check(
    "create: notification_url sent",
    body.get("notification_url") == "https://swimcoach.test/api/subscription/webhook",
)
check("create: external_reference", body.get("external_reference") == f"user_{uid}")

# An HTTP webhook URL must never be sent to MercadoPago (unreachable/invalid).
captured.clear()
mp.requests.request = fake_request
try:
    mp.create_preapproval(
        get_user(uid), "http://localhost:8000/api/subscription/webhook"
    )
finally:
    mp.requests.request = orig_request
http_body = captured.get("json", {})
check(
    "create: non-HTTPS notification_url omitted",
    "notification_url" not in http_body,
)

# Without a public HTTPS URL there is no usable checkout: fail before MP.
mp.settings.mp_back_url = ""
mp.settings.frontend_url = "http://localhost:8000"
rejected = mp.create_preapproval(get_user(uid))
check("create: non-HTTPS back_url rejected", rejected is None)
mp.settings.mp_back_url = orig_back_url
mp.settings.frontend_url = orig_frontend_url

# ---------------------------------------------------------------------------
# cancel_preapproval uses PUT status=cancelled (two Ls)
# ---------------------------------------------------------------------------
cancel_capture = {}


def fake_put(method, url, **kwargs):
    cancel_capture["method"] = method
    cancel_capture["url"] = url
    cancel_capture.update(kwargs)
    return FakeResponse()


orig_request = mp.requests.request
mp.requests.request = fake_put
try:
    cancelled = mp.cancel_preapproval("pre-cancel")
finally:
    mp.requests.request = orig_request

check("cancel: returns true", cancelled is True)
check("cancel: PUT /preapproval/{id}", cancel_capture.get("method") == "PUT" and cancel_capture.get("url", "").endswith("/preapproval/pre-cancel"))
check("cancel: status cancelled (two Ls)", cancel_capture.get("json") == {"status": "cancelled"})


class Fake400:
    status_code = 400
    text = '{"message":"Invalid preapproval status param: canceled","status":400}'


orig_get_pre = mp.get_preapproval
orig_request = mp.requests.request
mp.requests.request = lambda method, url, **kwargs: Fake400()
mp.get_preapproval = lambda pid: {"id": pid, "status": "authorized"}
try:
    rejected = mp.cancel_preapproval("pre-cancel-400")
finally:
    mp.requests.request = orig_request
    mp.get_preapproval = orig_get_pre
check("cancel: 400 invalid status is not success", rejected is False)

# Idempotent: a 400 is success only when the resource is already cancelled.
mp.requests.request = lambda method, url, **kwargs: Fake400()
mp.get_preapproval = lambda pid: {"id": pid, "status": "cancelled"}
try:
    already = mp.cancel_preapproval("pre-cancel-already")
finally:
    mp.requests.request = orig_request
    mp.get_preapproval = orig_get_pre
check("cancel: already cancelled is idempotent", already is True)

# ---------------------------------------------------------------------------
# Webhook: subscription_preapproval authorized
# ---------------------------------------------------------------------------
uid, headers = mkuser("authorized@test.com")
next_payment = utcnow() + timedelta(days=30)
orig_get_pre = mp.get_preapproval
mp.get_preapproval = lambda pid: {
    "id": pid,
    "external_reference": f"user_{uid}",
    "status": "authorized",
    "next_payment_date": next_payment.isoformat(),
}
try:
    ok = process({"type": "subscription_preapproval", "action": "updated", "data": {"id": "pre-auth"}})
finally:
    mp.get_preapproval = orig_get_pre

user = get_user(uid)
check("webhook authorized: processed", ok is True)
check("webhook authorized: tier pro", user.subscription_tier == SubscriptionTier.PRO)
check("webhook authorized: status active", user.subscription_status == SubscriptionStatus.ACTIVE)
check("webhook authorized: period end", user.current_period_end is not None and abs((user.current_period_end - next_payment).total_seconds()) < 2)
check("webhook authorized: ids stored", user.mp_preapproval_id == "pre-auth" and user.mp_subscription_id == "pre-auth")

# ---------------------------------------------------------------------------
# Webhook: subscription_preapproval pending (new subscription)
# ---------------------------------------------------------------------------
uid, headers = mkuser("pending@test.com")
orig_get_pre = mp.get_preapproval
mp.get_preapproval = lambda pid: {
    "id": pid,
    "external_reference": f"user_{uid}",
    "status": "pending",
    "next_payment_date": (utcnow() + timedelta(days=1)).isoformat(),
}
try:
    ok = process({"type": "subscription_preapproval", "data": {"id": "pre-pending"}})
finally:
    mp.get_preapproval = orig_get_pre

user = get_user(uid)
check("webhook pending: processed", ok is True)
check("webhook pending: stays free", user.subscription_tier == SubscriptionTier.FREE)
check("webhook pending: status pending", user.subscription_status == SubscriptionStatus.PENDING)
check("webhook pending: id stored", user.mp_preapproval_id == "pre-pending")

# ---------------------------------------------------------------------------
# Webhook: canceled keeps Pro until period end
# ---------------------------------------------------------------------------
period_end = utcnow() + timedelta(days=12)
uid, headers = mkuser(
    "cancelled@test.com",
    tier=SubscriptionTier.PRO,
    status=SubscriptionStatus.ACTIVE,
    period_end=period_end,
    preapproval_id="pre-cancelled",
)
orig_get_pre = mp.get_preapproval
mp.get_preapproval = lambda pid: {
    "id": pid,
    "external_reference": f"user_{uid}",
    "status": "cancelled",
    "next_payment_date": period_end.isoformat(),
}
try:
    ok = process({"type": "subscription_preapproval", "data": {"id": "pre-cancelled"}})
finally:
    mp.get_preapproval = orig_get_pre

user = get_user(uid)
check("webhook cancelled: processed", ok is True)
check("webhook cancelled: keeps pro", user.subscription_tier == SubscriptionTier.PRO)
check("webhook cancelled: status cancelled", user.subscription_status == SubscriptionStatus.CANCELLED)
check("webhook cancelled: keeps period end", user.current_period_end is not None and abs((user.current_period_end - period_end).total_seconds()) < 2)

# Older resources/webhook payloads may still use the one-L spelling.
uid_one_l, headers_one_l = mkuser(
    "cancelled-one-l@test.com",
    tier=SubscriptionTier.PRO,
    status=SubscriptionStatus.ACTIVE,
    period_end=period_end,
    preapproval_id="pre-cancelled-one-l",
)
mp.get_preapproval = lambda pid: {
    "id": pid,
    "external_reference": f"user_{uid_one_l}",
    "status": "canceled",
    "next_payment_date": period_end.isoformat(),
}
try:
    ok_one_l = process(
        {"type": "subscription_preapproval", "data": {"id": "pre-cancelled-one-l"}}
    )
finally:
    mp.get_preapproval = orig_get_pre

user_one_l = get_user(uid_one_l)
check("webhook cancelled (one L): processed", ok_one_l is True)
check("webhook cancelled (one L): status cancelled", user_one_l.subscription_status == SubscriptionStatus.CANCELLED)

# ---------------------------------------------------------------------------
# Webhook: subscription_authorized_payment approved extends the period
# ---------------------------------------------------------------------------
uid, headers = mkuser(
    "renew@test.com",
    tier=SubscriptionTier.PRO,
    status=SubscriptionStatus.ACTIVE,
    period_end=utcnow() + timedelta(days=1),
    preapproval_id="pre-renew",
)
renewed_end = utcnow() + timedelta(days=31)
orig_get_pay = mp.get_authorized_payment
orig_get_pre = mp.get_preapproval
mp.get_authorized_payment = lambda pid: {
    "id": pid,
    "preapproval_id": "pre-renew",
    "debit_date": utcnow().isoformat(),
    "payment": {"id": 123, "status": "approved"},
}
mp.get_preapproval = lambda pid: {
    "id": pid,
    "external_reference": f"user_{uid}",
    "status": "authorized",
    "next_payment_date": renewed_end.isoformat(),
}
try:
    ok = process({"type": "subscription_authorized_payment", "data": {"id": "inv-1"}})
finally:
    mp.get_authorized_payment = orig_get_pay
    mp.get_preapproval = orig_get_pre

user = get_user(uid)
check("webhook invoice: processed", ok is True)
check("webhook invoice: active", user.subscription_status == SubscriptionStatus.ACTIVE)
check("webhook invoice: period extended", user.current_period_end is not None and abs((user.current_period_end - renewed_end).total_seconds()) < 2)

# ---------------------------------------------------------------------------
# Webhook: rejected invoice does not grant/extend
# ---------------------------------------------------------------------------
uid, headers = mkuser(
    "rejected@test.com",
    tier=SubscriptionTier.FREE,
    status=SubscriptionStatus.PENDING,
    preapproval_id="pre-rejected",
)
orig_get_pay = mp.get_authorized_payment
mp.get_authorized_payment = lambda pid: {
    "id": pid,
    "preapproval_id": "pre-rejected",
    "payment": {"id": 124, "status": "rejected"},
}
try:
    ok = process({"type": "subscription_authorized_payment", "data": {"id": "inv-2"}})
finally:
    mp.get_authorized_payment = orig_get_pay

user = get_user(uid)
check("webhook invoice rejected: acknowledged", ok is True)
check("webhook invoice rejected: stays free", user.subscription_tier == SubscriptionTier.FREE)
check("webhook invoice rejected: no period", user.current_period_end is None)

# ---------------------------------------------------------------------------
# Checkout route persists preapproval_id + sends notification_url
# ---------------------------------------------------------------------------
uid, headers = mkuser("checkout@test.com")
seen = {}


def fake_checkout(user, notification_url=None):
    seen["user_id"] = user.id
    seen["notification_url"] = notification_url
    return {"init_point": "https://mp.test/checkout", "preapproval_id": "pre-checkout"}


orig_create_checkout = subroutes.create_mp_checkout
orig_frontend = subroutes.settings.frontend_url
orig_backend = subroutes.settings.backend_url

# Public HTTPS frontend -> webhook registered.
subroutes.settings.frontend_url = "https://swimcoach.test"
subroutes.settings.backend_url = ""
subroutes.create_mp_checkout = fake_checkout
try:
    r = client.post("/api/subscription/checkout", headers=headers)
finally:
    subroutes.create_mp_checkout = orig_create_checkout

user = get_user(uid)
check("checkout route: 200", r.status_code == 200, r.text[:120])
check("checkout route: init_point", r.json().get("init_point") == "https://mp.test/checkout")
check(
    "checkout route: notification_url",
    seen.get("notification_url") == "https://swimcoach.test/api/subscription/webhook",
)
check("checkout route: preapproval persisted", user.mp_preapproval_id == "pre-checkout")
check("checkout route: status pending", user.subscription_status == SubscriptionStatus.PENDING)

# Local HTTP frontend -> do not register an unreachable webhook.
uid_http, headers_http = mkuser("checkout-http@test.com")
seen.clear()
subroutes.settings.frontend_url = "http://localhost:8000"
subroutes.settings.backend_url = ""
subroutes.create_mp_checkout = fake_checkout
try:
    r_http = client.post("/api/subscription/checkout", headers=headers_http)
finally:
    subroutes.create_mp_checkout = orig_create_checkout
check(
    "checkout route: HTTP notification_url omitted",
    r_http.status_code == 200 and seen.get("notification_url") is None,
    r_http.text[:120],
)

# A public backend URL takes precedence over the frontend URL.
uid_backend, headers_backend = mkuser("checkout-backend@test.com")
seen.clear()
subroutes.settings.frontend_url = "http://localhost:8000"
subroutes.settings.backend_url = "https://api.swimcoach.test"
subroutes.create_mp_checkout = fake_checkout
try:
    r_backend = client.post("/api/subscription/checkout", headers=headers_backend)
finally:
    subroutes.create_mp_checkout = orig_create_checkout
    subroutes.settings.frontend_url = orig_frontend
    subroutes.settings.backend_url = orig_backend
check(
    "checkout route: backend_url precedence",
    r_backend.status_code == 200
    and seen.get("notification_url")
    == "https://api.swimcoach.test/api/subscription/webhook",
    r_backend.text[:120],
)

uid, headers = mkuser(
    "already@test.com",
    tier=SubscriptionTier.PRO,
    status=SubscriptionStatus.ACTIVE,
    period_end=utcnow() + timedelta(days=10),
    preapproval_id="pre-already",
)
r = client.post("/api/subscription/checkout", headers=headers)
check("checkout route: active pro rejected", r.status_code == 400)

# Mock checkout must never persist a fake MercadoPago id.
uid, headers = mkuser("mock@test.com")
orig_create_checkout = subroutes.create_mp_checkout
subroutes.create_mp_checkout = lambda user, notification_url=None: {
    "init_point": "https://mp.test/mock",
    "preapproval_id": "preapproval_dev_99",
    "mock": True,
}
try:
    r = client.post("/api/subscription/checkout", headers=headers)
finally:
    subroutes.create_mp_checkout = orig_create_checkout

user = get_user(uid)
check("checkout route: mock 200", r.status_code == 200, r.text[:120])
check("checkout route: mock id not persisted", user.mp_preapproval_id is None)
check("checkout route: mock status pending", user.subscription_status == SubscriptionStatus.PENDING)

# ---------------------------------------------------------------------------
# Cancel route
# ---------------------------------------------------------------------------
uid, headers = mkuser(
    "cancel-route@test.com",
    tier=SubscriptionTier.PRO,
    status=SubscriptionStatus.ACTIVE,
    period_end=utcnow() + timedelta(days=10),
    preapproval_id="pre-cancel-route",
)
called = {}
orig_cancel = subroutes.cancel_preapproval
subroutes.cancel_preapproval = lambda pid: called.setdefault("id", pid) or True
try:
    r = client.post("/api/subscription/cancel", headers=headers)
finally:
    subroutes.cancel_preapproval = orig_cancel

user = get_user(uid)
check("cancel route: 200", r.status_code == 200, r.text[:120])
check("cancel route: MP id used", called.get("id") == "pre-cancel-route")
check("cancel route: status cancelled", user.subscription_status == SubscriptionStatus.CANCELLED)
check("cancel route: keeps pro", user.subscription_tier == SubscriptionTier.PRO)

uid, headers = mkuser(
    "cancel-fail@test.com",
    tier=SubscriptionTier.PRO,
    status=SubscriptionStatus.ACTIVE,
    period_end=utcnow() + timedelta(days=10),
    preapproval_id="pre-cancel-fail",
)
orig_cancel = subroutes.cancel_preapproval
subroutes.cancel_preapproval = lambda pid: False
try:
    r = client.post("/api/subscription/cancel", headers=headers)
finally:
    subroutes.cancel_preapproval = orig_cancel

user = get_user(uid)
check("cancel route: MP failure 502", r.status_code == 502)
check("cancel route: failure keeps active", user.subscription_status == SubscriptionStatus.ACTIVE)

# ---------------------------------------------------------------------------
# Portal route (Mexico)
# ---------------------------------------------------------------------------
uid, headers = mkuser(
    "portal@test.com",
    tier=SubscriptionTier.PRO,
    status=SubscriptionStatus.ACTIVE,
    period_end=utcnow() + timedelta(days=10),
    preapproval_id="pre-portal",
)
r = client.get("/api/subscription/portal", headers=headers)
check("portal route: 200", r.status_code == 200, r.text[:120])
check("portal route: Mexico URL", "mercadopago.com.mx" in r.json().get("portal_url", ""))

# ---------------------------------------------------------------------------
# Webhook route: signature enforcement
# ---------------------------------------------------------------------------
mp.settings.mp_webhook_secret = SECRET
route_calls = []
orig_process = subroutes.process_webhook
subroutes.process_webhook = lambda payload, db: route_calls.append(payload) or True

payload = {"type": "subscription_preapproval", "data": {"id": "pre-route"}}
r = client.post("/api/subscription/webhook", json=payload)
check("webhook route: missing signature 401", r.status_code == 401)

r = client.post(
    "/api/subscription/webhook",
    json=payload,
    headers={"x-signature": sign(SECRET, "pre-route"), "x-request-id": "req-1"},
)
check("webhook route: valid signature 200", r.status_code == 200, r.text[:120])
check("webhook route: processed once", len(route_calls) == 1)

r = client.post(
    "/api/subscription/webhook",
    json={"type": "subscription_preapproval", "data": {"id": "pre-other"}},
    headers={"x-signature": sign(SECRET, "pre-route"), "x-request-id": "req-1"},
)
check("webhook route: body-id mismatch 401", r.status_code == 401)

route_calls.clear()
r = client.post(
    "/api/subscription/webhook?data.id=pre-query&type=subscription_preapproval",
    json={},
    headers={"x-signature": sign(SECRET, "pre-query"), "x-request-id": "req-1"},
)
check("webhook route: query-only 200", r.status_code == 200, r.text[:120])
check(
    "webhook route: query-only rebuilt",
    route_calls and route_calls[0].get("data", {}).get("id") == "pre-query"
    and route_calls[0].get("type") == "subscription_preapproval",
)

route_calls.clear()
r = client.post(
    "/api/subscription/webhook?data.id=pre-query",
    json={"type": "subscription_preapproval", "data": {"id": "pre-body"}},
    headers={"x-signature": sign(SECRET, "pre-query"), "x-request-id": "req-1"},
)
check("webhook route: query precedence 200", r.status_code == 200, r.text[:120])
check(
    "webhook route: processes signed query id",
    route_calls and route_calls[0].get("data", {}).get("id") == "pre-query",
)

subroutes.process_webhook = orig_process

# ---------------------------------------------------------------------------
# /webhook/test disabled in production
# ---------------------------------------------------------------------------
orig_env = subroutes.settings.environment
subroutes.settings.environment = "production"
try:
    r = client.post("/api/subscription/webhook/test", json={"type": "payment"})
finally:
    subroutes.settings.environment = orig_env
check("webhook test: 404 in production", r.status_code == 404)

# ---------------------------------------------------------------------------
# Lazy downgrade after cancellation expires
# ---------------------------------------------------------------------------
uid, headers = mkuser(
    "expired@test.com",
    tier=SubscriptionTier.PRO,
    status=SubscriptionStatus.CANCELLED,
    period_end=utcnow() - timedelta(days=1),
    preapproval_id="pre-expired",
)
r = client.get("/api/auth/me", headers=headers)
user = get_user(uid)
check("lazy downgrade: /me 200", r.status_code == 200, r.text[:120])
check("lazy downgrade: tier free", user.subscription_tier == SubscriptionTier.FREE)
check("lazy downgrade: response free", r.json().get("subscription_tier") == "free")

uid, headers = mkuser(
    "paused-expired@test.com",
    tier=SubscriptionTier.PRO,
    status=SubscriptionStatus.PAUSED,
    period_end=utcnow() - timedelta(days=1),
    preapproval_id="pre-paused",
)
r = client.get("/api/auth/me", headers=headers)
user = get_user(uid)
check("lazy downgrade paused: /me 200", r.status_code == 200, r.text[:120])
check("lazy downgrade paused: tier free", user.subscription_tier == SubscriptionTier.FREE)

# ---------------------------------------------------------------------------
mp.settings.mp_webhook_secret = ""
print(f"\n=== subscription: {len(PASS)} passed, {len(FAIL)} failed ===")
engine.dispose()
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
sys.exit(1 if FAIL else 0)
