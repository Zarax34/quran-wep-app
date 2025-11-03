
from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # 1. Log in as admin
    page.goto("http://localhost:5000/login")
    page.fill("input[name='username']", "admin")
    page.fill("input[name='password']", "admin123")
    page.click("button[type='submit']")
    expect(page.get_by_role("heading", name="مرحباً المسؤول 👋")).to_be_visible()

    # 2. Create a parent user
    page.goto("http://localhost:5000/add_parents")
    page.fill("textarea[name='parents_text']", "Test Parent:777123456")
    page.click("button[type='submit']")
    expect(page.get_by_text("تم إضافة 1 من أولياء الأمور بنجاح")).to_be_visible()

    # 3. Log out from admin
    page.goto("http://localhost:5000/logout")
    expect(page.get_by_role("heading", name="أهلاً بك في نظام إدارة مركز تحفيظ القرآن"))

    # 4. Log in as the parent
    page.goto("http://localhost:5000/login")
    page.fill("input[name='username']", "Test Parent")
    page.fill("input[name='password']", "777123456")
    page.click("button[type='submit']")
    expect(page.get_by_role("heading", name="مرحباً Test Parent 👋")).to_be_visible()

    # 5. Take a screenshot of the parent dashboard
    page.screenshot(path="jules-scratch/verification/parent_dashboard.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
