from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, get_db_context
from backend.auth import create_access_token, get_current_user, decode_token
from backend.models import User
from backend.routes.auth import get_current_user as get_current_user_route

init_db()

# Test 1: Verify decode_token works
token = create_access_token({"sub": 1, "email": "test@example.com"})
payload = decode_token(token)
print("Token decode:", payload)

# Test 2: Test with direct FastAPI request object
from starlette.testclient import TestClient as StarletteTestClient
from starlette.requests import Request
from starlette.datastructures import Headers

client = TestClient(app)

# Create user and login
r = client.post("/api/auth/register", json={
    "email": "cookie_test@example.com",
    "password": "password123",
    "full_name": "Cookie Test"
})
print("Register:", r.status_code)

r = client.post("/api/auth/login", json={
    "email": "cookie_test@example.com",
    "password": "password123"
})
print("Login:", r.status_code)

# Check cookie in response
cookie = r.cookies.get("access_token")
print("Cookie from response:", cookie)

# Now test with the cookie in a proper way - use client.cookies
# TestClient stores cookies in client.cookies
print("Client cookies after login:", client.cookies)

# Test with client directly (it should auto-handle cookies)
r = client.get("/api/auth/me")
print("Me with auto-cookie:", r.status_code, r.json())

r = client.get("/api/subscription/status")
print("Status with auto-cookie:", r.status_code, r.json())

r = client.post("/api/subscription/checkout")
print("Checkout with auto-cookie:", r.status_code, r.json())