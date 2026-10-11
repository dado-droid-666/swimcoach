from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

init_db()
client = TestClient(app)

# Create test user
r = client.post('/api/auth/register', json={
    'email': 'final_test@example.com',
    'password': 'password123',
    'full_name': 'Final Test'
})
print('Register:', r.status_code)

r = client.post('/api/auth/login', json={
    'email': 'final_test@example.com',
    'password': 'password123'
})
print('Login:', r.status_code)

# Get cookie
cookie = r.cookies.get('access_token')
headers = {'Cookie': f'access_token={cookie}'}

# Test all endpoints
tests = [
    ('GET', '/api/auth/me', None, 'Auth me'),
    ('GET', '/api/profile', None, 'Get profile'),
    ('PUT', '/api/profile', {'level': 'advanced', 'swim_days_per_week': 5}, 'Update profile'),
    ('GET', '/api/profile', None, 'Get profile after update'),
    ('POST', '/api/competition', {'competition_date': '2026-12-01', 'competition_type': 'pool', 'pool_events': ['400_free', '1500_free'], 'strength_days_per_week': 2}, 'Create competition'),
    ('GET', '/api/competition', None, 'Get competition'),
    ('POST', '/api/competition/generate', None, 'Generate macrocycle'),
    ('GET', '/api/plan/macrocycle', None, 'Get macrocycle'),
    ('GET', '/api/plan/today', None, 'Get today plan'),
    ('POST', '/api/feedback', {'date': '2026-09-15', 'swim_feeling': 4, 'swim_completed': True, 'strength_feeling': 3, 'strength_completed': True, 'comments': 'Great session'}, 'Submit feedback'),
    ('GET', '/api/feedback/history', None, 'Get feedback history'),
    ('GET', '/api/stats/summary', None, 'Get stats summary'),
    ('POST', '/api/subscription/checkout', None, 'Subscription checkout'),
    ('GET', '/api/subscription/status', None, 'Subscription status'),
    ('GET', '/api/subscription/portal', None, 'Billing portal'),
    ('POST', '/api/subscription/cancel', None, 'Cancel subscription (should fail - not pro)'),
]

for method, url, data, name in tests:
    if method == 'GET':
        r = client.get(url, headers=headers)
    elif method == 'POST':
        r = client.post(url, json=data, headers=headers)
    elif method == 'PUT':
        r = client.put(url, json=data, headers=headers)
    
    status = 'PASS' if r.status_code < 400 else 'FAIL'
    print(f'{status} {name}: {r.status_code}')

print('\n=== ALL TESTS COMPLETE ===')