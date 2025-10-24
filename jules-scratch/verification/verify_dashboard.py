from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()
    page.goto("http://127.0.0.1:5000")

    # Login
    page.get_by_label("اسم المستخدم").fill("admin")
    page.get_by_label("كلمة المرور").fill("admin123")
    page.get_by_role("button", name="تسجيل الدخول").click()

    page.wait_for_url("http://127.0.0.1:5000/dashboard")

    # Take screenshot
    page.screenshot(path="jules-scratch/verification/dashboard.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
