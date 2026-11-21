from datetime import timedelta
from app import db
from app.models import Enrollment, Assignment, Submission, get_utc_now


def test_student_enroll_and_dashboard_view(client, seed_data, auth):
    """Test checklist item: Student enrolls and sees assignment on dashboard"""
    auth.login('student@test.com', 'StudentPass@123')

    # Student enrolls in course
    enroll_res = client.post(f"/courses/{seed_data['course'].id}/enroll", follow_redirects=True)
    assert enroll_res.status_code == 200
    assert b'Successfully enrolled' in enroll_res.data

    # Verify enrollment in DB
    enrollment = Enrollment.query.filter_by(student_id=seed_data['student'].id, course_id=seed_data['course'].id).first()
    assert enrollment is not None

    # Check student dashboard shows the assignment
    dash_res = client.get('/dashboard')
    assert dash_res.status_code == 200
    assert b'Assignment 1' in dash_res.data


def test_student_submission_flow(client, seed_data, auth):
    """Test checklist item: Student submits a link; status changes"""
    auth.login('student@test.com', 'StudentPass@123')

    # Enroll first
    client.post(f"/courses/{seed_data['course'].id}/enroll", follow_redirects=True)

    # Submit assignment
    sub_res = client.post(f"/assignments/{seed_data['assignment'].id}/submit", data={
        'link': 'https://github.com/student/my-solution',
        'notes': 'All test cases passing successfully.'
    }, follow_redirects=True)

    assert sub_res.status_code == 200
    assert b'Assignment submitted successfully' in sub_res.data

    # Check submission status in DB
    sub = Submission.query.filter_by(assignment_id=seed_data['assignment'].id, student_id=seed_data['student'].id).first()
    assert sub is not None
    assert sub.status == 'submitted'
    assert sub.link == 'https://github.com/student/my-solution'


def test_progress_calculation(client, seed_data, auth):
    """Test checklist item: Progress percentages update correctly"""
    student = seed_data['student']
    course = seed_data['course']
    auth.login('student@test.com', 'StudentPass@123')

    # Enroll
    client.post(f"/courses/{course.id}/enroll", follow_redirects=True)

    # Add second assignment to this course
    a2 = Assignment(course_id=course.id, title="Assignment 2", deadline=get_utc_now() + timedelta(days=5))
    db.session.add(a2)
    db.session.commit()

    # Before any submission: 0 completed out of 2 = 0%
    prog_res = client.get('/progress')
    assert b'0.0%' in prog_res.data

    # Submit assignment 1
    client.post(f"/assignments/{seed_data['assignment'].id}/submit", data={
        'link': 'https://github.com/solution1',
        'notes': 'Done'
    }, follow_redirects=True)

    # Now 1 completed out of 2 = 50%
    prog_res2 = client.get('/progress')
    assert b'50.0%' in prog_res2.data


def test_profile_update_and_password_change(client, seed_data, auth):
    """Test checklist item: Profile update and password change work"""
    auth.login('student@test.com', 'StudentPass@123')

    # Update profile name and department
    res = client.post('/profile', data={
        'name': 'Updated Student Name',
        'department': 'Robotics',
        'year': 4
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b'Profile updated successfully' in res.data
    assert seed_data['student'].name == 'Updated Student Name'
    assert seed_data['student'].department == 'Robotics'

    # Change password
    pwd_res = client.post('/profile', data={
        'name': 'Updated Student Name',
        'department': 'Robotics',
        'year': 4,
        'current_password': 'StudentPass@123',
        'new_password': 'BrandNewPassword@456',
        'confirm_new_password': 'BrandNewPassword@456'
    }, follow_redirects=True)

    assert pwd_res.status_code == 200
    assert b'Profile updated successfully' in pwd_res.data

    # Verify student can login with the new password
    auth.logout()
    re_login = auth.login('student@test.com', 'BrandNewPassword@456')
    assert b'Welcome back, Updated Student Name' in re_login.data
