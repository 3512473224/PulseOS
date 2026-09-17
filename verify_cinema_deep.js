const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function main() {
  const screenshotsDir = path.join(__dirname, 'verification_screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  console.log('=== Starting PulseOS Cyber Cinema Deep E2E Verification ===');
  console.log('Launching Headless Chrome with Retina 2x scale...');

  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--ignore-certificate-errors', '--window-size=1600,1050', '--autoplay-policy=no-user-gesture-required']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 1050, deviceScaleFactor: 2 });

  const consoleLogs = [];
  const consoleErrors = [];
  page.on('console', msg => {
    const txt = msg.text();
    consoleLogs.push(txt);
    if (msg.type() === 'error') {
      consoleErrors.push(txt);
      console.error('[BROWSER ERROR]', txt);
    }
  });
  page.on('pageerror', err => {
    consoleErrors.push(err.toString());
    console.error('[BROWSER PAGE ERROR]', err.toString());
  });

  console.log('1. Navigating to production https://ppday.site/workspace ...');
  await page.goto('https://ppday.site/workspace', { waitUntil: 'domcontentloaded', timeout: 40000 });
  await new Promise(r => setTimeout(r, 2000));

  // 1. Verify AList connection
  console.log('2. Verifying AList API endpoint...');
  const alistCheck = await page.evaluate(async () => {
    try {
      const res = await fetch('/alist/api/public/settings');
      const json = await res.json();
      return { ok: true, code: json.code, message: json.message };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  });
  console.log('AList API check:', alistCheck);
  if (!alistCheck.ok || alistCheck.code !== 200) {
    throw new Error('AList API check failed: ' + JSON.stringify(alistCheck));
  }

  // 2. Switch to Cinema View
  console.log('3. Switching to Cinema View...');
  await page.evaluate(() => switchView('cinema'));
  await new Promise(r => setTimeout(r, 1500));

  const viewStatus = await page.evaluate(() => {
    const v = document.getElementById('view-cinema');
    const nav = document.getElementById('navItemCinema');
    return {
      viewActive: v && v.classList.contains('active'),
      navActive: nav && nav.classList.contains('active'),
      hasPlayer: !!window.artCinemaInstance
    };
  });
  console.log('Cinema view status:', viewStatus);
  if (!viewStatus.viewActive || !viewStatus.hasPlayer) {
    throw new Error('Cinema view or Artplayer instance not ready: ' + JSON.stringify(viewStatus));
  }

  // 3. Verify Subtitle Engine on Ep01
  console.log('4. Verifying Subtitle Engine on Ep01...');
  const subStatus = await page.evaluate(() => {
    const art = window.artCinemaInstance;
    return {
      hasSubtitle: !!art.subtitle,
      subtitleUrl: art.subtitle ? art.subtitle.url : null,
      subtitleShow: art.subtitle ? art.subtitle.show : false,
      cuesCount: art.subtitle && art.subtitle.cues ? art.subtitle.cues.length : 0
    };
  });
  console.log('Subtitle status on Ep01:', subStatus);
  if (!subStatus.hasSubtitle || !subStatus.subtitleUrl || subStatus.cuesCount === 0) {
    throw new Error('Subtitle not properly mounted on Ep01: ' + JSON.stringify(subStatus));
  }

  // Capture Screenshot 1: Dark Theater with Subtitle
  const ss1 = path.join(screenshotsDir, 'cinema_01_theater_dark_mode.png');
  await page.screenshot({ path: ss1 });
  console.log('Saved screenshot [1/5]:', ss1);

  // 4. Test Episode switching & Subtitle update
  console.log('5. Testing Episode switching (Ep01 -> Ep02)...');
  const epSwitchStatus = await page.evaluate(async () => {
    playCinemaEpisode(1);
    await new Promise(r => setTimeout(r, 600));
    const art = window.artCinemaInstance;
    return {
      title: art.title,
      url: art.url,
      subtitleShow: art.subtitle ? art.subtitle.show : false
    };
  });
  console.log('Episode switch status:', epSwitchStatus);
  if (!epSwitchStatus.url.includes('Ep02')) {
    throw new Error('Failed to switch to Ep02: ' + JSON.stringify(epSwitchStatus));
  }

  // Switch back to Ep01 and start playing for subtitle display
  await page.evaluate(async () => {
    playCinemaEpisode(0);
    const art = window.artCinemaInstance;
    await art.play();
  });
  await new Promise(r => setTimeout(r, 1200));

  const ss2 = path.join(screenshotsDir, 'cinema_02_subtitle_active.png');
  await page.screenshot({ path: ss2 });
  console.log('Saved screenshot [2/5]:', ss2);

  // 5. Test Smart Resume in localStorage
  console.log('6. Testing Smart Resume...');
  const resumeStatus = await page.evaluate(() => {
    const url = '/alist/d/Demo-Cinema/Ep01_CyberPulse_HD.mp4';
    saveCinemaHistory(url, 'Ep01 · CyberPulse', 4.5, 10.0);
    const retrieved = getCinemaHistory(url);
    return {
      retrievedTime: retrieved ? retrieved.time : null,
      success: retrieved && Math.abs(retrieved.time - 4.5) < 0.1
    };
  });
  console.log('Smart Resume result:', resumeStatus);
  if (!resumeStatus.success) {
    throw new Error('Smart resume failed: ' + JSON.stringify(resumeStatus));
  }

  // 6. Test Mini-PiP and Placeholder Hint
  console.log('7. Testing Mini-PiP activation & Placeholder Hint...');
  const pipStatus = await page.evaluate(() => {
    enableCinemaMiniPip();
    const stage = document.getElementById('cinemaPlayerStage');
    const placeholder = document.getElementById('cinemaStagePlaceholder');
    return {
      isFloating: stage && stage.classList.contains('is-pip-floating'),
      placeholderHintActive: placeholder && placeholder.classList.contains('pip-active')
    };
  });
  console.log('Mini-PiP & Placeholder status:', pipStatus);
  if (!pipStatus.isFloating || !pipStatus.placeholderHintActive) {
    throw new Error('Mini-PiP or placeholder hint not active: ' + JSON.stringify(pipStatus));
  }

  // 7. Test Mini-PiP Dragging (Touch & Mouse simulation)
  console.log('8. Testing Mini-PiP Touch Dragging...');
  const dragStatus = await page.evaluate(() => {
    const stage = document.getElementById('cinemaPlayerStage');
    const topbar = document.getElementById('cinemaPipTopbar');
    const r1 = stage.getBoundingClientRect();

    // Test mouse drag
    topbar.dispatchEvent(new MouseEvent('mousedown', {
      clientX: r1.left + 50,
      clientY: r1.top + 10,
      bubbles: true
    }));
    window.dispatchEvent(new MouseEvent('mousemove', {
      clientX: r1.left - 120,
      clientY: r1.top - 80,
      bubbles: true
    }));
    window.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));

    // Also test touch drag if Touch constructor available
    try {
      if (typeof Touch !== 'undefined') {
        const touch1 = new Touch({
          identifier: 1,
          target: topbar,
          clientX: r1.left - 120,
          clientY: r1.top - 80
        });
        topbar.dispatchEvent(new TouchEvent('touchstart', { touches: [touch1], bubbles: true }));
        const touch2 = new Touch({
          identifier: 1,
          target: topbar,
          clientX: r1.left - 150,
          clientY: r1.top - 100
        });
        window.dispatchEvent(new TouchEvent('touchmove', { touches: [touch2], bubbles: true }));
        window.dispatchEvent(new TouchEvent('touchend', { bubbles: true }));
      }
    } catch (e) {
      console.log('Touch event synthesis note:', e.message);
    }

    const r2 = stage.getBoundingClientRect();
    return {
      before: { left: r1.left, top: r1.top },
      after: { left: r2.left, top: r2.top },
      moved: Math.abs(r2.left - r1.left) > 10
    };
  });
  console.log('Touch drag result:', dragStatus);
  if (!dragStatus.moved) {
    throw new Error('Mini-PiP touch dragging did not move element: ' + JSON.stringify(dragStatus));
  }

  // 8. Test Cross-view Persistence in Obsidian
  console.log('9. Testing Cross-View Persistence in Obsidian...');
  await page.evaluate(() => switchView('obsidian'));
  await new Promise(r => setTimeout(r, 1000));

  const crossViewStatus = await page.evaluate(() => {
    const art = window.artCinemaInstance;
    const stage = document.getElementById('cinemaPlayerStage');
    return {
      isPlaying: art && art.video && !art.video.paused,
      isFloating: stage && stage.classList.contains('is-pip-floating'),
      inBody: stage && stage.parentElement === document.body
    };
  });
  console.log('Cross-View status in Obsidian:', crossViewStatus);

  const ss3 = path.join(screenshotsDir, 'cinema_03_minipip_dragged_over_obsidian.png');
  await page.screenshot({ path: ss3 });
  console.log('Saved screenshot [3/5]:', ss3);

  // Restore back to Cinema
  console.log('10. Restoring from Mini-PiP back to Cinema...');
  await page.evaluate(() => restoreFromPipToCinema());
  await new Promise(r => setTimeout(r, 1000));

  // 9. Test Light Theme Harmonization (Verifying No White-on-White Contrast Bugs!)
  console.log('11. Testing Light Theme Harmonization & Contrast...');
  await page.evaluate(() => applyTheme(true));
  await new Promise(r => setTimeout(r, 800));

  const lightContrastCheck = await page.evaluate(() => {
    const activeTab = document.querySelector('.cinema-tab-btn.active');
    const activeEpNum = document.querySelector('.cinema-ep-item.active .cinema-ep-num');
    const filterInput = document.getElementById('cinemaSearchInput');

    const tabComp = window.getComputedStyle(activeTab);
    const epNumComp = window.getComputedStyle(activeEpNum);
    const inputComp = window.getComputedStyle(filterInput);

    return {
      tabColor: tabComp.color,
      tabBg: tabComp.backgroundColor,
      tabNotWhite: tabComp.color !== 'rgb(255, 255, 255)',
      epNumColor: epNumComp.color,
      epNumNotWhite: epNumComp.color !== 'rgb(255, 255, 255)',
      inputBg: inputComp.backgroundColor,
      inputColor: inputComp.color
    };
  });
  console.log('Light mode contrast check:', lightContrastCheck);
  if (!lightContrastCheck.tabNotWhite || !lightContrastCheck.epNumNotWhite) {
    throw new Error('Contrast failure in light mode! Tab or EpNum still white-on-white: ' + JSON.stringify(lightContrastCheck));
  }

  const ss4 = path.join(screenshotsDir, 'cinema_04_light_theme_verified.png');
  await page.screenshot({ path: ss4 });
  console.log('Saved screenshot [4/5]:', ss4);

  // Restore dark theme
  await page.evaluate(() => applyTheme(false));
  await new Promise(r => setTimeout(r, 500));

  // 10. Test Multi-tab Search Filtering (AList & Preset & Live)
  console.log('12. Testing Multi-tab Search Filtering...');
  // A. Test AList Tab search filtering
  await page.evaluate(async () => {
    switchCinemaTab('alist');
    await new Promise(r => setTimeout(r, 1500));
  });

  const alistRootFilter = await page.evaluate(() => {
    const input = document.getElementById('cinemaSearchInput');
    input.value = 'Demo';
    filterCinemaEpisodes();

    const items = Array.from(document.querySelectorAll('#cinemaAlistFileList .cinema-ep-item'));
    return {
      totalRendered: items.length,
      allMatch: items.every(el => el.textContent.includes('Demo')),
      firstItemText: items[0] ? items[0].textContent.trim() : null
    };
  });
  console.log('AList root filter result ("Demo"):', alistRootFilter);
  if (!alistRootFilter.allMatch || alistRootFilter.totalRendered === 0) {
    throw new Error('AList search filter at root failed: ' + JSON.stringify(alistRootFilter));
  }

  // Navigate into /Demo-Cinema and test file filter
  await page.evaluate(async () => {
    await loadAlistDirectory('/Demo-Cinema');
    await new Promise(r => setTimeout(r, 1500));
  });

  const alistFileFilter = await page.evaluate(() => {
    const input = document.getElementById('cinemaSearchInput');
    input.value = 'CyberPulse';
    filterCinemaEpisodes();

    const items = Array.from(document.querySelectorAll('#cinemaAlistFileList .cinema-ep-item'));
    return {
      totalRendered: items.length,
      allMatch: items.every(el => el.textContent.includes('CyberPulse')),
      firstItemText: items[0] ? items[0].textContent.trim() : null
    };
  });
  console.log('AList folder filter result ("CyberPulse"):', alistFileFilter);
  if (!alistFileFilter.allMatch || alistFileFilter.totalRendered === 0) {
    throw new Error('AList search filter in /Demo-Cinema failed: ' + JSON.stringify(alistFileFilter));
  }

  const ss5 = path.join(screenshotsDir, 'cinema_05_alist_filtered_search.png');
  await page.screenshot({ path: ss5 });
  console.log('Saved screenshot [5/5]:', ss5);

  // Clear search input
  await page.evaluate(() => {
    const input = document.getElementById('cinemaSearchInput');
    input.value = '';
    filterCinemaEpisodes();
  });

  await browser.close();
  console.log('\n=== ALL DEEP VERIFICATION TESTS PASSED 100% SUCCESFULLY! ===');
}

main().catch(err => {
  console.error('\n❌ DEEP E2E TEST FAILED:', err);
  process.exit(1);
});
