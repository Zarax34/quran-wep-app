
from playwright.sync_api import sync_playwright
import time
from datetime import datetime, timedelta

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Log in
    page.goto("http://127.0.0.1:5000/login")
    page.get_by_label("اسم المستخدم").fill("admin")
    page.get_by_label("كلمة المرور").fill("admin123")
    page.get_by_role("button", name="تسجيل الدخول").click()
    time.sleep(5)

    # Create a teacher
    page.goto("http://127.0.0.1:5000/add_user")
    page.get_by_label("الاسم الكامل").fill("Test Teacher")
    page.get_by_label("اسم المستخدم").fill("testteacher")
    page.get_by_label("كلمة المرور").fill("password")
    page.select_option('select[name="role"]', 'teacher')
    page.get_by_role("button", name="إضافة المستخدم").click()
    time.sleep(5)

    # Create a circle
    page.goto("http://127.0.0.1:5000/add_circle")
    page.get_by_label("اسم الحلقة").fill("حلقة الأمة")
    page.get_by_label("أو أدخل اسم المعلم يدوياً").fill("Test Teacher")
    page.get_by_role("button", name="إضافة الحلقة").click()
    time.sleep(5)

    # Create a course
    page.goto("http://127.0.0.1:5000/add_course")
    page.get_by_label("اسم الدورة").fill("My Test Course")
    page.get_by_label("وصف الدورة (اختياري)").fill("This is a test course.")
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    page.get_by_label("تاريخ البدء").fill(start_date)
    page.get_by_label("تاريخ الانتهاء").fill(end_date)
    page.select_option('select[name="teacher_id"]', label='Test Teacher')
    page.get_by_role("button", name="حفظ الدورة").click()
    time.sleep(5)

    # Create a student
    page.goto("http://127.0.0.1:5000/add_student")
    page.get_by_label("الاسم الكامل للطالب").fill("Test Student")
    page.get_by_label("رقم ولي الأمر").fill("777123456")
    page.select_option('select[name="circle_id"]', label='حلقة الأمة - Test Teacher')
    page.get_by_role("button", name="إضافة الطالب").click()
    time.sleep(5)

    # Go to the course and enroll the student
    page.goto("http://127.0.0.1:5000/courses")
    page.get_by_role("link", name="My Test Course").click()
    time.sleep(5)
    page.get_by_role("button", name="تسجيل طالب جديد").click()
    time.sleep(5)
    page.get_by_label("Test Student").check()
    page.get_by_role("button", name="تسجيل الطلاب المحددين").click()
    time.sleep(5)

    # Manually add a certificate URL for the student in this course
    page.locator('button[data-bs-target^="#editEnrollmentModal"]').click()
    time.sleep(5)
    page.get_by_label("رابط الشهادة (Google Drive)").fill("https://example.com/certificate")
    page.get_by_role("button", name="حفظ التغييرات").click()
    time.sleep(5)


    # Take a screenshot of the course details page
    page.screenshot(path="jules-scratch/verification/certificate_link.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
