
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()

    # Parent verification
    page.goto("http://127.0.0.1:5000/login")
    page.fill("input[name=username]", "testparent")
    page.fill("input[name=password]", "password")
    page.click("button[type=submit]")
    page.wait_for_url("http://127.0.0.1:5000/parent_dashboard")
    page.screenshot(path="jules-scratch/verification/parent_dashboard.png")

    page.goto("http://127.0.0.1:5000/logout")
    page.wait_for_url("http://127.0.0.1:5000/")

    # Student verification
    page.goto("http://127.0.0.1:5000/login")
    page.fill("input[name=username]", "teststudent")
    page.fill("input[name=password]", "password")
    page.click("button[type=submit]")
    # The student is redirected to student_details
    page.wait_for_url(lambda url: "student_details" in url)
    page.screenshot(path="jules-scratch/verification/student_details.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
