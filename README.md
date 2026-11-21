# Student Dashboard

A web-based student management dashboard where students track courses, assignments, submissions and academic progress, and faculty/admins manage courses, assignments and review submissions.

- **Live demo:** https://student-dashboard-nexorithm.onrender.com

---

## 1. Features

### Student
- **Authentication & Security:** Register, login, logout (secure password hashing using Werkzeug, session-based auth).
- **Protected Dashboard:** Login required; unauthorized visits redirect to login.
- **Profile Management:** View and update profile details (name, email, department, academic year) and change password securely.
- **Student Dashboard:** View student personal info, enrolled courses, upcoming assignments, and completion status metrics.
- **Assignment Tracking:** View all course assignments with due dates and automatically highlighted overdue indicators.
- **Submission Workflow:** Submit work via URL link or written notes/text; update submission anytime (Pending / Submitted / Reviewed).
- **Academic Progress:** Visual metrics for completed vs pending tasks, per-course progress bars, and overall completion percentage with interactive Chart.js charts.

### Admin / Faculty
- **Course Management:** Add and edit academic courses with course codes and descriptions.
- **Assignment Creation:** Create assignments with titles, descriptions, associated courses, and strict deadlines.
- **Submission Overview:** View all enrolled students and their submission statuses per assignment.
- **Review & Feedback:** Mark submissions as Reviewed and provide individualized faculty remarks.

---

## 2. Tech Stack

| Layer | Choice |
| :--- | :--- |
| **Backend** | Python, Flask |
| **ORM** | Flask-SQLAlchemy |
| **Auth** | Flask-Login, Werkzeug password hashing |
| **Forms/CSRF** | Flask-WTF, WTForms |
| **Database** | SQLite (local), PostgreSQL (production) |
| **Frontend** | Jinja2 templates, Bootstrap 5, Chart.js, Bootstrap Icons |
| **Server** | Gunicorn |
| **Hosting** | Render (Web Service + PostgreSQL) |

---

## 3. System Architecture

```text
Browser -> Flask app (routes / blueprints) -> SQLAlchemy models -> Database
           |- auth      (register, login, logout)
           |- student   (dashboard, assignments, progress, profile, courses, enroll)
           |- admin     (courses, assignments, submissions, review)
```

**Role-based access:** Each user has a `role` of `student` or `admin`. A custom `@role_required("admin")` decorator protects all administrative routes server-side.

---

## 4. Database Design

### `users`
| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | Integer PK | Primary key |
| `name` | String | Full user name |
| `email` | String | Unique, indexed |
| `password_hash` | String | Werkzeug hashed |
| `role` | String | `'student'` or `'admin'` |
| `department` | String | Optional |
| `year` | Integer | Optional (1-5) |
| `created_at` | DateTime | Account creation timestamp |

### `courses`
| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | Integer PK | Primary key |
| `code` | String | Unique, e.g. `CS101` |
| `title` | String | Course title |
| `description` | Text | Course syllabus / overview |
| `faculty_id` | FK -> `users.id` | Instructor / Creator |

### `enrollments`
| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | Integer PK | Primary key |
| `student_id` | FK -> `users.id` | Student foreign key |
| `course_id` | FK -> `courses.id` | Course foreign key |
| *Constraints* | Unique (`student_id`, `course_id`) | Prevent duplicate enrollments |

### `assignments`
| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | Integer PK | Primary key |
| `course_id` | FK -> `courses.id` | Associated course |
| `title` | String | Assignment title |
| `description` | Text | Assignment prompt & instructions |
| `deadline` | DateTime | Due date & time |
| `created_at` | DateTime | Timestamp |

### `submissions`
| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | Integer PK | Primary key |
| `assignment_id` | FK -> `assignments.id` | Associated assignment |
| `student_id` | FK -> `users.id` | Submitting student |
| `link` | String | Submission URL (e.g. GitHub/Drive) |
| `notes` | Text | Submission comments / text |
| `status` | String | `'pending'`, `'submitted'`, `'reviewed'` |
| `remarks` | Text | Faculty evaluation remarks |
| `submitted_at` | DateTime | Submission timestamp |
| *Constraints* | Unique (`assignment_id`, `student_id`) | One submission record per student per assignment |

**Relationships:**
- User 1-N Enrollment N-1 Course
- Course 1-N Assignment
- Assignment 1-N Submission N-1 User

---

## 5. Routes

### Auth
| Method | Route | Purpose |
| :--- | :--- | :--- |
| `GET / POST` | `/register` | Student registration |
| `GET / POST` | `/login` | User login (students & faculty/admins) |
| `GET` | `/logout` | User logout |

### Student (login required)
| Method | Route | Purpose |
| :--- | :--- | :--- |
| `GET` | `/dashboard` | Student overview: info, enrolled courses, upcoming assignments, status |
| `GET / POST` | `/profile` | View and update profile, password change |
| `GET` | `/courses` | Browse course catalog and enrollment status |
| `POST` | `/courses/<id>/enroll` | Enroll in a course |
| `GET` | `/assignments` | View all assignments with status (Pending, Submitted, Reviewed, Overdue) |
| `GET / POST` | `/assignments/<id>/submit` | Add or update assignment submission |
| `GET` | `/progress` | Progress stats, course-wise breakdown, and Chart.js charts |

### Admin (admin role required)
| Method | Route | Purpose |
| :--- | :--- | :--- |
| `GET` | `/admin` | Admin dashboard overview |
| `GET / POST` | `/admin/courses/new` | Add new course |
| `GET / POST` | `/admin/courses/<id>/edit` | Edit existing course |
| `GET / POST` | `/admin/assignments/new` | Create assignment with course and deadline |
| `GET` | `/admin/assignments/<id>/submissions` | View all student submissions for an assignment |
| `POST` | `/admin/submissions/<id>/review` | Mark submission as reviewed and add remarks |

---

## 6. Progress Logic

- **Completed:** Submissions with status `submitted` or `reviewed`.
- **Pending:** Assignments in enrolled courses with no submission, or status `pending`.
- **Overall %:** `(completed / total assignments in enrolled courses) * 100`
- **Course-wise %:** `(completed in course / total in course) * 100`

---

## 7. Folder Structure

```text
student-dashboard/
|- app/
|  |- __init__.py        # App factory, extensions, error handlers
|  |- models.py          # SQLAlchemy models (User, Course, Enrollment, Assignment, Submission)
|  |- decorators.py      # @role_required, @admin_required, @student_required
|  |- forms.py           # WTForms for authentication, profile, courses, assignments, submissions
|  |- auth/
|  |  |- __init__.py
|  |  |- routes.py       # Register, login, logout
|  |- student/
|  |  |- __init__.py
|  |  |- routes.py       # Dashboard, profile, courses, assignments, submit, progress
|  |- admin/
|  |  |- __init__.py
|  |  |- routes.py       # Admin home, course creation, assignment creation, submissions review
|  |- templates/         # Jinja2 templates
|  |  |- base.html
|  |  |- auth/
|  |  |  |- login.html
|  |  |  |- register.html
|  |  |- student/
|  |  |  |- dashboard.html
|  |  |  |- profile.html
|  |  |  |- courses.html
|  |  |  |- assignments.html
|  |  |  |- submit.html
|  |  |  |- progress.html
|  |  |- admin/
|  |  |  |- dashboard.html
|  |  |  |- course_form.html
|  |  |  |- assignment_form.html
|  |  |  |- submissions.html
|  |  |- errors/
|  |  |  |- 403.html
|  |  |  |- 404.html
|  |  |  |- 500.html
|  |- static/
|  |  |- css/
|  |  |  |- style.css
|  |  |- js/
|  |  |  |- main.js
|- tests/
|  |- conftest.py
|  |- test_auth.py
|  |- test_student.py
|  |- test_admin.py
|- config.py             # SQLite local / PostgreSQL production configuration
|- seed.py               # Demo accounts, sample courses & assignments
|- requirements.txt      # Project dependencies
|- Procfile              # Gunicorn process definition for Render
|- .env.example          # Sample environment variables
|- .gitignore            # Git ignore file
|- README.md
```

---

## 8. Local Setup

```bash
# 1. Clone repository
git clone <your-github-url>
cd student-dashboard

# 2. Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env

# 5. Populate initial database with demo accounts & courses
python seed.py

# 6. Run local development server
flask --app "app:create_app()" run
```

---

## 9. Demo Accounts (created by `seed.py`)

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@demo.com` | `Admin@123` |
| **Student** | `student@demo.com` | `Student@123` |

---

## 10. Deployment (Render)

1. Push your repository to GitHub.
2. In Render Dashboard, click **New +** -> **PostgreSQL (Free)**:
   - Copy the **Internal Database URL** (or External Database URL).
3. Click **New +** -> **Web Service** -> Connect your GitHub repository:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn "app:create_app()"`
4. Configure Environment Variables in Render:
   - `SECRET_KEY`: Set to a strong random secret.
   - `DATABASE_URL`: Paste the PostgreSQL connection URL (Render `postgres://` URLs are automatically handled and rewritten to `postgresql://` by `config.py`).
5. Deploy the Web Service.
6. Open the Render Web Shell (or run a one-time command) to seed initial data:
   ```bash
   python seed.py
   ```
7. Paste the live deployment URL at the top of this `README.md`.

---

## 11. Testing Checklist

- [x] Register a new student, login, logout
- [x] Visiting `/dashboard` while logged out redirects to login
- [x] Student cannot open any `/admin` route (server-side 403 Forbidden check)
- [x] Admin creates a course and an assignment with a deadline
- [x] Student enrolls and sees assignment on dashboard
- [x] Student submits a link/notes; status updates; admin sees submission
- [x] Progress percentages update accurately according to specification
- [x] Profile update and password change work seamlessly
- [x] Works on deployed URL, not just locally

To execute the automated test suite:
```bash
pytest -v
```

---

## 12. Security Notes

- **Password Hashing:** Passwords are hashed using PBKDF2/SHA256 via Werkzeug and never stored in plain text.
- **CSRF Protection:** Flask-WTF protects all web forms against Cross-Site Request Forgery.
- **Server-Side Role Authorization:** `@role_required("admin")` validates permissions on the server for all admin endpoints.
- **Environment Isolation:** Sensitive secrets are stored in `.env` and kept out of version control via `.gitignore`.

---

## 13. Future Improvements

- Automated email notifications for upcoming deadlines
- Direct file uploads to cloud object storage (AWS S3 or Google Cloud Storage)
- Faculty analytics dashboards and grading rubrics
- Full RESTful API with token-based authentication (JWT)
