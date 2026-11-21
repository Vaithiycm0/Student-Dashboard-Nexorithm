"""
Database Seeding Script for Student Dashboard
Creates all tables and populates initial demo data:
- Demo Admin: admin@demo.com / Admin@123
- Demo Student: student@demo.com / Student@123
- Sample courses, assignments (both upcoming & overdue), enrollments, and submissions.
"""
from datetime import timedelta
from app import create_app, db
from app.models import User, Course, Enrollment, Assignment, Submission, get_utc_now


def seed_database():
    app = create_app()
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()

        # Check if already seeded
        if User.query.filter_by(email='admin@demo.com').first():
            print("Database already contains demo accounts. Skipping seeding.")
            return

        print("Seeding demo accounts...")
        # 1. Create Admin
        admin = User(
            name="Professor Alan Turing",
            email="admin@demo.com",
            role="admin",
            department="Computer Science",
            year=None
        )
        admin.set_password("Admin@123")
        db.session.add(admin)

        # 2. Create Student
        student = User(
            name="Ada Lovelace",
            email="student@demo.com",
            role="student",
            department="Computer Science",
            year=3
        )
        student.set_password("Student@123")
        db.session.add(student)

        # Additional sample student
        student2 = User(
            name="Grace Hopper",
            email="grace@demo.com",
            role="student",
            department="Software Engineering",
            year=2
        )
        student2.set_password("Student@123")
        db.session.add(student2)

        db.session.commit()

        print("Seeding courses...")
        # 3. Create Courses
        course1 = Course(
            code="CS101",
            title="Introduction to Web Development",
            description="Comprehensive introduction to HTML5, CSS3, JavaScript, Python, and Flask framework architecture.",
            faculty_id=admin.id
        )
        course2 = Course(
            code="CS201",
            title="Data Structures & Algorithms",
            description="Fundamental data structures including lists, stacks, queues, trees, graphs, and algorithmic complexity analysis.",
            faculty_id=admin.id
        )
        course3 = Course(
            code="CS301",
            title="Database Management Systems",
            description="Relational database models, SQL design, ACID properties, indexing, and object-relational mapping (ORM).",
            faculty_id=admin.id
        )
        db.session.add_all([course1, course2, course3])
        db.session.commit()

        print("Seeding enrollments...")
        # 4. Enroll Student in Course 1 & 2
        e1 = Enrollment(student_id=student.id, course_id=course1.id)
        e2 = Enrollment(student_id=student.id, course_id=course2.id)
        e3 = Enrollment(student_id=student2.id, course_id=course1.id)
        db.session.add_all([e1, e2, e3])
        db.session.commit()

        print("Seeding assignments...")
        now = get_utc_now()

        # Course 1 Assignments
        a1 = Assignment(
            course_id=course1.id,
            title="Lab 1: Responsive Portfolio Website",
            description="Build a fully responsive personal portfolio webpage using Bootstrap 5 and semantic HTML.",
            deadline=now - timedelta(days=5),  # Past deadline
            created_at=now - timedelta(days=12)
        )
        a2 = Assignment(
            course_id=course1.id,
            title="Milestone 1: Flask CRUD Application",
            description="Implement a multi-route Flask application with SQLite database persistence and Jinja2 templating.",
            deadline=now + timedelta(days=4),  # Upcoming
            created_at=now - timedelta(days=3)
        )
        a3 = Assignment(
            course_id=course1.id,
            title="Final Project: Production Cloud Deployment",
            description="Deploy your Flask application to Render with PostgreSQL database connection and environment variables.",
            deadline=now + timedelta(days=14),  # Upcoming
            created_at=now - timedelta(days=1)
        )

        # Course 2 Assignments
        a4 = Assignment(
            course_id=course2.id,
            title="Problem Set 1: Binary Search Trees",
            description="Implement balanced binary search tree insertion, traversal, and deletion algorithms in Python.",
            deadline=now - timedelta(days=2),  # Past deadline (test overdue highlighting)
            created_at=now - timedelta(days=8)
        )
        a5 = Assignment(
            course_id=course2.id,
            title="Problem Set 2: Graph Pathfinding (Dijkstra)",
            description="Implement Dijkstra's shortest path algorithm using a min-heap priority queue.",
            deadline=now + timedelta(days=7),  # Upcoming
            created_at=now - timedelta(days=2)
        )

        db.session.add_all([a1, a2, a3, a4, a5])
        db.session.commit()

        print("Seeding submissions...")
        # a1 for student: Submitted and Reviewed with Remarks
        sub1 = Submission(
            assignment_id=a1.id,
            student_id=student.id,
            link="https://github.com/demo/portfolio-project",
            notes="Completed responsive layout with dark mode toggle and fluid grids.",
            status="reviewed",
            remarks="Excellent work on responsive typography and clean semantic markup. 10/10!",
            submitted_at=now - timedelta(days=6)
        )

        # a2 for student: Submitted, awaiting review
        sub2 = Submission(
            assignment_id=a2.id,
            student_id=student.id,
            link="https://github.com/demo/flask-crud-demo",
            notes="Implemented user authentication, SQLite ORM models, and WTForms validation.",
            status="submitted",
            remarks=None,
            submitted_at=now - timedelta(hours=10)
        )

        # a4 for student is deliberately unsubmitted to demonstrate the "OVERDUE" highlighting!
        # a3 and a5 are pending and upcoming.

        db.session.add_all([sub1, sub2])
        db.session.commit()

        print("\n=== Seeding Complete ===")
        print("Demo Accounts:")
        print("  Admin:   admin@demo.com   / Admin@123")
        print("  Student: student@demo.com / Student@123")
        print("========================\n")


if __name__ == '__main__':
    seed_database()
