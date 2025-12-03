from app import app, db, User, Student, Parent, create_student_username
from werkzeug.security import generate_password_hash
import re

def create_student_accounts():
    with app.app_context():
        students = Student.query.all()
        created_count = 0
        updated_count = 0

        for student in students:
            # Check if user already exists
            # We first check if there is a user with name matching student.name and role='student'
            existing_user = User.query.filter_by(name=student.name, role='student').first()

            if existing_user:
                # If username is different (e.g. old underscore format), we might want to update it?
                # User asked for "It must be matching the name with spaces".
                # If we update username, it might break login if they already use it.
                # However, since this is a requirement to "fix/add", let's update if it differs.
                # BUT, check uniqueness first.

                desired_username = student.name.strip()
                if existing_user.username != desired_username:
                    # Check if desired username is taken by someone else
                    conflict = User.query.filter(User.username == desired_username, User.id != existing_user.id).first()
                    if not conflict:
                        print(f"Updating username for {student.name}: {existing_user.username} -> {desired_username}")
                        existing_user.username = desired_username
                        updated_count += 1
                    else:
                        print(f"Skipping username update for {student.name}: {desired_username} is taken.")
                continue

            # Create new user
            username = create_student_username(student.name)

            # Determine password
            password_plain = '123456' # Default
            if student.student_phone:
                password_plain = re.sub(r'[^\d]', '', student.student_phone)
            elif student.parent_phone:
                password_plain = re.sub(r'[^\d]', '', student.parent_phone)

            print(f"Creating account for {student.name}. Username: {username}, Password: {password_plain}")

            new_user = User(
                username=username,
                password=generate_password_hash(password_plain),
                name=student.name,
                role='student'
            )
            db.session.add(new_user)
            created_count += 1

        try:
            db.session.commit()
            print(f"Successfully created {created_count} accounts and updated {updated_count} usernames.")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating accounts: {e}")

if __name__ == '__main__':
    create_student_accounts()
