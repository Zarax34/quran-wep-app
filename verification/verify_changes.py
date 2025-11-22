
from playwright.sync_api import sync_playwright
import time

def verify_frontend():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 375, "height": 812}) # Mobile viewport
        page = context.new_page()

        try:
            # 1. Login as Admin to setup
            page.goto("http://localhost:5000/login")
            page.get_by_placeholder("اسم المستخدم").fill("admin")
            page.get_by_placeholder("كلمة المرور").fill("admin123")
            page.get_by_role("button", name="تسجيل الدخول").click()

            # 2. Go to Settings and Enable Permissions
            page.goto("http://localhost:5000/settings")

            # Take screenshot of settings page (bottom part for permissions)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.screenshot(path="verification/settings_permissions.png")
            print("Snapshot of settings permissions taken.")

            # 3. Verify Mobile UI (Bottom Nav)
            page.set_viewport_size({"width": 375, "height": 812})
            page.goto("http://localhost:5000/dashboard")
            time.sleep(1)
            page.screenshot(path="verification/mobile_dashboard_bottom_nav.png")
            print("Snapshot of mobile dashboard with bottom nav taken.")

            # 4. Verify Certificate Upload Button in Course Details
            # Need to find a course first.
            page.goto("http://localhost:5000/courses")
            # Click first course "التفاصيل" button if exists, otherwise create one?
            # Assuming data exists from seed.
            if page.get_by_text("التفاصيل").count() > 0:
                page.get_by_text("التفاصيل").first.click()
                page.screenshot(path="verification/course_details_certificate.png")
                print("Snapshot of course details with certificate options taken.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_frontend()
