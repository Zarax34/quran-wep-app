
from playwright.sync_api import sync_playwright
import time

def verify_more_menu():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 375, "height": 812}) # Mobile viewport
        page = context.new_page()

        try:
            # Login as Admin
            page.goto("http://localhost:5000/login")
            page.get_by_placeholder("اسم المستخدم").fill("admin")
            page.get_by_placeholder("كلمة المرور").fill("admin123")
            page.get_by_role("button", name="تسجيل الدخول").click()

            # Wait for dashboard
            page.wait_for_url("**/dashboard")

            # Click "More" button
            page.get_by_text("المزيد").click()
            time.sleep(1) # Wait for animation

            # Verify overlay elements
            page.screenshot(path="verification/mobile_more_menu.png")
            print("Snapshot of 'More' menu overlay taken.")

            # Check for key items specifically inside the overlay
            overlay = page.locator("#mobileMenuOverlay")

            # Use specific selectors for items inside the overlay
            if overlay.get_by_text("الحلقات").is_visible() and overlay.get_by_text("الرسوم").is_visible():
                print("Success: 'Circles' and 'Fees' icons are visible in the overlay.")
            else:
                print("Failure: Missing icons in the overlay.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_more_menu()
