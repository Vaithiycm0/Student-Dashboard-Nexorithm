from datetime import timedelta
from app import db
from app.models import Course, Assignment, Submission, Enrollment, get_utc_now


def test_student_cannot_access_admin_routes(client, seed_data, auth):
    """Test checklist item: Student cannot open any /admin route (server-side 403)"""
    auth.login('student@test.com', 'StudentPass@123')

    # Student attempts to access admin home
    res1 = client.get('/admin')
    assert res1.status_code == 403

    # Student attempts to access course creation
    res2 = client.get('/admin/courses/new')
    assert res2.status_code == 403

    # Student attempts to access assignment creation
    res3 = client.get('/admin/assignments/new')
    assert res3.status_code == 403


def test_admin_creates_course_and_assignment(client, seed_data, auth):
    """Test checklist item: Admin creates a course and an assignment with a deadline"""
    auth.login('admin@test.com', 'AdminPass@123')

    # Admin creates course
    res_course = client.post('/admin/courses/new', data={
        'code': 'CS302',
        'title': 'Advanced Cloud Architecture',
        'description': 'Microservices and Kubernetes orchestration.'
    }, follow_redirects=True)

    assert res_course.status_code == 200
    assert b'Course CS302 created successfully' in res_course.data

    course = Course.query.filter_by(code='CS302').first()
    assert course is not None

    # Admin creates assignment for CS302
    deadline_dt = get_utc_now() + timedelta(days=10)
    res_assign = client.post('/admin/assignments/new', data={
        'course_id': course.id,
        'title': 'Project: Containerized Deployments',
        'description': 'Write Dockerfiles and compose specs.',
        'deadline': deadline_dt.strftime('%Y-%m-%dT%H:%M')
    }, follow_redirects=True)

    assert res_assign.status_code == 200
    assert b'created successfully' in res_assign.data

    assignment = Assignment.query.filter_by(title='Project: Containerized Deployments').first()
    assert assignment is not None
    assert assignment.course_id == course.id


def test_admin_views_submissions_and_reviews(client, seed_data, auth):
    """Test checklist item: Admin reviews submission and adds remarks"""
    # 1. Student enrolls and submits
    auth.login('student@test.com', 'StudentPass@123')
    client.post(f"/courses/{seed_data['course'].id}/enroll")
    client.post(f"/assignments/{seed_data['assignment'].id}/submit", data={
        'link': 'https://github.com/student/homework',
        'notes': 'Please review my PR.'
    })
    auth.logout()

    # 2. Admin logs in to view and review
    auth.login('admin@test.com', 'AdminPass@123')
    sub_view = client.get(f"/admin/assignments/{seed_data['assignment'].id}/submissions")
    assert sub_view.status_code == 200
    assert b'https://github.com/student/homework' in sub_view.data

    # Get submission ID
    submission = Submission.query.filter_by(assignment_id=seed_data['assignment'].id).first()
    assert submission is not None

    # Admin reviews submission
    rev_res = client.post(f"/admin/submissions/{submission.id}/review", data={
        'status': 'reviewed',
        'remarks': 'Outstanding architecture and clean tests! Grade: 100/100'
    }, follow_redirects=True)

    assert rev_res.status_code == 200
    assert b'Reviewed' in rev_res.data

    # Verify submission updated in DB
    updated_sub = db.session.get(Submission, submission.id)
    assert updated_sub.status == 'reviewed'
    assert 'Outstanding architecture' in updated_sub.remarks
