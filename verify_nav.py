import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={'width': 375, 'height': 812},
            is_mobile=True,
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1'
        )
        page = await context.new_page()

        try:
            # Login
            await page.goto("http://127.0.0.1:5000/login", timeout=60000)
            await page.fill('input[name="username"]', "parent_test")
            await page.fill('input[name="password"]', "password")
            await page.click('button[type="submit"]')
            await page.wait_for_url("http://127.0.0.1:5000/parent_dashboard", timeout=60000)

            # Take screenshot of the bottom navigation bar
            nav_element = await page.query_selector('.parent-bottom-nav')
            if nav_element:
                await nav_element.screenshot(path="bottom_nav_screenshot_new.png")
                print("Screenshot saved as bottom_nav_screenshot_new.png")
            else:
                print("Bottom navigation bar not found.")

        except Exception as e:
            print(f"An error occurred: {e}")
            await page.screenshot(path='error_screenshot.png')
            print("Error screenshot saved as error_screenshot.png")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
