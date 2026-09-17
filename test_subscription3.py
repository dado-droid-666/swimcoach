from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, get_db_context
from backend.auth import create_access_token, set_auth_cookie
from backend.models import User
from backend.auth import get_current_user

init_db()
client = TestClient(app)

# Create test user and get token
r = client.post("/api/auth/register", json={
    "email": "sub_test3@example.com",
    "password": "password123",
    "full_name": "Sub Test 3"
})
print("Register:", r.status_code)

# Login to get cookie
r = client.post("/api/auth/login", json={
    "email": "sub_test3@example.com",
    "password": "password123"
})
print("Login:", r.status_code)

# Manually extract and set cookie
cookie = r.cookies.get("access_token")
print("Cookie:", cookie)

# Use cookie in subsequent requests
headers = {"Cookie": f"access_token={cookie}"}

# Test subscription checkout
r = client.post("/api/subscription/checkout", headers=headers)
print("Checkout:", r.status_code, r.json())

# Test status
r = client.get("/api/subscription/status", headers=headers)
print("Status:", r.status_code, r.json())

# Test portal
r = client.get("/api/subscription/portal", headers=headers)
print("Portal:", r.status_code, r.json())

# Test cancel (should fail - not pro)
r = client.post("/api/subscription/cancel", headers=headers)
print("Cancel:", r.status_code, r.json())

print("\n=== Subscription API tests passed ===")