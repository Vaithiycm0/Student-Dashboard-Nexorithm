from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.student import student_bp
from app.models import Course, Enrollment, Assignment, Submission, get_utc_now
from app.forms import ProfileForm, SubmissionForm
from app.decorators import student_required


def get_student_progress_data(student_id):
    """
    Computes progress metrics according to specification:
    - Completed = submissions with status 'submitted' or 'reviewed'
    - Pending = assignments in enrolled courses with no submission, or status 'pending'
    - Overall % = (completed / total assignments in enrolled courses) * 100
    - Course-wise % = (completed in course / total in course) * 100
    """
    enrollments = Enrollment.query.filter_by(student_id=student_id).all()
    enrolled_course_ids = [e.course_id for e in enrollments]

    if not enrolled_course_ids:
        return {
            'total_assignments': 0,
            'completed_count': 0,
            'pending_count': 0,
            'overall_percent': 0.0,
            'course_stats': []
        }

    all_assignments = Assignment.query.filter(Assignment.course_id.in_(enrolled_course_ids)).all()
    total_assignments = len(all_assignments)

    # Fetch all submissions by this student for these assignments
    assignment_ids = [a.id for a in all_assignments]
    submissions = {
        s.assignment_id: s
        for s in Submission.query.filter(
            Submission.student_id == student_id,
            Submission.assignment_id.in_(assignment_ids)
        ).all()
    } if assignment_ids else {}

    course_stats = []
    completed_count = 0
    pending_count = 0

    for enrollment in enrollments:
        course = enrollment.course
        course_assignments = [a for a in all_assignments if a.course_id == course.id]
        c_total = len(course_assignments)
        c_completed = 0
        c_pending = 0

        for a in course_assignments:
            sub = submissions.get(a.id)
            if sub and sub.status in ['submitted', 'reviewed']:
                c_completed += 1
            else:
                c_pending += 1

        c_percent = round((c_completed / c_total * 100), 1) if c_total > 0 else 0.0
        course_stats.append({
            'course': course,
            'total': c_total,
            'completed': c_completed,
            'pending': c_pending,
            'percent': c_percent
        })

        completed_count += c_completed
        pending_count += c_pending

    overall_percent = round((completed_count / total_assignments * 100), 1) if total_assignments > 0 else 0.0

    return {
        'total_assignments': total_assignments,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'overall_percent': overall_percent,
        'course_stats': course_stats
    }


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    progress_data = get_student_progress_data(current_user.id)
    enrollments = current_user.enrollments.all()
    enrolled_course_ids = [e.course_id for e in enrollments]

    now = get_utc_now()
    upcoming_assignments = []
    if enrolled_course_ids:
        assignments = Assignment.query.filter(
            Assignment.course_id.in_(enrolled_course_ids)
        ).order_by(Assignment.deadline.asc()).all()

        for a in assignments:
            sub = current_user.get_submission_for(a.id)
            status = sub.status if sub else 'pending'
            is_overdue = a.deadline < now and status not in ['submitted', 'reviewed']

            upcoming_assignments.append({
                'assignment': a,
                'course': a.course,
                'submission': sub,
                'status': status,
                'is_overdue': is_overdue
            })

    return render_template(
        'student/dashboard.html',
        progress_data=progress_data,
        enrollments=enrollments,
        upcoming_assignments=upcoming_assignments[:6]  # show upcoming on dashboard
    )


@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # If user attempts to change password
        if form.new_password.data:
            if not form.current_password.data:
                flash('Please enter your current password to set a new password.', 'danger')
                return render_template('student/profile.html', form=form)
            if not current_user.check_password(form.current_password.data):
                flash('Incorrect current password.', 'danger')
                return render_template('student/profile.html', form=form)
            current_user.set_password(form.new_password.data)

        current_user.name = form.name.data.strip()
        current_user.department = form.department.data.strip() if form.department.data else None
        current_user.year = form.year.data if form.year.data else None
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', form=form)


@student_bp.route('/courses')
@login_required
@student_required
def courses():
    all_courses = Course.query.order_by(Course.code.asc()).all()
    enrolled_course_ids = {e.course_id for e in current_user.enrollments.all()}
    return render_template(
        'student/courses.html',
        courses=all_courses,
        enrolled_course_ids=enrolled_course_ids
    )


@student_bp.route('/courses/<int:id>/enroll', methods=['POST'])
@login_required
@student_required
def enroll(id):
    course = db.get_or_404(Course, id)
    existing_enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course.id
    ).first()

    if existing_enrollment:
        flash(f'You are already enrolled in {course.code} - {course.title}.', 'info')
    else:
        new_enrollment = Enrollment(student_id=current_user.id, course_id=course.id)
        db.session.add(new_enrollment)
        db.session.commit()
        flash(f'Successfully enrolled in {course.code}: {course.title}!', 'success')

    return redirect(url_for('student.courses'))


@student_bp.route('/assignments')
@login_required
@student_required
def assignments():
    enrollments = current_user.enrollments.all()
    enrolled_course_ids = [e.course_id for e in enrollments]

    status_filter = request.args.get('filter', 'all')
    now = get_utc_now()

    items = []
    if enrolled_course_ids:
        all_assignments = Assignment.query.filter(
            Assignment.course_id.in_(enrolled_course_ids)
        ).order_by(Assignment.deadline.asc()).all()

        for a in all_assignments:
            sub = current_user.get_submission_for(a.id)
            sub_status = sub.status if sub else 'pending'
            is_overdue = a.deadline < now and sub_status not in ['submitted', 'reviewed']

            # Apply filter
            if status_filter == 'pending' and sub_status != 'pending':
                continue
            elif status_filter == 'submitted' and sub_status != 'submitted':
                continue
            elif status_filter == 'reviewed' and sub_status != 'reviewed':
                continue
            elif status_filter == 'overdue' and not is_overdue:
                continue

            items.append({
                'assignment': a,
                'course': a.course,
                'submission': sub,
                'status': sub_status,
                'is_overdue': is_overdue
            })

    return render_template(
        'student/assignments.html',
        items=items,
        current_filter=status_filter,
        has_enrollments=bool(enrolled_course_ids)
    )


@student_bp.route('/assignments/<int:id>/submit', methods=['GET', 'POST'])
@login_required
@student_required
def submit_assignment(id):
    assignment = db.get_or_404(Assignment, id)

    # Ensure student is enrolled in the assignment's course
    if not current_user.is_enrolled(assignment.course_id):
        flash('You must be enrolled in the course to submit this assignment.', 'danger')
        return redirect(url_for('student.courses'))

    submission = current_user.get_submission_for(assignment.id)
    form = SubmissionForm()

    if form.validate_on_submit():
        if not submission:
            submission = Submission(
                assignment_id=assignment.id,
                student_id=current_user.id
            )
            db.session.add(submission)

        submission.link = form.link.data.strip() if form.link.data else None
        submission.notes = form.notes.data.strip() if form.notes.data else None
        submission.status = 'submitted'
        submission.submitted_at = get_utc_now()
        db.session.commit()

        flash('Assignment submitted successfully!', 'success')
        return redirect(url_for('student.assignments'))

    elif request.method == 'GET' and submission:
        form.link.data = submission.link
        form.notes.data = submission.notes

    now = get_utc_now()
    sub_status = submission.status if submission else 'pending'
    is_overdue = assignment.deadline < now and sub_status not in ['submitted', 'reviewed']

    return render_template(
        'student/submit.html',
        form=form,
        assignment=assignment,
        submission=submission,
        is_overdue=is_overdue
    )


@student_bp.route('/progress')
@login_required
@student_required
def progress():
    progress_data = get_student_progress_data(current_user.id)
    return render_template('student/progress.html', progress=progress_data)
