import asyncio
from playwright.async_api import async_playwright

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

            # 1. Verify Parent Management Page
            await page.goto("http://localhost:5000/parent_management")
            await page.screenshot(path="jules-scratch/verification/01_parent_management.png")
            print("Screenshot of Parent Management page taken.")

            # 2. Verify Students Page (Card Layout)
            await page.goto("http://localhost:5000/students")
            await page.screenshot(path="jules-scratch/verification/02_students_page.png")
            print("Screenshot of Students page taken.")

            # 3. Add an announcement to ensure the card appears
            await page.goto("http://localhost:5000/add_announcement")
            await page.fill('input[name="title"]', "Test Announcement")
            await page.fill('textarea[name="content"]', "This is the content of the test announcement.")
            await page.click('button[type="submit"]')
            await page.wait_for_url("http://localhost:5000/announcements")
            print("Added a test announcement.")

            # 4. Verify Announcements Page
            await page.goto("http://localhost:5000/announcements")
            await page.wait_for_selector(".announcement-card")
            await page.screenshot(path="jules-scratch/verification/03_announcements_page.png")
            print("Screenshot of Announcements page taken.")

            # 5. Add a "Work" item to ensure the card appears
            await page.goto("http://localhost:5000/add_work")
            await page.fill('input[name="title"]', "Test Work Item")
            await page.fill('textarea[name="description"]', "This is the description of the test work item.")
            await page.click('button[type="submit"]')
            await page.wait_for_url("http://localhost:5000/manage_work")
            print("Added a test work item.")

            # 6. Verify "Our Work" Page
            await page.goto("http://localhost:5000/our_work")
            await page.wait_for_selector(".work-card")
            await page.screenshot(path="jules-scratch/verification/04_our_work_page.png")
            print("Screenshot of 'Our Work' page taken.")

        except Exception as e:
            print(f"An error occurred: {e}")
            await page.screenshot(path="jules-scratch/verification/error_screenshot.png")
        finally:
            await browser.close()

asyncio.run(main())
