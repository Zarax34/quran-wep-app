from app import app, db, User, Parent
from werkzeug.security import generate_password_hash

def create_test_parent_user():
    with app.app_context():
        # Check if user already exists
        user = User.query.filter_by(username='parent_test').first()
        if user:
            # Ensure the corresponding parent record exists
            parent = Parent.query.filter_by(user_id=user.id).first()
            if not parent:
                new_parent = Parent(
                    user_id=user.id,
                    name="Test Parent", # Name is on the Parent model now
                    phone="1234567890" # Example phone
                )
                db.session.add(new_parent)
                db.session.commit()
                print("Created corresponding parent record for existing user.")
            else:
                print("Test parent user and parent record already exist.")
            return

        # Create a new user if it doesn't exist
        hashed_password = generate_password_hash('password', method='pbkdf2:sha256')
        new_user = User(
            username='parent_test',
            password=hashed_password,
            role='parent',
            name="Test Parent"  # Add the required name field
        )
        db.session.add(new_user)
        db.session.commit()

        # Create a corresponding parent entry
        new_parent = Parent(
            user_id=new_user.id,
            name="Test Parent",
            phone="1234567890" # Make sure phone is unique if required
        )
        db.session.add(new_parent)
        db.session.commit()

        print(f"Created test user 'parent_test' with id {new_user.id} and parent record with id {new_parent.id}")

if __name__ == '__main__':
    create_test_parent_user()
