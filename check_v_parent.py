
from app import app, db, User

def check_user(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"User Found:")
            print(f"  ID: {user.id}")
            print(f"  Username: {user.username}")
            print(f"  Name: {user.name}")
            print(f"  Role: {user.role}")
            print(f"  Is Active: {user.is_active}")
            print(f"  Password Hash (first 20 chars): {user.password[:20]}...")
        else:
            print(f"User '{username}' not found.")

if __name__ == '__main__':
    check_user('v_parent')
