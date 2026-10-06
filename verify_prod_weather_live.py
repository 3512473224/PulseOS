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

        # Unlock and boot workspace
        page.evaluate("""() => {
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
        }""")
        time.sleep(2)

        # 1. Open Weather Detail Modal on Production
        print("\n--- 1. Testing Production Open Weather Modal ---")
        page.evaluate("openWeatherDetailModal()")
        time.sleep(1.5)

        modal = page.wait_for_selector("#weatherDetailModal", timeout=5000)
        assert modal is not None, "Production weather modal not found!"

        # Check City Chips Bar
        chips_count = page.evaluate("document.querySelectorAll('#wmCitiesBar .wm-city-chip').length")
        print(f"Prod City Chips Count: {chips_count} (Expected 8)")
        assert chips_count == 8, f"Expected 8 city chips, got {chips_count}"

        # Check 24-hour hourly cards
        hours_count = page.evaluate("document.querySelectorAll('#wmHourlyScroll .wm-hour-card').length")
        print(f"Prod Hourly Cards Count: {hours_count} (Expected 24)")
        assert hours_count == 24, f"Expected 24 hourly cards, got {hours_count}"

        # 2. Test Mouse Wheel Horizontal Scrolling on Production
        print("\n--- 2. Testing Production Mouse Wheel Horizontal Scrolling ---")
        init_scroll = page.evaluate("document.getElementById('wmHourlyScroll').scrollLeft")
        print(f"Prod Initial ScrollLeft: {init_scroll}")

        page.hover("#wmHourlyScroll")
        for _ in range(5):
            page.mouse.wheel(delta_x=0, delta_y=120)
            time.sleep(0.1)
        time.sleep(0.8)

        scrolled_x = page.evaluate("document.getElementById('wmHourlyScroll').scrollLeft")
        print(f"Prod Scrolled ScrollLeft after wheel events: {scrolled_x}")
        assert scrolled_x > 50, f"Expected scrollLeft > 50 after wheel, got {scrolled_x}!"

        # 3. Capture Production Screenshots
        print("\n--- 3. Capturing Production Screenshots ---")
        page.evaluate("applyTheme(true)")
        time.sleep(1)
        prod_light_img = os.path.join(artifact_dir, "prod_weather_modal_light.png")
        page.locator("#weatherDetailModal .weather-detail-card").screenshot(path=prod_light_img)
        print(f"Saved: {prod_light_img}")

        page.evaluate("applyTheme(false)")
        time.sleep(1)
        prod_dark_img = os.path.join(artifact_dir, "prod_weather_modal_dark.png")
        page.locator("#weatherDetailModal .weather-detail-card").screenshot(path=prod_dark_img)
        print(f"Saved: {prod_dark_img}")

        # 4. Test Production City Switching
        print("\n--- 4. Testing Production City Switch ---")
        page.click("button[data-city='shanghai']")
        time.sleep(1.5)
        active_city = page.evaluate("document.querySelector('#wmCitiesBar .wm-city-chip.active').textContent")
        city_title = page.evaluate("document.getElementById('wmCityName').textContent")
        print(f"Prod Active City: {active_city} | Title: {city_title}")
        assert "上海" in active_city, "Active chip did not update to Shanghai!"

        browser.close()
        print("\n[SUCCESS] Production live verification passed 100%!")

if __name__ == "__main__":
    verify_prod()
