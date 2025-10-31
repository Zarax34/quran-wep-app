from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Login
    page.goto("http://127.0.0.1:5000/login")
    page.fill("input[name='username']", "admin")
    page.fill("input[name='password']", "admin123")
    page.click("button[type='submit']")

    # Add student page
    page.goto("http://127.0.0.1:5000/add_student")
    page.screenshot(path="jules-scratch/verification/add_student.png")

    # Students page
    page.goto("http://127.0.0.1:5000/students")
    page.screenshot(path="jules-scratch/verification/students.png")

    # Parent management page
    page.goto("http://127.0.0.1:5000/parent_management")
    page.screenshot(path="jules-scratch/verification/parent_management.png")

    # Review delete requests page
    page.goto("http://127.0.0.1:5000/review_delete_requests")
    page.screenshot(path="jules-scratch/verification/review_delete_requests.png")

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
