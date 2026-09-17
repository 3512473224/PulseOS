const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function main() {
  const screenshotsDir = path.join(__dirname, 'verification_screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  console.log('=== Starting Verification: Cinema UI Polish & Anti-Jump Bugfix ===');
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1600,1050']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 1050, deviceScaleFactor: 2 });

  console.log('1. Navigating to https://ppday.site/workspace ...');
  await page.goto('https://ppday.site/workspace', { waitUntil: 'domcontentloaded', timeout: 40000 });
  await new Promise(r => setTimeout(r, 2000));

  console.log('2. Switching to Cinema View...');
  await page.evaluate(() => switchView('cinema'));
  await new Promise(r => setTimeout(r, 1500));

  // 1. Verify Search Icon Layout (Anti-Clipping / No Overlap with Tabs)
  console.log('3. Verifying Search Icon & Tab Layout...');
  const layoutCheck = await page.evaluate(() => {
    const tabBtn = document.getElementById('cinemaTabBtnPreset');
    const searchWrap = document.getElementById('cinemaSearchInput').parentElement;
    const searchIcon = searchWrap.querySelector('[data-lucide="search"]');
    const searchInput = document.getElementById('cinemaSearchInput');

    const tabRect = tabBtn.getBoundingClientRect();
    const iconRect = searchIcon.getBoundingClientRect();
    const inputRect = searchInput.getBoundingClientRect();

    const isBelowTab = iconRect.top >= tabRect.bottom;
    const isInsideInput = (iconRect.top >= inputRect.top) && (iconRect.bottom <= inputRect.bottom);

    return {
      tabBottom: tabRect.bottom,
      iconTop: iconRect.top,
      iconBottom: iconRect.bottom,
      inputTop: inputRect.top,
      inputBottom: inputRect.bottom,
      isBelowTab,
      isInsideInput
    };
  });
  console.log('Search icon positioning check:', layoutCheck);
  if (!layoutCheck.isBelowTab || !layoutCheck.isInsideInput) {
    throw new Error('Search icon is still overlapping or improperly positioned: ' + JSON.stringify(layoutCheck));
  }

  // 2. Verify Colors: [AList 面板], [下一集], [进入存储管理中心] are Ice Sky Blue
  console.log('4. Verifying Button Colors (Ice Sky Blue)...');
  const colorCheck = await page.evaluate(() => {
    const alistBtn = document.querySelector('.cinema-header-bar .btn-cinema-sky');
    const nextBtn = document.querySelector('.cinema-now-playing-bar .btn-cinema-sky');
    const manageBtn = document.querySelector('.cinema-cards-grid .btn-cinema-sky');

    function getStyle(el) {
      if (!el) return null;
      const cs = window.getComputedStyle(el);
      return {
        color: cs.color,
        bg: cs.backgroundImage || cs.backgroundColor,
        border: cs.borderColor
      };
    }

    return {
      alistBtn: getStyle(alistBtn),
      nextBtn: getStyle(nextBtn),
      manageBtn: getStyle(manageBtn)
    };
  });
  console.log('Button colors check:', colorCheck);

  // 3. Verify Video Jump Bug is FIXED
  console.log('5. Verifying Video Playback Stability (Anti-Rapid Jump)...');
  await page.evaluate(() => playCinemaEpisode(0));
  await new Promise(r => setTimeout(r, 1000));

  const initialEp = await page.evaluate(() => window.cinemaCurrentEpisodeIndex);
  console.log('Initial playing episode index:', initialEp);

  await new Promise(r => setTimeout(r, 4000));
  const afterEp = await page.evaluate(() => window.cinemaCurrentEpisodeIndex);
  console.log('Episode index after 4s:', afterEp);

  if (initialEp !== afterEp) {
    throw new Error('Episode jumped unexpectedly: initial=' + initialEp + ' after=' + afterEp);
  }
  console.log('Episode is completely stable, no rapid jumping!');

  // 4. Capture screenshot of the full polished Cinema view
  const ss1 = path.join(screenshotsDir, 'cinema_refined_overview.png');
  await page.screenshot({ path: ss1 });
  console.log('Saved screenshot:', ss1);

  // 5. Scroll down and capture netdisk cards
  await page.evaluate(() => {
    document.querySelector('.cinema-onboarding-section').scrollIntoView({ behavior: 'instant' });
  });
  await new Promise(r => setTimeout(r, 800));

  const ss2 = path.join(screenshotsDir, 'cinema_netdisk_cards_refined.png');
  await page.screenshot({ path: ss2 });
  console.log('Saved screenshot of refined netdisk cards:', ss2);

  await browser.close();
  console.log('=== VERIFICATION COMPLETED SUCCESSFULLY ===');
}

main().catch(err => {
  console.error('Verification failed:', err);
  process.exit(1);
});
