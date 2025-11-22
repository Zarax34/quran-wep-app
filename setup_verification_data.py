from app import app, db, User, Student, EducationalNote, Circle
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    # Create Admin
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', password=generate_password_hash('admin123'), name='Admin', role='admin')
        db.session.add(admin)

    # Create Teacher
    teacher = User.query.filter_by(username='teacher').first()
    if not teacher:
        teacher = User(username='teacher', password=generate_password_hash('teacher123'), name='Teacher', role='teacher')
        db.session.add(teacher)

    # Create Circle
    circle = Circle.query.filter_by(name='Test Circle').first()
    if not circle:
        circle = Circle(name='Test Circle', teacher_id=teacher.id if teacher else None)
        db.session.add(circle)
        db.session.commit()

    # Create Student
    student = Student.query.filter_by(name='Test Student').first()
    if not student:
        student = Student(name='Test Student', circle_id=circle.id)
        db.session.add(student)
        db.session.commit()

    # Add Educational Note (to test the card display)
    note = EducationalNote.query.filter_by(student_id=student.id).first()
    if not note:
        note = EducationalNote(student_id=student.id, teacher_id=admin.id if admin else 1, note='This is a test note.', date=datetime.now().date())
        db.session.add(note)

    db.session.commit()
    print("Test data created.")
