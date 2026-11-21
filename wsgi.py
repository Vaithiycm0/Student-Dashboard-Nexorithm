import os
from app import create_app, db

app = create_app()

# Auto-create database tables on startup if they don't exist
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        app.logger.error(f"Error creating database tables: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
