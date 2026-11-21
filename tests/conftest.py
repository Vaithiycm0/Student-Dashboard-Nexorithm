import os
import sys
import pytest
from datetime import datetime, timedelta

# Ensure the root project directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Course, Assignment, Enrollment, Submission, get_utc_now
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def seed_data(app):
    """Creates a basic admin, student, course, and assignment for test suites."""
    admin = User(name="Admin User", email="admin@test.com", role="admin")
    admin.set_password("AdminPass@123")

    student = User(name="Student User", email="student@test.com", role="student", department="CS", year=3)
    student.set_password("StudentPass@123")

    db.session.add_all([admin, student])
    db.session.commit()

    course = Course(code="CS101", title="Intro to CS", description="Basics", faculty_id=admin.id)
    db.session.add(course)
    db.session.commit()

    assignment = Assignment(
        course_id=course.id,
        title="Assignment 1",
        description="First task",
        deadline=get_utc_now() + timedelta(days=7)
    )
    db.session.add(assignment)
    db.session.commit()

    return {
        'admin': admin,
        'student': student,
        'course': course,
        'assignment': assignment
    }


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, email, password):
        return self._client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

    def logout(self):
        return self._client.get('/logout', follow_redirects=True)


@pytest.fixture
def auth(client):
    return AuthActions(client)
