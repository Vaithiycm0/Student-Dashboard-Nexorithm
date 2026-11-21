from app.models import User


def test_register_student(client):
    """Test checklist item: Register a new student"""
    response = client.post('/register', data={
        'name': 'New Student',
        'email': 'newstudent@example.com',
        'department': 'Electrical Engineering',
        'year': 2,
        'password': 'Password@123',
        'confirm_password': 'Password@123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Registration successful' in response.data

    user = User.query.filter_by(email='newstudent@example.com').first()
    assert user is not None
    assert user.role == 'student'
    assert user.check_password('Password@123')


def test_login_and_logout(client, seed_data, auth):
    """Test checklist item: Login and logout"""
    # Valid student login
    res = auth.login('student@test.com', 'StudentPass@123')
    assert res.status_code == 200
    assert b'Welcome back, Student User' in res.data

    # Logout
    res_logout = auth.logout()
    assert res_logout.status_code == 200
    assert b'You have been logged out' in res_logout.data


def test_protected_dashboard_redirects_when_logged_out(client):
    """Test checklist item: Visiting /dashboard while logged out redirects to login"""
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

    # Follow redirect
    follow_res = client.get('/dashboard', follow_redirects=True)
    assert follow_res.status_code == 200
    assert b'Sign In' in follow_res.data
