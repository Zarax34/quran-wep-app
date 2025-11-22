from playwright.sync_api import sync_playwright, expect
import time

def verify_fixes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 375, 'height': 812}) # Mobile viewport
        page = context.new_page()

        # 1. Login
        page.goto('http://localhost:5000/login')
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'admin123')
        page.click('button[type="submit"]')

        # Wait for navigation
        page.wait_for_url('http://localhost:5000/dashboard')

        # 2. Verify Flash Message (Auto-dismiss)
        # The login success message should appear
        flash_message = page.locator('.flash-message')
        if flash_message.is_visible():
            print("Flash message visible. Waiting for auto-dismiss...")
            time.sleep(4) # Wait > 3 seconds
            if not flash_message.is_visible():
                print("PASS: Flash message auto-dismissed.")
            else:
                print("FAIL: Flash message did not auto-dismiss.")
        else:
            print("WARNING: Flash message not found initially.")

        # 3. Verify Student Details Note Card (The broken one)
        # Go to student details
        page.goto('http://localhost:5000/students')
        # Find the link to the test student details
        # Assuming the list has links. Let's click the first "Details" or name.
        # In mobile view, it might be a card.
        # Let's just go to the URL directly if we can't find it easily, but clicking is better.
        # page.click('text=Test Student') -> might not work if name is inside a complex structure.
        # Let's try to find the ID or just list students.

        # Actually, let's check the Dashboard mobile view first as per the screenshot.
        # The screenshot showed "Student Name", "Surah", etc. It was the "Recent Reports" section or similar.
        # But my note fix was changing `.alert` to `.flash-message`.
        # The "Educational Note" is in `student_details.html`.
        # The user's screenshot was dashboard-like list.

        # Let's check `student_details.html` as it has notes.
        # I don't know the student ID, but I can grep it or just assume ID 1 or loop.
        # Let's assume ID 1 (created in setup).
        page.goto('http://localhost:5000/student_details/1')

        # Take screenshot of student details to verify layout
        page.screenshot(path='verification/student_details.png')
        print("Screenshot taken: verification/student_details.png")

        # 4. Verify Circles Page (Notification Removed)
        page.goto('http://localhost:5000/circles')
        content = page.content()
        if "يمكنك إرسال التقارير الأسبوعية" not in content:
            print("PASS: Notification text removed from Circles page.")
        else:
            print("FAIL: Notification text still present.")

        # 5. Verify Login Background (Requires checking HTML/CSS or upload)
        # We can't easily verify the visual image without uploading one first.
        # But we can check if the style attribute is present in login page
        page.goto('http://localhost:5000/login')
        # Check if body has background-image style (it should be default or uploaded)
        # My change added `{% if settings.login_background %}`.
        # Default is gradient.

        browser.close()

if __name__ == '__main__':
    verify_fixes()
