import re
from playwright.sync_api import Page, expect

def test_report_form(page: Page):
    # Go to http://127.0.0.1:5000/
    page.goto("http://127.0.0.1:5000/")
    # Go to http://127.0.0.1:5000/login
    page.goto("http://127.0.0.1:5000/login")
    # Fill input[name="username"]
    page.locator('input[name="username"]').fill("admin")
    # Press Tab
    page.locator('input[name="username"]').press("Tab")
    # Fill input[name="password"]
    page.locator('input[name="password"]').fill("admin123")
    # Click button:has-text("تسجيل الدخول")
    page.locator('button:has-text("تسجيل الدخول")').click()
    expect(page).to_have_url("http://127.0.0.1:5000/dashboard")

    # Add a circle
    page.goto("http://127.0.0.1:5000/add_circle")
    page.locator('input[name="name"]').fill("حلقة جديدة")
    page.locator('button:has-text("إضافة الحلقة")').click()

    # Add a student
    page.goto("http://127.0.0.1:5000/add_student")
    page.locator('input[name="name"]').fill("طالب جديد")
    page.locator('input[name="parent_phone"]').fill("777123456")
    page.locator('select[name="circle_id"]').select_option("1")
    page.locator('button:has-text("إضافة الطالب")').click()

    # Go to http://127.0.0.1:5000/add_report
    page.goto("http://127.0.0.1:5000/add_report")

    # Select a student
    page.locator('select[name="student_id"]').select_option("1")
    # Select a surah
    page.locator('select[name="surah"]').select_option("البقرة")
    # Select a from verse
    page.locator('select[name="from_verse"]').select_option("10")
    # Select a to verse
    page.locator('select[name="to_verse"]').select_option("20")

    # Take screenshot
    page.screenshot(path="jules-scratch/verification/verification.png")
