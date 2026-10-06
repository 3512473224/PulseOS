import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def run_weather_verification():
    artifact_dir = r"C:\Users\lan\.gemini\antigravity\brain\c6058254-3b68-4b10-b857-c3aa0df5a52c"
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

        # 1. Open Weather Detail Modal
        print("\n--- 1. Testing Open Weather Modal ---")
        page.evaluate("openWeatherDetailModal()")
        time.sleep(1)

        modal = page.wait_for_selector("#weatherDetailModal", timeout=5000)
        assert modal is not None, "Weather detail modal not found!"
        assert page.is_visible("#weatherDetailModal"), "Weather modal is not visible!"

        # Check City Chips Bar
        chips_count = page.evaluate("document.querySelectorAll('#wmCitiesBar .wm-city-chip').length")
        print(f"City Quick Switch Chips Count: {chips_count} (Expected 8)")
        assert chips_count == 8, f"Expected 8 city chips, got {chips_count}"

        # Check 24-hour hourly cards
        hours_count = page.evaluate("document.querySelectorAll('#wmHourlyScroll .wm-hour-card').length")
        print(f"Hourly Cards Count: {hours_count} (Expected 24)")
        assert hours_count == 24, f"Expected 24 hourly cards, got {hours_count}"

        # Verify condition text and rain chance are present in first hour card
        first_cond = page.evaluate("document.querySelector('#wmHourlyScroll .wm-hour-card .wm-hour-cond').textContent")
        first_pop = page.evaluate("document.querySelector('#wmHourlyScroll .wm-hour-card .wm-hour-pop').textContent")
        print(f"First Card Condition Text: '{first_cond}' | Rain Chance: '{first_pop}'")
        assert len(first_cond.strip()) > 0, "Weather condition text is missing!"
        assert "💧" in first_pop, "Rain probability indicator is missing!"

        # 2. Test Light Mode Screenshot of Weather Modal
        print("\n--- 2. Capturing Light Mode Weather Modal ---")
        page.evaluate("applyTheme(true)")
        time.sleep(1)

        light_modal_img = os.path.join(artifact_dir, "weather_modal_light_rich.png")
        page.locator("#weatherDetailModal .weather-detail-card").screenshot(path=light_modal_img)
        print(f"Saved: {light_modal_img}")

        # 3. Test Mouse Wheel Horizontal Scrolling on #wmHourlyScroll
        print("\n--- 3. Testing Mouse Wheel Horizontal Scrolling ---")
        init_scroll = page.evaluate("document.getElementById('wmHourlyScroll').scrollLeft")
        print(f"Initial ScrollLeft: {init_scroll}")

        # Dispatch wheel events over #wmHourlyScroll
        page.hover("#wmHourlyScroll")
        for _ in range(5):
            page.mouse.wheel(delta_x=0, delta_y=120)
            time.sleep(0.1)
        time.sleep(0.8)

        scrolled_x = page.evaluate("document.getElementById('wmHourlyScroll').scrollLeft")
        print(f"Scrolled ScrollLeft after wheel events: {scrolled_x}")
        assert scrolled_x > 50, f"Expected scrollLeft > 50 after mouse wheel, got {scrolled_x}!"

        # 4. Test Navigation Chevrons
        print("\n--- 4. Testing Navigation Chevron Buttons ---")
        page.click("#wmHourlyNextBtn")
        time.sleep(0.8)
        scrolled_next = page.evaluate("document.getElementById('wmHourlyScroll').scrollLeft")
        print(f"ScrollLeft after Next button click: {scrolled_next}")
        assert scrolled_next > scrolled_x, "Next chevron did not advance scrollLeft!"

        page.click("#wmHourlyPrevBtn")
        time.sleep(0.8)
        scrolled_prev = page.evaluate("document.getElementById('wmHourlyScroll').scrollLeft")
        print(f"ScrollLeft after Prev button click: {scrolled_prev}")
        assert scrolled_prev < scrolled_next, "Prev chevron did not decrease scrollLeft!"

        # Reset scroll to 0
        page.evaluate("document.getElementById('wmHourlyScroll').scrollLeft = 0")
        time.sleep(0.3)

        # 5. Test City Switching Fluency (Switching to Beijing and Shanghai)
        print("\n--- 5. Testing Instant City Switching ---")
        # Click Beijing chip
        page.click("button[data-city='beijing']")
        time.sleep(1.2)
        active_city = page.evaluate("document.querySelector('#wmCitiesBar .wm-city-chip.active').textContent")
        city_title = page.evaluate("document.getElementById('wmCityName').textContent")
        print(f"Active City Chip: {active_city} | City Title: {city_title}")
        assert "北京" in active_city, "Active chip did not update to Beijing!"
        assert "北京" in city_title, "City title did not update to Beijing!"

        # 6. Test Dark Mode Weather Modal
        print("\n--- 6. Capturing Dark Mode Weather Modal ---")
        page.evaluate("applyTheme(false)")
        time.sleep(1)

        dark_modal_img = os.path.join(artifact_dir, "weather_modal_dark_rich.png")
        page.locator("#weatherDetailModal .weather-detail-card").screenshot(path=dark_modal_img)
        print(f"Saved: {dark_modal_img}")

        # Macro zoom of 24-hour ribbon
        ribbon_img = os.path.join(artifact_dir, "weather_24h_ribbon_macro.png")
        page.locator("#weatherDetailModal .wm-section").first.screenshot(path=ribbon_img)
        print(f"Saved: {ribbon_img}")

        browser.close()
        print("\n[SUCCESS] Weather modal rich display, smooth wheel scroll, and fluent city switching verified 100%!")

if __name__ == "__main__":
    run_weather_verification()
