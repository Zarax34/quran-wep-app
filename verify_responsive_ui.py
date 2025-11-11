import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Create a directory for screenshots if it doesn't exist
        os.makedirs('verification_screenshots', exist_ok=True)

        # Login as a parent
        await page.goto('http://localhost:5000/login')
        await page.fill('input[name="username"]', 'test_parent')
        await page.fill('input[name="password"]', 'test_password')
        await page.click('button[type="submit"]')
        await page.wait_for_url('http://localhost:5000/parent_dashboard')

        # Desktop view screenshot
        await page.set_viewport_size({'width': 1280, 'height': 800})
        await page.screenshot(path='verification_screenshots/parent_desktop_view.png')

        # Mobile view screenshot
        await page.set_viewport_size({'width': 375, 'height': 667})
        await page.screenshot(path='verification_screenshots/parent_mobile_view.png')

        # Check for notification count
        notification_count = await page.locator('.notification-badge').text_content()
        print(f"Notification count: {notification_count}")

        await browser.close()

# Helper script to create a test parent user
async def create_test_user():
    from app import app, db, User, Parent
    from werkzeug.security import generate_password_hash

    with app.app_context():
        # Check if user already exists
        if User.query.filter_by(username='test_parent').first():
            print("Test parent user already exists.")
            return

        # Create user
        user = User(
            username='test_parent',
            password=generate_password_hash('test_password'),
            name='Test Parent',
            role='parent'
        )
        db.session.add(user)
        db.session.commit()

        # Create parent
        parent = Parent(
            name='Test Parent',
            phone='777123456',
            user_id=user.id
        )
        db.session.add(parent)
        db.session.commit()
        print("Test parent user created successfully.")

if __name__ == '__main__':
    # Create the test user first
    import asyncio
    asyncio.run(create_test_user())
    # Then run the verification script
    asyncio.run(main())
