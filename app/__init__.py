from datetime import datetime, timezone
from flask import Flask, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    csrf.init_app(app)

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.student.routes import student_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def index():
        try:
            if current_user.is_authenticated:
                if current_user.role == 'admin':
                    return redirect(url_for('admin.admin_home'))
                return redirect(url_for('student.dashboard'))
        except Exception:
            pass
        return redirect(url_for('auth.login'))

    @app.route('/init-db')
    def init_db():
        """Helper route to initialize tables and seed demo data on Render if needed"""
        db.create_all()
        from seed import seed_database
        try:
            seed_database(app)
            return "Database initialized and seeded successfully! <a href='/login'>Go to Login</a>"
        except Exception as e:
            return f"Database already initialized or error: {e}. <a href='/login'>Go to Login</a>"

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.context_processor
    def inject_now():
        return {'now': datetime.now(timezone.utc)}

    # Auto-initialize database tables and seed data if brand new
    if not app.config.get('TESTING'):
        with app.app_context():
            try:
                db.create_all()
                from app.models import User
                if not User.query.first():
                    from seed import seed_database
                    seed_database(app)
            except Exception as e:
                app.logger.warning(f"Auto-init database notice: {e}")

    return app
