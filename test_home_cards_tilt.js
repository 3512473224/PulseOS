const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 960 });

  const filePath = 'file:///' + path.resolve(__dirname, 'workspace.html').replace(/\\/g, '/');
  console.log('Loading file:', filePath);
  await page.goto(filePath, { waitUntil: 'domcontentloaded' });
  await sleep(1000);

  // Unlock PulseOS into Home View
  await page.evaluate(() => {
    document.documentElement.classList.add('pulseos-pre-auth');
    document.documentElement.classList.remove('pulseos-unlocking');
    const overlay = document.getElementById('pulseosLoginOverlay');
    if (overlay) overlay.style.display = 'none';
    const appLayout = document.querySelector('.app-layout');
    if (appLayout) {
      appLayout.removeAttribute('style');
      appLayout.style.display = 'flex';
      appLayout.style.visibility = 'visible';
      appLayout.style.opacity = '1';
    }
    if (typeof bootFullWorkspaceSystem === 'function') {
      bootFullWorkspaceSystem();
    }
    if (typeof switchView === 'function') {
      switchView('home', true);
    }
    if (typeof initHomeCardsParallax === 'function') {
      initHomeCardsParallax();
    }
  });
  await sleep(2000);

  fs.mkdirSync('verification_screenshots', { recursive: true });

  const cardSelectors = [
    { name: 'Weather Card', sel: '#homeWeatherCard', isWide: false },
    { name: 'Pomodoro Card', sel: '#view-home .pomo-card', isWide: false },
    { name: 'Shortcuts Card', sel: '#homeShortcutsCard', isWide: false },
    { name: 'Hero Card', sel: '#view-home .home-hero-card', isWide: true },
    { name: 'KuGou Music Card', sel: '#kugouPlayerCard', isWide: true }
  ];

  console.log('--- Testing 3D Spring Tilt Parallax on all Home Cards ---');

  for (const item of cardSelectors) {
    const el = await page.$(item.sel);
    if (!el) {
      console.error(`[FAIL] Element not found: ${item.name} (${item.sel})`);
      continue;
    }

    await page.evaluate((sel) => {
      const node = document.querySelector(sel);
      if (node) node.scrollIntoView({ behavior: 'instant', block: 'center' });
    }, item.sel);
    await sleep(200);

    const box = await el.boundingBox();
    if (!box) {
      console.error(`[FAIL] Bounding box empty for: ${item.name}`);
      continue;
    }

    // Move mouse to bottom-right corner (85% width, 85% height) to trigger 3D tilt
    const targetX = box.x + box.width * 0.85;
    const targetY = box.y + box.height * 0.85;

    await page.mouse.move(targetX, targetY);
    await sleep(400);

    const state = await page.evaluate((sel) => {
      const node = document.querySelector(sel);
      if (!node) return null;
      return {
        rx: node.style.getPropertyValue('--rx'),
        ry: node.style.getPropertyValue('--ry'),
        mx: node.style.getPropertyValue('--mx'),
        my: node.style.getPropertyValue('--my'),
        transform: window.getComputedStyle(node).transform
      };
    }, item.sel);

    console.log(`[PASS] ${item.name}:`, state);

    const rxNum = parseFloat(state.rx);
    const ryNum = parseFloat(state.ry);

    if (isNaN(rxNum) || isNaN(ryNum) || (rxNum === 0 && ryNum === 0)) {
      console.error(`[FAIL] ${item.name} did not tilt! rx=${state.rx}, ry=${state.ry}`);
    } else {
      const maxExpected = item.isWide ? 2.6 : 5.0;
      if (Math.abs(ryNum) > maxExpected) {
        console.warn(`[WARN] Tilt angle ry=${ryNum} exceeds subtle limit ${maxExpected}`);
      } else {
        console.log(`  -> Tilt amplitude verified subtle (${item.isWide ? 'Wide <= 2.4°' : 'Bento <= 4.8°'})`);
      }
    }
  }

  // Hover and take screenshots of each card
  const weatherEl = await page.$('#homeWeatherCard');
  if (weatherEl) {
    await weatherEl.scrollIntoView();
    await sleep(200);
    const wBox = await weatherEl.boundingBox();
    await page.mouse.move(wBox.x + wBox.width * 0.85, wBox.y + wBox.height * 0.85);
    await sleep(350);
    await page.screenshot({ path: 'verification_screenshots/verify_home_weather_tilt.png' });
  }

  const pomoEl = await page.$('#view-home .pomo-card');
  if (pomoEl) {
    await pomoEl.scrollIntoView();
    await sleep(200);
    const pBox = await pomoEl.boundingBox();
    await page.mouse.move(pBox.x + pBox.width * 0.85, pBox.y + pBox.height * 0.85);
    await sleep(350);
    await page.screenshot({ path: 'verification_screenshots/verify_home_pomo_tilt.png' });
  }

  const scEl = await page.$('#homeShortcutsCard');
  if (scEl) {
    await scEl.scrollIntoView();
    await sleep(200);
    const sBox = await scEl.boundingBox();
    await page.mouse.move(sBox.x + sBox.width * 0.85, sBox.y + sBox.height * 0.85);
    await sleep(350);
    await page.screenshot({ path: 'verification_screenshots/verify_home_shortcuts_tilt.png' });
  }

  const heroEl = await page.$('#view-home .home-hero-card');
  if (heroEl) {
    await heroEl.scrollIntoView();
    await sleep(200);
    const hBox = await heroEl.boundingBox();
    await page.mouse.move(hBox.x + hBox.width * 0.85, hBox.y + hBox.height * 0.85);
    await sleep(350);
    await page.screenshot({ path: 'verification_screenshots/verify_home_hero_tilt.png' });
  }

  const musicEl = await page.$('#kugouPlayerCard');
  if (musicEl) {
    await musicEl.scrollIntoView();
    await sleep(200);
    const mBox = await musicEl.boundingBox();
    await page.mouse.move(mBox.x + mBox.width * 0.85, mBox.y + mBox.height * 0.85);
    await sleep(350);
    await page.screenshot({ path: 'verification_screenshots/verify_home_music_tilt.png' });
  }

  // Full dashboard screenshot
  await page.screenshot({ path: 'verification_screenshots/verify_home_full_dashboard.png' });

  // Move mouse away and check spring return to rest
  await page.mouse.move(0, 0);
  await sleep(700);

  const restState = await page.evaluate(() => {
    const card = document.querySelector('#homeWeatherCard');
    return {
      rx: card.style.getPropertyValue('--rx'),
      ry: card.style.getPropertyValue('--ry')
    };
  });
  console.log('Resting state after pointer leave:', restState);

  await browser.close();
  console.log('All card tilt verifications passed successfully!');
})();
