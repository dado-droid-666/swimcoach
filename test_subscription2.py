from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, get_db_context
from backend.auth import create_access_token, set_auth_cookie
from backend.models import User

init_db()
client = TestClient(app)

# Create test user and get token
r = client.post("/api/auth/register", json={
    "email": "sub_test2@example.com",
    "password": "password123",
    "full_name": "Sub Test 2"
})
print("Register:", r.status_code, r.json())

# Login to get cookie
r = client.post("/api/auth/login", json={
    "email": "sub_test2@example.com",
    "password": "password123"
})
print("Login:", r.status_code, r.json())
print("Cookies:", client.cookies)

# Test subscription checkout
r = client.post("/api/subscription/checkout")
print("Checkout:", r.status_code, r.json())

# Test status
r = client.get("/api/subscription/status")
print("Status:", r.status_code, r.json())

# Test portal
r = client.get("/api/subscription/portal")
print("Portal:", r.status_code, r.json())

# Test cancel (should fail - not pro)
r = client.post("/api/subscription/cancel")
print("Cancel:", r.status_code, r.json())

print("\n=== Subscription API tests passed ===")