
from playwright.sync_api import sync_playwright
import time

def verify_features():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # Login as Admin
        print("Logging in...")
        page.goto("http://127.0.0.1:5000/login")
        page.fill('input[placeholder="اسم المستخدم"]', "admin")
        page.fill('input[placeholder="كلمة المرور"]', "admin123")
        page.click("button:has-text('تسجيل الدخول')")
        page.wait_for_url("**/dashboard")

        # 1. Verify Modern Dashboard Cards
        print("Verifying Dashboard...")
        page.wait_for_selector(".modern-stat-card")
        page.screenshot(path="verification/1_dashboard_modern_cards.png")

        # 2. Verify Mobile Menu Deduplication (Mobile View)
        print("Verifying Mobile Menu...")
        mobile_context = browser.new_context(viewport={"width": 375, "height": 812})
        mobile_page = mobile_context.new_page()

        # Need to login again in new context
        mobile_page.goto("http://127.0.0.1:5000/login")
        mobile_page.fill('input[placeholder="اسم المستخدم"]', "admin")
        mobile_page.fill('input[placeholder="كلمة المرور"]', "admin123")
        mobile_page.click("button:has-text('تسجيل الدخول')")
        mobile_page.wait_for_url("**/dashboard")

        # Click "More" to open overlay
        # Note: The 'More' button is part of the admin mobile nav
        mobile_page.click("text=المزيد")
        time.sleep(1) # Wait for animation
        mobile_page.screenshot(path="verification/2_mobile_menu_overlay.png")

        # 3. Verify Collective Report Redesign
        print("Verifying Collective Report...")
        # We need a circle id. Let's assume ID 1 exists or navigate to it
        # To be safe, go to /collective_report and pick one if possible, or direct to form
        # Assuming there is at least one circle with ID 1 for testing
        try:
            mobile_page.goto("http://127.0.0.1:5000/collective_report/1")
            # Check if page loaded (might redirect if invalid ID)
            if "collective_report_form" in mobile_page.url:
                mobile_page.screenshot(path="verification/3_collective_report_mobile.png")
            else:
                print("Could not access collective report form directly (ID 1 invalid?). Skipping this screenshot.")
        except Exception as e:
            print(f"Error accessing collective report: {e}")

        # 4. Verify Course Details Buttons
        print("Verifying Course Details...")
        # Assuming Course ID 1 exists
        try:
            page.goto("http://127.0.0.1:5000/course/1")
            if page.url.endswith("/course/1"):
                page.screenshot(path="verification/4_course_details.png")
            else:
                 print("Could not access course details (ID 1 invalid?).")
        except Exception as e:
             print(f"Error accessing course details: {e}")

        browser.close()

if __name__ == "__main__":
    verify_features()
