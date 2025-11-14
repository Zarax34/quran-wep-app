
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            # Go to the login page
            await page.goto("http://127.0.0.1:5000/login")

            # Fill in the login form
            await page.fill('input[name="username"]', "v_parent")
            await page.fill('input[name="password"]', "v_parent_pass")

            # Click the login button
            await page.click('button[type="submit"]')

            # Wait for navigation to the dashboard
            await page.wait_for_url("http://127.0.0.1:5000/parent_dashboard")

            # Verify the dashboard is loaded by checking for a known element
            dashboard_header = await page.locator('h1:has-text("لوحة تحكم ولي الأمر")').is_visible()
            if not dashboard_header:
                raise Exception("Parent dashboard did not load correctly.")

            print("Successfully logged in and loaded parent dashboard.")

            # Navigate to the new settings page
            await page.goto("http://127.0.0.1:5000/parent_settings")

            # Verify the settings page loaded
            settings_header = await page.locator('h1:has-text("إعدادات الحساب")').is_visible()
            if not settings_header:
                raise Exception("Parent settings page did not load correctly.")

            print("Successfully navigated to parent settings page.")

            # Take a screenshot
            await page.screenshot(path="verify_parent_settings_fix.png")
            print("Screenshot taken.")

        except Exception as e:
            print(f"An error occurred: {e}")
            await page.screenshot(path="error_verify_parent_settings_fix.png")
        finally:
            await browser.close()

asyncio.run(main())
