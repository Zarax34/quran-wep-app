# app.py (Entry point)
from app import create_app, db
from app.models import User

app = create_app()

def setup_database():
    with app.app_context():
        db.create_all()
        
        # Idempotent admin creation
        admin_exists = User.query.filter_by(username='admin').first()
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
