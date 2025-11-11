from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://127.0.0.1:5000/login")
    page.fill('input[name="username"]', "admin")
    page.fill('input[name="password"]', "admin123")
    page.click('button[type="submit"]')
    page.wait_for_url("http://127.0.0.1:5000/dashboard")
    page.goto("http://127.0.0.1:5000/collective_report")
    page.screenshot(path="/home/jules/verification/collective_report_page.png")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
