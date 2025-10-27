import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            # Login
            await page.goto("http://localhost:5000/login")
            await page.fill('input[name="username"]', "admin")
            await page.fill('input[name="password"]', "admin123")
            await page.click('button[type="submit"]')
            await page.wait_for_url("http://localhost:5000/dashboard")
            print("Login successful.")

            # Navigate to add report page
            await page.goto("http://localhost:5000/add_report")
            print("Navigated to add_report page.")

            # Select a student
            await page.select_option('select[name="student_id"]', index=1)
            print("Selected a student.")

            # Select a Surah and wait for dependent dropdown to populate
            await page.select_option('select[name="surah"]', "البقرة")
            await page.wait_for_timeout(1000)  # Wait for API call
            print("Selected Surah 'البقرة'.")

            # Verify verse dropdown
            verse_count = await page.locator('select[name="to_verse"] > option').count()
            print(f"Verse dropdown count: {verse_count}")
            if verse_count != 287: # "البقرة" has 286 verses + 1 placeholder
                raise Exception(f"Verse dropdown count is incorrect. Expected 287, got {verse_count}")
            print("Verse dropdown populated correctly.")

            # Select a verse and verify page number
            await page.select_option('select[name="from_verse"]', "10")
            await page.wait_for_timeout(1000) # Wait for API call
            page_number = await page.input_value('input[name="page_number"]')
            print(f"Page number for verse 10: {page_number}")
            if page_number != "3":
                raise Exception(f"Page number is incorrect. Expected 3, got {page_number}")
            print("Page number populated correctly.")

            # Take screenshot
            screenshot_path = "report_form_verification.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")

        except Exception as e:
            print(f"An error occurred: {e}")
            await page.screenshot(path="error_screenshot.png")

        finally:
            await browser.close()

asyncio.run(main())
