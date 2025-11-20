
from playwright.sync_api import sync_playwright
import time

def verify_features():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Login as Admin
        page.goto('http://localhost:5000/login')
        page.fill('input[placeholder="اسم المستخدم"]', 'admin')
        page.fill('input[placeholder="كلمة المرور"]', 'admin123')
        page.click('button[type="submit"]')
        page.wait_for_url('http://localhost:5000/dashboard')
        print("Logged in as Admin")

        # 2. Verify Add User includes 'Communication Officer'
        page.goto('http://localhost:5000/add_user')
        page.wait_for_selector('select#role')
        options = page.locator('select#role option').all_inner_texts()
        print("Role options:", options)
        if "مسؤول تواصل" in options:
             print("Communication Officer role found.")
        else:
             print("Communication Officer role NOT found.")

        # Screenshot Add User page
        page.screenshot(path='verification/add_user_page.png')

        # 3. Create a Teacher User for testing
        page.fill('input#username', 'teacher_test')
        page.fill('input#password', 'password123')
        page.fill('input#name', 'Teacher Test')
        page.select_option('select#role', 'teacher')

        # Handle circle selection if visible (it should be for teacher)
        if page.is_visible('#circle_select_container'):
            # Create a circle first? Assuming circles exist or selection is optional/handled
             pass

        page.click('button[type="submit"]')
        print("Created Teacher User")

        # 4. Create a Communication Officer for testing
        page.goto('http://localhost:5000/add_user')
        page.fill('input#username', 'comm_officer')
        page.fill('input#password', 'password123')
        page.fill('input#name', 'Communication Officer')
        page.select_option('select#role', 'communication_officer')
        page.click('button[type="submit"]')
        print("Created Communication Officer User")

        # 5. Logout
        page.goto('http://localhost:5000/logout')

        # 6. Login as Teacher
        page.goto('http://localhost:5000/login')
        page.fill('input[placeholder="اسم المستخدم"]', 'teacher_test')
        page.fill('input[placeholder="كلمة المرور"]', 'password123')
        page.click('button[type="submit"]')
        page.wait_for_url('http://localhost:5000/dashboard')
        print("Logged in as Teacher")

        # 7. Verify Teacher Sidebar is Hidden and Bottom Nav is Visible (Mobile View simulation)
        # We need to force mobile view or check responsive classes
        page.set_viewport_size({"width": 375, "height": 812}) # Mobile size
        page.reload()

        # Check sidebar visibility
        sidebar = page.locator('.sidebar')
        # We added style="display:none !important;" for teachers in base.html
        # But let's check computed style
        is_sidebar_hidden = sidebar.evaluate("element => window.getComputedStyle(element).display === 'none'")
        print(f"Sidebar hidden for teacher: {is_sidebar_hidden}")

        # Check bottom nav visibility
        bottom_nav = page.locator('.parent-bottom-nav')
        is_bottom_nav_visible = bottom_nav.is_visible()
        print(f"Bottom Nav visible for teacher: {is_bottom_nav_visible}")

        page.screenshot(path='verification/teacher_mobile_view.png')

        # 8. Verify Attendance Page restrictions
        page.goto('http://localhost:5000/attendance')
        # Circle selector should be hidden
        circle_selector_container = page.locator('div.col-md-4:has(label[for="circle_id"])')
        is_selector_hidden = circle_selector_container.evaluate("element => window.getComputedStyle(element).display === 'none'")
        print(f"Attendance Circle Selector hidden for teacher: {is_selector_hidden}")
        page.screenshot(path='verification/teacher_attendance.png')

        # 9. Verify Add Holiday (Pending status)
        page.goto('http://localhost:5000/add_holiday')
        # Just verify page loads
        page.screenshot(path='verification/teacher_add_holiday.png')

        # 10. Logout
        page.goto('http://localhost:5000/logout')

        # 11. Login as Communication Officer
        page.goto('http://localhost:5000/login')
        page.fill('input[placeholder="اسم المستخدم"]', 'comm_officer')
        page.fill('input[placeholder="كلمة المرور"]', 'password123')
        page.click('button[type="submit"]')
        print("Logged in as Communication Officer")

        # 12. Verify Reports Page (Approval buttons)
        page.goto('http://localhost:5000/reports')
        # We might not have pending reports to see buttons, but we can check if the page loads without error
        # and maybe take a screenshot
        page.screenshot(path='verification/comm_officer_reports.png')

        browser.close()

if __name__ == "__main__":
    try:
        verify_features()
        print("Verification script completed successfully.")
    except Exception as e:
        print(f"Verification failed: {e}")
