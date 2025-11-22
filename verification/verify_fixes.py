
from playwright.sync_api import sync_playwright
import time

def verify_new_features():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Verify Users Mobile View (Mobile Viewport)
        print("Verifying Users Mobile View...")
        mobile_context = browser.new_context(viewport={"width": 375, "height": 812})
        mobile_page = mobile_context.new_page()

        # Login
        mobile_page.goto("http://127.0.0.1:5000/login")
        mobile_page.fill('input[placeholder="اسم المستخدم"]', "admin")
        mobile_page.fill('input[placeholder="كلمة المرور"]', "admin123")
        mobile_page.click("button:has-text('تسجيل الدخول')")
        mobile_page.wait_for_url("**/dashboard")

        # Go to Users page
        mobile_page.goto("http://127.0.0.1:5000/users")
        mobile_page.screenshot(path="verification/1_users_mobile.png")

        # 2. Verify Parent Dashboard (Parent Role)
        # Note: We need a parent user. Assuming 'parent1' exists or we can mock/setup.
        # Since I can't easily switch users without knowing credentials, I'll skip this if I don't have creds.
        # But wait, I can modify the session or just check the template visually if I were logged in as parent.
        # Let's try to verify the Header which is visible to Admin too.

        # 3. Verify Header Revamp
        print("Verifying Header Revamp...")
        mobile_page.goto("http://127.0.0.1:5000/dashboard")
        # Scroll to top to see header
        mobile_page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        mobile_page.screenshot(path="verification/3_header_revamp.png")

        # 4. Verify Accordion in Collective Report (Admin/Teacher)
        # Assuming we can access a report.
        # We need a circle.
        print("Verifying Collective Report Accordion...")
        # Try to find a circle link
        try:
             # Just go to a likely URL
             mobile_page.goto("http://127.0.0.1:5000/collective_report/1")
             # Check if accordion elements exist
             if mobile_page.locator(".student-card-mobile").count() > 0:
                 # Click the first one to toggle
                 mobile_page.click(".student-card-mobile >> nth=0 >> .card-header")
                 time.sleep(0.5)
                 mobile_page.screenshot(path="verification/4_collective_report_accordion.png")
             else:
                 print("No student cards found on collective report page (empty circle?).")
        except Exception as e:
            print(f"Error checking collective report: {e}")

        browser.close()

if __name__ == "__main__":
    verify_new_features()
