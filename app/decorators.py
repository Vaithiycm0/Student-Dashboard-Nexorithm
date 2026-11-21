from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(role):
    """
    Decorator to restrict access to users with a specific role ('admin' or 'student').
    Enforces server-side authorization check.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required('admin')(f)


def student_required(f):
    return role_required('student')(f)
