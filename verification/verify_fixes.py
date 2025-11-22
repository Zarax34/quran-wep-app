
from playwright.sync_api import sync_playwright
import time

def verify_updates():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 375, "height": 812})
        page = context.new_page()

        try:
            # 1. Login
            page.goto("http://localhost:5000/login")
            page.get_by_placeholder("اسم المستخدم").fill("admin")
            page.get_by_placeholder("كلمة المرور").fill("admin123")
            page.get_by_role("button", name="تسجيل الدخول").click()

            # 2. Verify Dashboard Stats
            page.wait_for_url("**/dashboard")
            # Check if a stat card has opacity 1
            stat_opacity = page.evaluate("document.querySelector('.stat-card .bottom-text').style.opacity")
            # Wait, the style attribute might be empty if set by CSS class.
            # Let's check computed style.
            opacity = page.evaluate("window.getComputedStyle(document.querySelector('.stat-card .bottom-text')).opacity")
            if opacity == '1':
                print("Success: Dashboard stat cards are visible.")
            else:
                print(f"Failure: Dashboard stat cards opacity is {opacity}")

            # 3. Verify Courses Responsive View
            page.goto("http://localhost:5000/courses")
            # Check for a card element (mobile view)
            if page.locator(".card.mb-3").count() > 0:
                 print("Success: Courses mobile view (cards) is active.")
            else:
                 # Might be empty, let's assuming seed data exists or just check if table is hidden
                 if page.locator(".table-responsive.d-none.d-md-block").is_visible() == False:
                     print("Success: Desktop table is hidden on mobile.")

            # 4. Verify Collective Report UI
            page.goto("http://localhost:5000/collective_report")
            # Check that textarea is GONE and "Start Recording" button is present
            if page.locator("textarea#report_text").count() == 0:
                print("Success: Text paste area removed from Collective Report.")
            else:
                print("Failure: Text paste area still present.")

            if page.get_by_text("بدء التسجيل").is_visible():
                print("Success: 'Start Recording' button found.")

            # 5. Verify Mobile Nav Customization
            page.goto("http://localhost:5000/settings")
            # Check if checkbox exists
            if page.locator("#nav_dashboard").is_visible():
                print("Success: Mobile nav settings present.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_updates()
