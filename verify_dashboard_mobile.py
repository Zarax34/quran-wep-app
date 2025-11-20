import os
import pytest
from playwright.sync_api import sync_playwright
from werkzeug.security import generate_password_hash
from app import app, db, User, Parent, Student, Report, Circle
from datetime import datetime

# Setup test data in a separate script to ensure database state
def setup_test_data():
    with app.app_context():
        # Ensure clean state
        db.drop_all()
        db.create_all()

        # Create Circle
        circle = Circle(name="Test Circle")
        db.session.add(circle)
        db.session.commit()

        # Create Admin
        admin = User(username="admin", password=generate_password_hash("admin123"), role="admin", name="Admin User")
        db.session.add(admin)

        # Create Teacher
        teacher = User(username="teacher", password=generate_password_hash("teacher123"), role="teacher", name="Teacher User")
        db.session.add(teacher)

        # Create Parent
        parent_user = User(username="parent", password=generate_password_hash("parent123"), role="parent", name="Parent User")
        db.session.add(parent_user)
        db.session.commit()

        parent = Parent(name="Parent User", phone="123456789", user_id=parent_user.id)
        db.session.add(parent)
        db.session.commit()

        # Create Student
        student = Student(name="Test Student", circle_id=circle.id, parent_id=parent.id, is_active=True)
        db.session.add(student)
        db.session.commit()

        # Create Reports
        report1 = Report(
            student_id=student.id,
            teacher_id=teacher.id,
            circle_id=circle.id,
            date=datetime.now().date(),
            surah="الفاتحة",
            from_verse=1,
            to_verse=7,
            grade="ممتاز",
            type="حفظ",
            notes="Good job"
        )
        db.session.add(report1)
        db.session.commit()
        print("Test data created.")

def verify_dashboard_mobile():
    setup_test_data()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Mobile viewport
        context = browser.new_context(viewport={"width": 375, "height": 812})
        page = context.new_page()

        try:
            # Login as Admin
            page.goto("http://localhost:5000/login")
            page.get_by_placeholder("اسم المستخدم").fill("admin")
            page.get_by_placeholder("كلمة المرور").fill("admin123")
            page.get_by_role("button", name="تسجيل الدخول").click()

            # Wait for dashboard
            page.wait_for_url("http://localhost:5000/dashboard")

            # Verify "Card" view is visible and "Table" view is hidden
            # The card wrapper has class 'd-block d-md-none'
            # The table wrapper has class 'table-responsive d-none d-md-block'

            # Check if card exists
            page.wait_for_selector(".card.mb-3.shadow-sm")

            # Take screenshot of the reports section
            # We scroll to the bottom where reports usually are
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            page.screenshot(path="verification.png")
            print("Screenshot taken: verification.png")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_dashboard_mobile()
