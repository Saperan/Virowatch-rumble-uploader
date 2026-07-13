from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time, sys, os, re

# ============================================================
#  CONFIGURATION
# ============================================================
CONFIG = {
    "debug_port": 8989,
    "output_file": os.path.join(os.path.dirname(os.path.abspath(__file__)), "embed_urls.txt"),
    "items_per_page": 25,
}

def js_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    time.sleep(0.35)
    driver.execute_script("arguments[0].click();", element)

# ============================================================
#  CONNECT TO CHROME
# ============================================================
print("=" * 60)
print("  RUMBLE EMBED GRABBER")
print("=" * 60)

opt = Options()
opt.add_experimental_option("debuggerAddress", f"localhost:{CONFIG['debug_port']}")

try:
    driver = webdriver.Chrome(options=opt)
    print(f"✓ Connected to Chrome! (tab: {driver.title!r})")
except Exception as e:
    print(f"✗ Could not connect to Chrome: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

# ============================================================
#  ASK HOW MANY VIDEOS
# ============================================================
# ============================================================
#  DETERMINE HOW MANY VIDEOS TO GRAB
#  Auto-read from uploader's count file if available and > 0
# ============================================================
count_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_upload_count")
total_to_grab = 0
auto_detected = False

try:
    with open(count_file, "r") as f:
        saved = int(f.read().strip())
    if saved > 0:
        total_to_grab = saved
        auto_detected = True
        print(f"✓ Auto-detected {total_to_grab} video(s) from last upload run.")
    else:
        print("  Upload count from last run was 0 — switching to manual input.")
except Exception:
    print("  No upload count file found — switching to manual input.")

if not auto_detected:
    print()
    while True:
        try:
            raw = input("How many videos do you want to grab embed URLs for? > ").strip()
            total_to_grab = int(raw)
            if total_to_grab < 1:
                raise ValueError
            break
        except ValueError:
            print("  ⚠️  Please enter a valid positive number.")

# Reset count file to 0 so it doesn't auto-trigger on next run accidentally
try:
    with open(count_file, "w") as f:
        f.write("0")
except Exception:
    pass

print(f"\n→ Will grab {total_to_grab} embed URL(s).\n")
time.sleep(0.5)

# ============================================================
#  NAVIGATE TO CONTENT PAGE
# ============================================================
print("Step 1: Opening https://rumble.com/account/content ...")
driver.get("https://rumble.com/account/content")
time.sleep(1)
print(f"  ✓ Loaded! Title: {driver.title!r}")

# ============================================================
#  HELPERS — selectors confirmed from your DOM screenshots
# ============================================================

def get_video_rows(driver, timeout=20):
    """
    Each video is a  div.info-video  block.
    Confirmed: id="8_438196744_76perk_item" class="info-video"  (screenshot 5)
    """
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.info-video'))
    )
    rows = driver.find_elements(By.CSS_SELECTOR, 'div.info-video')
    print(f"  ✓ Found {len(rows)} video rows.")
    return rows


def open_three_dots(driver, row):
    """
    Three-dots button:  a.activate-dd.open-menu  (screenshot 1)
    It lives inside  div.my-videos-nav  →  div.sub-footer.
    """
    selectors = [
        (By.CSS_SELECTOR, 'a.activate-dd.open-menu'),
        (By.CSS_SELECTOR, 'a.activate-dd'),
        (By.CSS_SELECTOR, 'a.open-menu'),
        (By.CSS_SELECTOR, '.my-videos-nav a'),
        (By.CSS_SELECTOR, '.sub-footer a'),
    ]
    for by, sel in selectors:
        try:
            btn = row.find_element(by, sel)
            js_click(driver, btn)
            time.sleep(0.5)
            print(f"    ✓ Dropdown opened ({sel}).")
            return True
        except Exception:
            continue
    print("    ✗ Three-dots button not found.")
    return False


def click_embed(driver):
    """
    Embed link:  <a href="#" id="embed" class="action">Embed</a>
    Inside  div.dd-menu  (screenshot 2).

    IMPORTANT: Every row has an <a id="embed"> so we MUST scope the search
    to the dd-menu that is currently VISIBLE (style="display: block;").
    Searching the whole page always finds the first row's link regardless
    of which dropdown is open.
    """
    # Strategy 1: find the open dd-menu (display:block) and click embed inside it
    try:
        open_menu = WebDriverWait(driver, 6).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//div[contains(@class,"dd-menu") and contains(@style,"display: block")]')
            )
        )
        embed_link = open_menu.find_element(By.XPATH, './/a[@id="embed"]')
        js_click(driver, embed_link)
        print("    ✓ Clicked Embed (open dd-menu → a#embed).")
        return True
    except Exception as e:
        print(f"    → Strategy 1 failed: {e}")

    # Strategy 2: same but looser style check (handles "display:block" without space)
    try:
        open_menus = driver.find_elements(By.CSS_SELECTOR, 'div.dd-menu')
        for menu in open_menus:
            style = menu.get_attribute('style') or ''
            if 'display: none' in style or 'display:none' in style:
                continue  # skip hidden menus
            # This menu is visible
            try:
                embed_link = menu.find_element(By.XPATH, './/a[@id="embed"]')
                js_click(driver, embed_link)
                print("    ✓ Clicked Embed (visible dd-menu scan).")
                return True
            except Exception:
                continue
    except Exception as e:
        print(f"    → Strategy 2 failed: {e}")

    # Strategy 3: use JS to find the embed link inside the visible menu
    try:
        embed_link = driver.execute_script("""
            var menus = document.querySelectorAll('div.dd-menu');
            for (var m of menus) {
                var s = m.style.display || window.getComputedStyle(m).display;
                if (s === 'none') continue;
                var a = m.querySelector('a#embed');
                if (a) return a;
            }
            return null;
        """)
        if embed_link:
            js_click(driver, embed_link)
            print("    ✓ Clicked Embed (JS visible menu scan).")
            return True
    except Exception as e:
        print(f"    → Strategy 3 failed: {e}")

    print("    ✗ Embed option not found in any visible dropdown.")
    return False


def get_embed_url(driver):
    """
    Overlay structure (screenshot 3):
      <h3 class="media-overlay-heading">Embed IFRAME URL</h3>
      <input readonly data-code="https://rumble.com/embed/v76pyxc/?pub=4p3ufg"
             data-code-with-start-time="..." class="copy-paste">

    We read the  data-code  attribute — that's the bare embed URL.
    """
    time.sleep(2.5)  # let overlay animate in

    # Strategy 1: input right after the "Embed IFRAME URL" heading
    try:
        inp = driver.find_element(
            By.XPATH,
            '//h3[contains(text(),"Embed IFRAME URL")]/following-sibling::input[@data-code][1]'
        )
        url = inp.get_attribute('data-code')
        if url:
            return url.strip()
    except Exception:
        pass

    # Strategy 2: any input[data-code] whose value is a rumble embed URL
    try:
        for inp in driver.find_elements(By.CSS_SELECTOR, 'input[data-code]'):
            val = inp.get_attribute('data-code') or ''
            if 'rumble.com/embed' in val:
                return val.strip()
    except Exception:
        pass

    # Strategy 3: input.copy-paste
    try:
        for inp in driver.find_elements(By.CSS_SELECTOR, 'input.copy-paste'):
            val = inp.get_attribute('data-code') or ''
            if 'embed' in val.lower():
                return val.strip()
    except Exception:
        pass

    # Strategy 4: brute-force all inputs
    try:
        for inp in driver.find_elements(By.TAG_NAME, 'input'):
            for attr in ('data-code', 'value', 'data-code-with-start-time'):
                val = inp.get_attribute(attr) or ''
                if 'rumble.com/embed' in val:
                    return val.strip()
    except Exception:
        pass

    return None


def close_overlay(driver):
    """
    Close button:  button.overlay-close  (screenshot 4)
    Shows an × symbol inside the overlay heading.
    """
    selectors = [
        (By.CSS_SELECTOR, 'button.overlay-close'),
        (By.CSS_SELECTOR, '.overlay-close'),
        (By.XPATH, '//button[contains(@class,"overlay-close")]'),
    ]
    for by, sel in selectors:
        try:
            el = driver.find_element(by, sel)
            js_click(driver, el)
            time.sleep(0.4)
            print("    ✓ Overlay closed.")
            return
        except Exception:
            continue
    # Fallback: Escape
    try:
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(0.4)
        print("    ✓ Overlay closed (ESC).")
    except Exception:
        pass


def go_next_page(driver, page_num):
    """
    Click the Next button that Rumble renders on the page.
    The actual href looks like /account/content?page=2&pg=2 — two params —
    so building the URL manually always breaks. We just click what's there.

    Confirmed selectors (screenshots):
      a[rel="next"]              — rel="next" on the page-2 link
      a.icon-chevron-right       — the > arrow button
      a containing text "2","3"  — numbered page links
    """
    next_page = page_num + 1

    # Strategy 1: click the link whose href contains the next page number
    # Rumble uses  ?page=N&pg=N  — match either param format
    try:
        candidates = driver.find_elements(
            By.XPATH,
            f'//div[contains(@class,"pagination")]//a[contains(@href,"page={next_page}")]'
        )
        for a in candidates:
            href = a.get_attribute('href') or ''
            if f'page={next_page}' in href:
                print(f"  → Clicking next-page link: {href}")
                js_click(driver, a)
                time.sleep(0.75)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(0.25)
                return True
    except Exception as e:
        print(f"  → Strategy 1 failed: {e}")

    # Strategy 2: click the rel="next" anchor
    try:
        a = driver.find_element(By.CSS_SELECTOR, 'a[rel="next"]')
        href = a.get_attribute('href') or ''
        print(f"  → Clicking rel=next: {href}")
        js_click(driver, a)
        time.sleep(0.75)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.25)
        return True
    except Exception as e:
        print(f"  → Strategy 2 failed: {e}")

    # Strategy 3: click the chevron-right / Next arrow button
    try:
        a = driver.find_element(By.CSS_SELECTOR, 'a.icon-chevron-right')
        href = a.get_attribute('href') or ''
        print(f"  → Clicking chevron-right: {href}")
        js_click(driver, a)
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.25)
        return True
    except Exception as e:
        print(f"  → Strategy 3 failed: {e}")

    print(f"  ✗ Could not find next page link. Stopping.")
    return False

# ============================================================
#  MAIN LOOP
# ============================================================
embed_urls   = []
grabbed      = 0
current_page = 1

print(f"\nStep 2: Starting embed URL grab (target: {total_to_grab} video(s))...")

while grabbed < total_to_grab:
    remaining = total_to_grab - grabbed
    print(f"\n--- Page {current_page} | Grabbed: {grabbed} | Remaining: {remaining} ---")

    try:
        rows = get_video_rows(driver)
    except Exception as e:
        print(f"✗ Could not load video rows: {e}")
        break

    to_do = min(remaining, len(rows), CONFIG["items_per_page"])
    print(f"  → Processing {to_do} row(s) on this page.\n")

    for i in range(to_do):
        video_num = grabbed + 1
        print(f"  [{video_num}/{total_to_grab}] Row {i + 1}...")

        # Re-fetch rows each time — DOM gets stale after overlay interactions
        try:
            rows = get_video_rows(driver)
        except Exception as e:
            print(f"    ✗ Row refresh failed: {e}")
            break

        if i >= len(rows):
            print(f"    ✗ Row {i} out of range ({len(rows)} available). Stopping.")
            break

        row = rows[i]

        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", row)
            time.sleep(0.2)
        except Exception:
            pass

        # 1. Open ⋮ dropdown
        if not open_three_dots(driver, row):
            embed_urls.append("ERROR_NO_DROPDOWN")
            grabbed += 1
            continue

        # 2. Click Embed
        if not click_embed(driver):
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            except Exception:
                pass
            embed_urls.append("ERROR_NO_EMBED_LINK")
            grabbed += 1
            continue

        # 3. Read the iframe src from the overlay
        url = get_embed_url(driver)
        if url:
            print(f"    ✓ {url}")
            embed_urls.append(url)
        else:
            print(f"    ✗ Could not extract embed URL.")
            embed_urls.append("ERROR_URL_NOT_FOUND")

        # 4. Close overlay
        close_overlay(driver)
        time.sleep(0.4)

        grabbed += 1

    # Paginate if needed
    if grabbed < total_to_grab:
        if len(rows) < CONFIG["items_per_page"]:
            print("\n  ⚠️  Last page reached before hitting target. Stopping.")
            break
        if not go_next_page(driver, current_page):
            break
        current_page += 1
    else:
        break

# ============================================================
#  FORMAT AND SAVE
# ============================================================
print("\n" + "=" * 60)
print(f"  DONE! Collected {len(embed_urls)} URL(s).")
print("=" * 60)

url_lines = [f"  '{u}'" for u in reversed(embed_urls)]
output_block = "video: [\n" + ",\n".join(url_lines) + "\n]"

print("\n📋 Result:\n")
print(output_block)

try:
    with open(CONFIG["output_file"], "w", encoding="utf-8") as f:
        f.write(output_block + "\n")
    print(f"\n✓ Saved to: {CONFIG['output_file']}")
except Exception as e:
    print(f"\n⚠️  Could not save: {e}")

print()
input("Press Enter to exit...")