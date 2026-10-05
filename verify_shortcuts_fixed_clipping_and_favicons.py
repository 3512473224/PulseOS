import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def run_verification():
    workspace_path = os.path.abspath('workspace.html')
    file_url = f"file:///{workspace_path.replace(os.sep, '/')}"
    print(f"Loading {file_url}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--disable-web-security", "--allow-file-access-from-files"]
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.goto(file_url, wait_until="networkidle", timeout=30000)
        time.sleep(1.5)

        # Clear localStorage custom shortcuts to trigger clean v3 dynamic web favicon crawler
        page.evaluate("""() => {
            localStorage.removeItem('pulseos_custom_shortcuts_v2');
            localStorage.removeItem('pulseos_custom_shortcuts_v3');
            const pwdInput = document.getElementById('sonomaPasswordInput');
            if (pwdInput) {
                pwdInput.value = 'zxcvbnm2016';
                const form = document.querySelector('.sonoma-unlock-form');
                if (form) {
                    const submitEvt = new Event('submit', { cancelable: true, bubbles: true });
                    form.dispatchEvent(submitEvt);
                }
            }
        }""")
        time.sleep(1.5)

        page.evaluate("""() => {
            document.documentElement.classList.add('pulseos-pre-auth');
            document.documentElement.classList.remove('pulseos-unlocking');
            const overlay = document.getElementById('pulseosLoginOverlay');
            if (overlay) overlay.style.display = 'none';
            const appLayout = document.querySelector('.app-layout');
            if (appLayout) appLayout.removeAttribute('style');
            if (typeof bootFullWorkspaceSystem === 'function') {
                bootFullWorkspaceSystem();
            }
            if (typeof switchView === 'function') {
                switchView('home');
            }
            if (typeof initShortcutsSystem === 'function') {
                initShortcutsSystem();
            }
        }""")
        time.sleep(2)

        # 1. Switch to Light Mode (matching user's screenshot media_1791184229510.png)
        print("\n--- 1. Testing Light Theme (Matching User Screenshot) ---")
        page.evaluate("""() => {
            document.documentElement.classList.add('theme-light');
            document.documentElement.classList.remove('theme-dark');
        }""")
        time.sleep(1)

        # Wait for images to load from network
        time.sleep(2.5)

        card = page.wait_for_selector("#homeShortcutsCard", timeout=5000)
        assert card is not None, "Shortcuts card not found!"

        # Check pills and favicons
        img_count = page.evaluate("document.querySelectorAll('#homeShortcutsGrid .sc-favicon-img').length")
        print(f"Number of shortcuts with dynamic web favicon <img>: {img_count}")
        assert img_count == 10, f"Expected 10 favicon images, got {img_count}"

        # Capture Light Theme Resting Screenshot
        output_dir = r"C:\Users\lan\.gemini\antigravity\brain\c6058254-3b68-4b10-b857-c3aa0df5a52c"
        light_macro = os.path.join(output_dir, "shortcuts_light_macro_resting.png")
        page.locator("#homeShortcutsCard").screenshot(path=light_macro)
        print(f"Captured Light Theme Resting Macro: {light_macro}")

        # 2. Toggle Manage Mode in Light Theme (Verify NO CLIPPING / 穿模 of delete button)
        print("\n--- 2. Testing Manage Mode Delete Button in Light Theme ---")
        page.click("#scManageBtn")
        time.sleep(1)

        # Verify overflow of shortcut-pill is visible
        overflow_val = page.evaluate("window.getComputedStyle(document.querySelector('.shortcut-pill')).overflow")
        print(f"Computed overflow on .shortcut-pill: {overflow_val}")
        assert overflow_val == "visible", f"Expected overflow visible, got {overflow_val}!"

        # Check delete button bounding box on first pill
        del_btn = page.locator(".shortcut-pill:first-child .shortcut-del-btn")
        del_box = del_btn.bounding_box()
        pill_box = page.locator(".shortcut-pill:first-child").bounding_box()
        print(f"Pill Box: x={pill_box['x']:.1f}, y={pill_box['y']:.1f}, w={pill_box['width']:.1f}, h={pill_box['height']:.1f}")
        print(f"Delete Btn Box: x={del_box['x']:.1f}, y={del_box['y']:.1f}, w={del_box['width']:.1f}, h={del_box['height']:.1f}")

        # Confirm delete button size is roughly 18-20px circular
        assert 16 <= del_box['width'] <= 24, f"Delete btn width unexpected: {del_box['width']}"
        assert 16 <= del_box['height'] <= 24, f"Delete btn height unexpected: {del_box['height']}"

        # Capture Light Theme Manage Mode Screenshot (Crucial for user comparison!)
        light_manage_macro = os.path.join(output_dir, "shortcuts_light_manage_macro.png")
        page.locator("#homeShortcutsCard").screenshot(path=light_manage_macro)
        print(f"Captured Light Theme Manage Macro: {light_manage_macro}")

        # 3. Test Dark Mode Resting & Manage
        print("\n--- 3. Testing Dark Theme ---")
        page.evaluate("""() => {
            document.documentElement.classList.remove('theme-light');
            document.documentElement.classList.add('theme-dark');
        }""")
        time.sleep(1)

        dark_manage_macro = os.path.join(output_dir, "shortcuts_dark_manage_macro.png")
        page.locator("#homeShortcutsCard").screenshot(path=dark_manage_macro)
        print(f"Captured Dark Theme Manage Macro: {dark_manage_macro}")

        page.click("#scManageBtn") # Exit manage mode
        time.sleep(0.5)

        dark_macro = os.path.join(output_dir, "shortcuts_dark_macro_resting.png")
        page.locator("#homeShortcutsCard").screenshot(path=dark_macro)
        print(f"Captured Dark Theme Resting Macro: {dark_macro}")

        browser.close()
        print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_verification()
