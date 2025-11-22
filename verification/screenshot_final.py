
from playwright.sync_api import sync_playwright
import time

def screenshot_final():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 375, "height": 812})
        page = context.new_page()

        try:
            page.goto("http://localhost:5000/login")
            page.get_by_placeholder("اسم المستخدم").fill("admin")
            page.get_by_placeholder("كلمة المرور").fill("admin123")
            page.get_by_role("button", name="تسجيل الدخول").click()
            page.wait_for_url("**/dashboard")

            page.goto("http://localhost:5000/settings")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.screenshot(path="verification/mobile_nav_settings.png")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    screenshot_final()
