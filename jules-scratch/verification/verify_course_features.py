from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Admin verification
    page.goto("http://localhost:5000/login")
    page.get_by_placeholder("اسم المستخدم").fill("admin")
    page.get_by_placeholder("كلمة المرور").fill("admin123")
    page.get_by_role("button", name="تسجيل الدخول").click()
    page.wait_for_url("http://localhost:5000/dashboard")

    page.goto("http://localhost:5000/courses")
    page.screenshot(path="jules-scratch/verification/debug_courses_page.png")
    page.get_by_role("link", name="عرض التفاصيل").first.click()
    page.screenshot(path="jules-scratch/verification/admin_course_details.png")

    # Parent verification
    page.goto("http://localhost:5000/logout")
    page.goto("http://localhost:5000/login")
    page.get_by_placeholder("اسم المستخدم").fill("testparent")
    page.get_by_placeholder("كلمة المرور").fill("password")
    page.get_by_role("button", name="تسجيل الدخول").click()
    page.wait_for_url("http://localhost:5000/parent_dashboard")
    page.screenshot(path="jules-scratch/verification/parent_dashboard.png")

    page.get_by_role("link", name="عرض التفاصيل").first.click()
    page.screenshot(path="jules-scratch/verification/parent_student_details.png")


    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
