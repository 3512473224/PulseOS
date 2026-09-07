import sys
sys.stdout.reconfigure(encoding='utf-8')
import urllib.request
import ssl
import json
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def http_get(url, is_json=False):
    t0 = time.time()
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
        content = resp.read()
        elapsed = round(time.time() - t0, 2)
        if is_json:
            return resp.status, json.loads(content.decode('utf-8', errors='ignore')), elapsed
        return resp.status, content.decode('utf-8', errors='ignore'), elapsed

def http_post(url):
    t0 = time.time()
    req = urllib.request.Request(url, data=b"", headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        content = resp.read()
        elapsed = round(time.time() - t0, 2)
        return resp.status, json.loads(content.decode('utf-8', errors='ignore')), elapsed

print("==================================================")
print("1. VERIFYING WEB PAGES & PROTECTED ASSETS")
print("==================================================")

status, html, el = http_get("https://ppday.site/")
print(f"GET https://ppday.site/ -> status {status}, {len(html)} bytes in {el}s")
assert "<title>PPDay</title>" in html, "Original Starfield Landing page title mismatch!"
print("  [PASS] Landing page (/index.html) is authentic Starfield Landing Page!")

status, html, el = http_get("https://ppday.site/app/")
print(f"GET https://ppday.site/app/ -> status {status}, {len(html)} bytes in {el}s")
assert "PulseOS" in html, "PulseOS App page mismatch!"
print("  [PASS] PulseOS Cloud Telemetry (/app/) is authentic!")

status, html, el = http_get("https://ppday.site/workspace.html")
print(f"GET https://ppday.site/workspace.html -> status {status}, {len(html)} bytes in {el}s")
assert "newsQuickRefreshBtn" in html and "newsRefreshBtn" in html, "Workspace buttons missing!"
print("  [PASS] Geek Workspace (/workspace.html) is authentic!")

print("\n==================================================")
print("2. VERIFYING LIVE NEWS API (INITIAL LOAD)")
print("==================================================")

status, news1, el = http_get("https://ppday.site/api/system/news", is_json=True)
print(f"GET /api/system/news -> status {status} in {el}s")
print(f"  UpdatedAt: {news1.get('updatedAt')}")
print(f"  Offset: {news1.get('offset')}")
cats = news1.get('categories', {})
print(f"  Categories present: {list(cats.keys())}")
for cat, items in cats.items():
    print(f"    - {cat}: {len(items)} items")
    assert len(items) == 5, f"Category {cat} should have 5 items, got {len(items)}"

first_ai_1 = cats['ai'][0]['title']
first_tech_1 = cats['tech'][0]['title']
first_dom_1 = cats['domestic'][0]['title']
print(f"  Batch 1 AI #1: [{cats['ai'][0]['source']}] {first_ai_1}")
print(f"  Batch 1 Tech #1: [{cats['tech'][0]['source']}] {first_tech_1}")
print(f"  Batch 1 Domestic #1: [{cats['domestic'][0]['source']}] {first_dom_1}")

print("\n==================================================")
print("3. VERIFYING DYNAMIC ROTATION (CLICK 实时刷新)")
print("==================================================")

status, news2, el = http_get(f"https://ppday.site/api/system/news?force=false&rotate=true&_t={int(time.time()*1000)}", is_json=True)
print(f"GET /api/system/news?rotate=true -> status {status} in {el}s")
cats2 = news2.get('categories', {})
first_ai_2 = cats2['ai'][0]['title']
first_tech_2 = cats2['tech'][0]['title']
first_dom_2 = cats2['domestic'][0]['title']
print(f"  Batch 2 AI #1: [{cats2['ai'][0]['source']}] {first_ai_2}")
print(f"  Batch 2 Tech #1: [{cats2['tech'][0]['source']}] {first_tech_2}")
print(f"  Batch 2 Domestic #1: [{cats2['domestic'][0]['source']}] {first_dom_2}")

# Verify that articles ACTUALLY ROTATED and changed
assert first_ai_1 != first_ai_2 or first_tech_1 != first_tech_2 or first_dom_1 != first_dom_2, "Rotation failed to produce different articles!"
print("  [PASS] Dynamic rotation verified: consecutive refreshes produce DIFFERENT articles!")

print("\n==================================================")
print("4. VERIFYING AI DEEP RESEARCH (CLICK AI 深度重研)")
print("==================================================")

status, news_ai, el = http_post(f"https://ppday.site/api/system/news/refresh?_t={int(time.time()*1000)}")
print(f"POST /api/system/news/refresh -> status {status} in {el}s")
print(f"  Message: {news_ai.get('message')}")
print(f"  UpdatedAt: {news_ai.get('updatedAt')}")
print(f"  Is AI Synthesized: {news_ai.get('is_ai_synthesized')}")
cats_ai = news_ai.get('categories', {})
print(f"  AI Deep Research categories: {list(cats_ai.keys())}")
for cat, items in cats_ai.items():
    print(f"    - {cat}: {len(items)} items")

print("\n==================================================")
print("5. VERIFYING REAL URL ACCESSIBILITY ACROSS SAMPLES")
print("==================================================")

sample_urls = []
for cat, items in cats_ai.items():
    for it in items[:2]:
        sample_urls.append((cat, it['source'], it['title'][:30], it['url']))

tested = 0
passed = 0
for cat, src, title, url in sample_urls:
    tested += 1
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            print(f"  [{r.status}] [{src}] {title} -> {url[:60]}")
            if r.status in [200, 301, 302]:
                passed += 1
    except Exception as e:
        print(f"  [ERROR {e}] [{src}] {title} -> {url[:60]}")

print(f"\nURL Accessibility test: {passed}/{tested} URLs reachable!")
assert passed >= tested - 1, "Too many unreachable URLs!"
print("All verifications completed successfully!")
