from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.admin import admin_bp
from app.models import User, Course, Assignment, Submission, Enrollment
from app.forms import CourseForm, AssignmentForm, ReviewForm
from app.decorators import admin_required


@admin_bp.route('/admin')
@login_required
@admin_required
def admin_home():
    total_students = User.query.filter_by(role='student').count()
    courses = Course.query.order_by(Course.code.asc()).all()
    assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    pending_reviews_count = Submission.query.filter_by(status='submitted').count()

    # Precalculate submission counts per assignment
    assignment_stats = []
    for a in assignments:
        total_enrolled = a.course.student_count
        submitted_count = a.submissions.filter_by(status='submitted').count()
        reviewed_count = a.submissions.filter_by(status='reviewed').count()
        total_subs = submitted_count + reviewed_count

        assignment_stats.append({
            'assignment': a,
            'total_enrolled': total_enrolled,
            'submitted_count': submitted_count,
            'reviewed_count': reviewed_count,
            'total_subs': total_subs
        })

    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        courses=courses,
        assignment_stats=assignment_stats,
        pending_reviews_count=pending_reviews_count
    )


@admin_bp.route('/admin/courses/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_course():
    form = CourseForm()
    if form.validate_on_submit():
        existing = Course.query.filter_by(code=form.code.data.strip().upper()).first()
        if existing:
            flash(f'Course code {form.code.data.upper()} already exists.', 'danger')
            return render_template('admin/course_form.html', form=form, title='Add Course')

        course = Course(
            code=form.code.data.strip().upper(),
            title=form.title.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            faculty_id=current_user.id
        )
        db.session.add(course)
        db.session.commit()
        flash(f'Course {course.code} created successfully!', 'success')
        return redirect(url_for('admin.admin_home'))

    return render_template('admin/course_form.html', form=form, title='Add Course')


@admin_bp.route('/admin/courses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(id):
    course = db.get_or_404(Course, id)
    form = CourseForm(obj=course)

    if form.validate_on_submit():
        code_input = form.code.data.strip().upper()
        existing = Course.query.filter(Course.code == code_input, Course.id != course.id).first()
        if existing:
            flash(f'Course code {code_input} is already used by another course.', 'danger')
            return render_template('admin/course_form.html', form=form, title='Edit Course', course=course)

        course.code = code_input
        course.title = form.title.data.strip()
        course.description = form.description.data.strip() if form.description.data else None
        db.session.commit()
        flash(f'Course {course.code} updated successfully!', 'success')
        return redirect(url_for('admin.admin_home'))

    return render_template('admin/course_form.html', form=form, title='Edit Course', course=course)


@admin_bp.route('/admin/assignments/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_assignment():
    courses = Course.query.order_by(Course.code.asc()).all()
    if not courses:
        flash('You must create at least one course before creating an assignment.', 'warning')
        return redirect(url_for('admin.new_course'))

    form = AssignmentForm()
    form.course_id.choices = [(c.id, f"{c.code} - {c.title}") for c in courses]

    if form.validate_on_submit():
        assignment = Assignment(
            course_id=form.course_id.data,
            title=form.title.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            deadline=form.deadline.data
        )
        db.session.add(assignment)
        db.session.commit()
        flash(f'Assignment "{assignment.title}" created successfully!', 'success')
        return redirect(url_for('admin.admin_home'))

    return render_template('admin/assignment_form.html', form=form, title='Create Assignment')


@admin_bp.route('/admin/assignments/<int:id>/submissions')
@login_required
@admin_required
def view_submissions(id):
    assignment = db.get_or_404(Assignment, id)
    review_form = ReviewForm()

    # Get all enrolled students for this course
    enrolled_students = [e.student for e in assignment.course.enrollments.all()]

    # Map existing submissions by student_id
    submissions_by_student = {
        s.student_id: s for s in assignment.submissions.all()
    }

    student_submission_rows = []
    for student in enrolled_students:
        sub = submissions_by_student.get(student.id)
        student_submission_rows.append({
            'student': student,
            'submission': sub,
            'status': sub.status if sub else 'pending',
            'link': sub.link if sub else None,
            'notes': sub.notes if sub else None,
            'submitted_at': sub.submitted_at if sub else None,
            'remarks': sub.remarks if sub else None,
            'submission_id': sub.id if sub else None
        })

    return render_template(
        'admin/submissions.html',
        assignment=assignment,
        course=assignment.course,
        student_submission_rows=student_submission_rows,
        review_form=review_form
    )


@admin_bp.route('/admin/submissions/<int:id>/review', methods=['POST'])
@login_required
@admin_required
def review_submission(id):
    submission = db.get_or_404(Submission, id)
    form = ReviewForm()

    if form.validate_on_submit():
        submission.status = form.status.data
        submission.remarks = form.remarks.data.strip() if form.remarks.data else None
        db.session.commit()
        flash(f"Submission for {submission.student.name} marked as {submission.status.title()}!", 'success')
    else:
        flash("Error saving review. Please try again.", 'danger')

    return redirect(url_for('admin.view_submissions', id=submission.assignment_id))
