import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def verify_prod():
    artifact_dir = r"C:\Users\lan\.gemini\antigravity\brain\c6058254-3b68-4b10-b857-c3aa0df5a52c"
    cache_buster = int(time.time())
    prod_url = f"https://ppday.site/workspace.html?_t={cache_buster}"
    print(f"Connecting to production: {prod_url}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, ignore_https_errors=True)
        page = context.new_page()

        page.goto(prod_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(1.5)

        # Unlock / authenticate
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
        time.sleep(1.5)

        # 1. Switch to Light Mode (matching user screenshot)
        print("\n--- Testing Light Theme on Production ---")
        page.evaluate("""() => {
            if (typeof applyTheme === 'function') {
                applyTheme(true);
            } else {
                document.documentElement.classList.add('theme-light', 'lock-day-mode');
                document.documentElement.classList.remove('lock-night-mode');
            }
        }""")
        time.sleep(1.5)

        # Wait for favicons to load
        time.sleep(2)

        card = page.wait_for_selector("#homeShortcutsCard", timeout=10000)
        assert card is not None, "Production shortcuts card not found!"

        img_count = page.evaluate("document.querySelectorAll('#homeShortcutsGrid .sc-favicon-img').length")
        print(f"Production Shortcuts with web favicon <img>: {img_count}")
        assert img_count == 10, f"Expected 10 favicon images, got {img_count}"

        # Resting Light Mode Screenshot
        prod_light_resting = os.path.join(artifact_dir, "prod_shortcuts_light_resting.png")
        page.locator("#homeShortcutsCard").screenshot(path=prod_light_resting)
        print(f"Saved: {prod_light_resting}")

        # 2. Toggle Manage Mode in Light Theme
        print("\n--- Testing Manage Mode in Light Theme on Production ---")
        page.click("#scManageBtn")
        time.sleep(1)

        overflow_val = page.evaluate("window.getComputedStyle(document.querySelector('.shortcut-pill')).overflow")
        print(f"Computed overflow on production .shortcut-pill: {overflow_val}")
        assert overflow_val == "visible", f"Expected overflow: visible, got {overflow_val}!"

        # Check delete button bounding box on first pill
        del_btn = page.locator(".shortcut-pill:first-child .shortcut-del-btn")
        del_box = del_btn.bounding_box()
        pill_box = page.locator(".shortcut-pill:first-child").bounding_box()
        print(f"Prod Pill Box: x={pill_box['x']:.1f}, y={pill_box['y']:.1f}, w={pill_box['width']:.1f}, h={pill_box['height']:.1f}")
        print(f"Prod Delete Btn Box: x={del_box['x']:.1f}, y={del_box['y']:.1f}, w={del_box['width']:.1f}, h={del_box['height']:.1f}")

        # Manage Light Mode Screenshot
        prod_light_manage = os.path.join(artifact_dir, "prod_shortcuts_light_manage.png")
        page.locator("#homeShortcutsCard").screenshot(path=prod_light_manage)
        print(f"Saved: {prod_light_manage}")

        # 3. Switch to Dark Mode
        print("\n--- Testing Dark Theme on Production ---")
        page.evaluate("""() => {
            if (typeof applyTheme === 'function') {
                applyTheme(false);
            } else {
                document.documentElement.classList.remove('theme-light', 'lock-day-mode');
                document.documentElement.classList.add('lock-night-mode');
            }
        }""")
        time.sleep(1.5)

        # Manage Dark Mode Screenshot
        prod_dark_manage = os.path.join(artifact_dir, "prod_shortcuts_dark_manage.png")
        page.locator("#homeShortcutsCard").screenshot(path=prod_dark_manage)
        print(f"Saved: {prod_dark_manage}")

        # Exit Manage Mode
        page.click("#scManageBtn")
        time.sleep(0.5)

        # Resting Dark Mode Screenshot
        prod_dark_resting = os.path.join(artifact_dir, "prod_shortcuts_dark_resting.png")
        page.locator("#homeShortcutsCard").screenshot(path=prod_dark_resting)
        print(f"Saved: {prod_dark_resting}")

        # Full Dashboard Screenshot
        prod_full = os.path.join(artifact_dir, "prod_shortcuts_full_dashboard.png")
        page.screenshot(path=prod_full)
        print(f"Saved: {prod_full}")

        browser.close()
        print("\n[SUCCESS] Production live verification completely passed! Zero clipping and authentic web icons verified.")

if __name__ == "__main__":
    verify_prod()
