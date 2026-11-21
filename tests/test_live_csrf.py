import re
import pytest
from app import create_app


def test_live_browser_csrf_flow():
    app = create_app()
    client = app.test_client()

    # 1. Fetch login form and extract CSRF token
    get_res = client.get('/login')
    assert get_res.status_code == 200
    match = re.search(r'name="csrf_token".*?value="([^"]+)"', get_res.data.decode('utf-8'))
    assert match is not None, "CSRF token must be present in HTML form"
    token = match.group(1)

    # 2. Login with valid CSRF token as student
    login_res = client.post('/login', data={
        'csrf_token': token,
        'email': 'student@demo.com',
        'password': 'Student@123'
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b'Ada Lovelace' in login_res.data

    # 3. Access student dashboard
    dash_res = client.get('/dashboard')
    assert dash_res.status_code == 200
    assert b'Dashboard' in dash_res.data

    # 4. Access courses catalog
    courses_res = client.get('/courses')
    assert courses_res.status_code == 200

    # 5. Access assignments
    assign_res = client.get('/assignments')
    assert assign_res.status_code == 200

    # 6. Access progress
    prog_res = client.get('/progress')
    assert prog_res.status_code == 200

    # 7. Student access to /admin must be blocked (403 Forbidden)
    admin_res = client.get('/admin')
    assert admin_res.status_code == 403
