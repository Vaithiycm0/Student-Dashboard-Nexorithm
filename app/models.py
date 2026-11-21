from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


def get_utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        db.session.rollback()
        return None


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' or 'admin'
    department = db.Column(db.String(100), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    courses_taught = db.relationship('Course', backref='faculty', lazy='dynamic', foreign_keys='Course.faculty_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_student(self):
        return self.role == 'student'

    def is_enrolled(self, course_id):
        return self.enrollments.filter_by(course_id=course_id).first() is not None

    def get_submission_for(self, assignment_id):
        return self.submissions.filter_by(assignment_id=assignment_id).first()

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., CS101
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='course', lazy='dynamic', cascade='all, delete-orphan', order_by='Assignment.deadline.asc()')

    @property
    def student_count(self):
        return self.enrollments.count()

    @property
    def assignment_count(self):
        return self.assignments.count()

    def __repr__(self):
        return f'<Course {self.code}: {self.title}>'


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='uq_student_course'),
    )

    def __repr__(self):
        return f'<Enrollment Student:{self.student_id} Course:{self.course_id}>'


class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    # Relationships
    submissions = db.relationship('Submission', backref='assignment', lazy='dynamic', cascade='all, delete-orphan')

    def is_overdue(self, student=None):
        """
        Check if assignment is overdue.
        If a student is provided, an assignment is overdue only if current time > deadline
        AND student has not submitted or been reviewed.
        If no student is provided, it's overdue strictly based on deadline < now.
        """
        now = get_utc_now()
        if now <= self.deadline:
            return False

        if student is not None:
            sub = student.get_submission_for(self.id)
            if sub and sub.status in ['submitted', 'reviewed']:
                return False
        return True

    def get_submission_count(self):
        return self.submissions.filter(Submission.status.in_(['submitted', 'reviewed'])).count()

    def __repr__(self):
        return f'<Assignment {self.title} (Course {self.course_id})>'


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    link = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'submitted', 'reviewed'
    remarks = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('assignment_id', 'student_id', name='uq_assignment_student'),
    )

    def __repr__(self):
        return f'<Submission Student:{self.student_id} Assignment:{self.assignment_id} Status:{self.status}>'
