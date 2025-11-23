# app.py (Entry point)
from app import create_app, db
from app.models import User

app = create_app()

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

def setup_database():
    with app.app_context():
        db.create_all()

        # Ensure password_needs_rehash column exists (Self-healing migration for SQLite)
        try:
            # Check if column exists by trying to query it
            db.session.execute(text("SELECT password_needs_rehash FROM user LIMIT 1"))
        except OperationalError:
            print("INFO: 'password_needs_rehash' column missing. Adding it...")
            try:
                # Rollback the failed transaction from the check above
                db.session.rollback()

                # Add the column
                # Determine dialect to be safe, but error was SQLite specific in prompt
                if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                    db.session.execute(text("ALTER TABLE user ADD COLUMN password_needs_rehash BOOLEAN DEFAULT 1"))
                else:
                    db.session.execute(text("ALTER TABLE user ADD COLUMN password_needs_rehash BOOLEAN DEFAULT TRUE"))
                db.session.commit()
                print("INFO: Column 'password_needs_rehash' added successfully.")
            except Exception as e:
                print(f"ERROR: Failed to add 'password_needs_rehash' column: {e}")

        # Idempotent admin creation
        try:
            admin_exists = User.query.filter_by(username='admin').first()
        except Exception as e:
            print(f"Warning: Could not check for admin user (DB error?): {e}")
            admin_exists = True # Skip creation to avoid crash loop if table broken

        if not admin_exists:
            from werkzeug.security import generate_password_hash
            try:
                # Seed badges if needed
                # seed_badges()
                admin_user = User(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    name='المسؤول',
                    role='admin'
                )
                db.session.add(admin_user)
                db.session.commit()
                print("INFO: Created default admin user.")
            except Exception as e:
                print(f"ERROR: Could not create default admin user: {e}")
                db.session.rollback()

if __name__ == '__main__':
    setup_database()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
