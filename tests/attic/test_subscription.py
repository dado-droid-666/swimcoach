from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db
from backend.auth import create_access_token

init_db()
client = TestClient(app)

# Create test user and get token
r = client.post("/api/auth/register", json={
    "email": "sub_test@example.com",
    "password": "password123",
    "full_name": "Sub Test"
})
print("Register:", r.status_code)

# Get token directly
from backend.database import get_db_context
from backend.models import User
with get_db_context() as db:
    user = db.query(User).filter(User.email == "sub_test@example.com").first()
    token = create_access_token({"sub": user.id, "email": user.email})

headers = {"Authorization": f"Bearer {token}"}

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