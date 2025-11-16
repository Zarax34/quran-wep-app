from app import app, db, User, Parent, Student, Circle
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_test_data():
    with app.app_context():
        # 1. Create Teacher
        teacher_user = User.query.filter_by(username='test_teacher').first()
        if not teacher_user:
            teacher_user = User(
                username='test_teacher',
                password=generate_password_hash('password123'),
                name='Test Teacher',
                role='teacher'
            )
            db.session.add(teacher_user)
            db.session.commit()
            print("Test teacher created.")

        # 2. Create Circle
        circle = Circle.query.filter_by(name='Test Circle').first()
        if not circle:
            circle = Circle(
                name='Test Circle',
                teacher_id=teacher_user.id
            )
            db.session.add(circle)
            db.session.commit()
            print("Test circle created.")

        # 3. Create Parent and User 'sara_ahmed'
        parent_user = User.query.filter_by(username='sara_ahmed').first()
        if not parent_user:
            parent_user = User(
                username='sara_ahmed',
                password=generate_password_hash('password123'),
                name='Sara Ahmed',
                role='parent'
            )
            db.session.add(parent_user)
            db.session.commit()
            print("Test parent user 'sara_ahmed' created.")

        parent = Parent.query.filter_by(user_id=parent_user.id).first()
        if not parent:
            parent = Parent(
                name='Sara Ahmed',
                phone='987654321',
                user_id=parent_user.id
            )
            db.session.add(parent)
            db.session.commit()
            print("Test parent profile for 'sara_ahmed' created.")

        # 4. Create an Approved Student
        student = Student.query.filter_by(name='Test Student').first()
        if not student:
            student = Student(
                name='Test Student',
                age=10,
                parent_id=parent.id,
                circle_id=circle.id,
                enrollment_date=datetime.now().date(),
                pending_approval=False,  # Explicitly approve the student
                is_active=True
            )
            db.session.add(student)
            db.session.commit()
            print("Test student created, approved, and active.")
        else:
            # If student exists, ensure they are approved and active
            student.pending_approval = False
            student.is_active = True
            db.session.commit()
            print("Existing test student has been approved and activated.")


if __name__ == '__main__':
    create_test_data()
