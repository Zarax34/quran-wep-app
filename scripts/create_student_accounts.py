from app import app, db, User, Student, create_student_username
from werkzeug.security import generate_password_hash

def create_accounts():
    with app.app_context():
        students = Student.query.filter_by(is_active=True).all()
        created_count = 0
        updated_count = 0

        print(f"Checking {len(students)} students...")

        for student in students:
            # Check if user account exists (by name match, assuming create_student_username logic)
            # This is a bit heuristic because username might be name_1, name_2.
            # A better link is ideal, but we don't have user_id on Student table (only parent_id).
            # We check if a User with role='student' and name=student.name exists.

            existing_user = User.query.filter_by(name=student.name, role='student').first()

            password_source = student.student_phone if student.student_phone else student.parent_phone
            if not password_source:
                password_source = '123456'

            if not existing_user:
                # Create new
                username = create_student_username(student.name)
                new_user = User(
                    username=username,
                    password=generate_password_hash(password_source),
                    name=student.name,
                    role='student'
                )
                db.session.add(new_user)
                created_count += 1
                print(f"Created account for {student.name} (User: {username})")
            else:
                # Update password only? Or assume existing is fine.
                # User asked to "Add accounts... password is phone".
                # I will update the password to match the rule to be safe.
                existing_user.password = generate_password_hash(password_source)
                updated_count += 1
                # print(f"Updated password for {student.name}")

        db.session.commit()
        print(f"Done. Created: {created_count}, Updated: {updated_count}")

if __name__ == "__main__":
    create_accounts()
