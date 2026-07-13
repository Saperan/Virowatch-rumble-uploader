from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, time, sys, random

def rsleep(base):
    """Sleep for base seconds + a random jitter between 0.1 and 0.8 seconds."""
    jitter = random.uniform(0.1, 0.8)
    time.sleep(base + jitter)

# --- CONFIGURATION (EDIT THESE!) ---
# --- HELPER: Extract Clean Filename from Path ---
def get_clean_filename(file_path):
    """Extract filename and sanitize it for use as a video title."""
    try:
        # Get just the filename without path
        filename = os.path.basename(file_path)
        
        # Remove common extensions (keep .mp4, .mov, etc. if needed)
        ext = os.path.splitext(filename)[1].lower()
        
        # Sanitize special characters that might break on Rumble
        safe_chars = " -_./"  # Allow spaces, hyphens, underscores, dots
        clean_name = "".join(c for c in filename.replace(ext, "") if c in safe_chars or c.isalnum())
        
        # Remove leading/trailing whitespace and normalize multiple spaces
        clean_name = " ".join(clean_name.split())
        
        # Capitalize first letter of each word (Title Case)
        words = clean_name.split()
        title_case = "".join(word.capitalize() for word in words)
        
        return title_case if title_case else CONFIG.get("video_title_default", "Video Title")
    except Exception as e:
        print(f"   ⚠️ Filename extraction error: {e}")
        return CONFIG.get("video_title_default", "Unknown Video")

# --- CONFIGURATION (EDIT THESE!) ---
CONFIG = {
    "folder_path": r"C:\Users\pc\Desktop\rumbler",  # ⚠️ YOUR VIDEO FOLDER!
    "video_title_default": "Content",  # Optional: default if filename fails
    "video_description": "",
    "video_tags": "virowatch",
    "chrome_profile": r"C:\Selenium\Chrome_Test_Profile",  # ⚠️ Ensure this folder exists!
    "debug_port": 8989,
    "chrome_path": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "upload_timeout_minutes": 30,  # Max minutes to wait for a video to finish uploading
    "auto_delete_after_upload": False,  # ⚠️ Toggle this: True=delete file, False=keep it
    "backup_folder_path": r"C:\Users\pc\Desktop\rumbler_backup",  # Where to move files if not deleting
}


# --- SETUP CHROME WITH DEBUGGING PORT (Connect to Already Running Instance) ---
print("=" * 60)
print("Step 1: Connecting to Chrome Debug Port...")
print(f"   Profile Path: {CONFIG['chrome_profile']}")
print(f"   Debug Port: {CONFIG['debug_port']}")
print(f"   Chrome Executable: {CONFIG['chrome_path']}")
print("=" * 60)

opt = Options()
opt.add_experimental_option("debuggerAddress", f"localhost:{CONFIG['debug_port']}")

try:
    print(f"   Loading Chrome options...")
    driver = webdriver.Chrome(options=opt)
    print(f"   ✓ Connected! Browser title: {driver.title}")
except Exception as e:
    print(f"   ✗ Chrome Connection Error: {e}")
    print("   Make sure Chrome is still open from the CMD command above!")
    input("Press Enter to exit...")
    exit()

print("Step 2: Loading Rumble.com...")
driver.get("https://rumble.com/")
rsleep(3)
print(f"   ✓ Loaded! Title: {driver.title}")

# --- CHECK VIDEO FOLDER ---
print("\nStep 3: Checking Video Folder...")
folder = CONFIG["folder_path"]
if not os.path.exists(folder):
    print(f"   ✗ Folder doesn't exist: {folder}")
    input("Press Enter to exit...")
    exit()

files = os.listdir(folder)
print(f"   ✓ Found {len(files)} files in folder!")
for f in files[:3]:
    print(f"      - {f}")

if not files:
    print("   ⚠️ No videos found! Add some to the folder.")
    input("Press Enter to exit...")
    exit()

uploads = 0

def getFirstFile():
    folder_path = CONFIG["folder_path"]
    files = os.listdir(folder_path)
    if not files:
        print("   Folder is empty!")
        return None
    first_file = os.path.join(folder_path, files[0])
    print(f"   Found file: {files[0]}")
    return first_file

def deleteTheFile(nameOfFileAndPath):
    rsleep(2)
    
    if CONFIG.get("auto_delete_after_upload", True):  # Mode 1: Delete permanently
        print("   Deleting the movie from folder (permanent)...")
        try:
            os.remove(nameOfFileAndPath)
            print("   ✓ File deleted successfully.")
        except Exception as e:
            print(f"   ⚠️ Error deleting file: {e}")
    else:  # Mode 2: Move to backup folder (prevents infinite loop, keeps SAME name!)
        try:
            backup_folder = CONFIG.get("backup_folder_path", r"C:\Users\pc\Desktop\rumbler_backup")
            
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder, exist_ok=True)
                print(f"   → Creating backup folder: {backup_folder}")
            
            # Keep the SAME filename (no timestamp change!)
            new_path = os.path.join(backup_folder, os.path.basename(nameOfFileAndPath))
            
            print(f"   → Moving file to backup with original name...")
            os.rename(nameOfFileAndPath, new_path)
            print("   ✓ File moved to backup successfully.")
        except Exception as e:
            print(f"   ⚠️ Error moving file to backup: {e}")




def js_click(driver, element):
    """Scroll into view and click via JavaScript."""
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    rsleep(0.4)
    driver.execute_script("arguments[0].click();", element)

def click_checkbox_robustly(driver, checkbox_id):
    """
    Checks a checkbox by its ID using multiple fallback strategies.
    Returns True on success, raises Exception on total failure.
    """
    # Strategy 1: Click the checkbox directly via JS
    try:
        cb = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.ID, checkbox_id))
        )
        if not cb.is_selected():
            js_click(driver, cb)
            rsleep(1)
        if cb.is_selected():
            print(f"   ✓ Checkbox #{checkbox_id} checked (direct JS click)!")
            return True
    except Exception as e:
        print(f"   → Direct click failed for #{checkbox_id}: {e}")

    # Strategy 2: Find label by 'for' attribute and click it
    try:
        label = driver.find_element(By.XPATH, f'//label[@for="{checkbox_id}"]')
        js_click(driver, label)
        rsleep(1)
        cb = driver.find_element(By.ID, checkbox_id)
        if cb.is_selected():
            print(f"   ✓ Checkbox #{checkbox_id} checked (label[for] click)!")
            return True
    except Exception as e:
        print(f"   → label[for] click failed for #{checkbox_id}: {e}")

    # Strategy 3: Find ancestor label and click it
    try:
        cb = driver.find_element(By.ID, checkbox_id)
        label = cb.find_element(By.XPATH, './ancestor::label[1]')
        js_click(driver, label)
        rsleep(1)
        if cb.is_selected():
            print(f"   ✓ Checkbox #{checkbox_id} checked (ancestor label click)!")
            return True
    except Exception as e:
        print(f"   → ancestor label click failed for #{checkbox_id}: {e}")

    # Strategy 4: Force-check via JS property mutation
    try:
        driver.execute_script(f"""
            var cb = document.getElementById('{checkbox_id}');
            cb.checked = true;
            ['change', 'input', 'click'].forEach(function(ev) {{
                cb.dispatchEvent(new Event(ev, {{bubbles: true}}));
            }});
        """)
        rsleep(0.5)
        cb = driver.find_element(By.ID, checkbox_id)
        if cb.is_selected():
            print(f"   ✓ Checkbox #{checkbox_id} checked (JS property force)!")
            return True
        else:
            # Some custom checkbox widgets don't use the real checked property
            print(f"   → JS force applied for #{checkbox_id} (custom widget, may be OK)")
            return True  # Proceed anyway — custom widgets may look unchecked to Selenium but work
    except Exception as e:
        raise Exception(f"All strategies failed for checkbox #{checkbox_id}: {e}")

def select_unlisted(driver):
    """
    Sets the video visibility to Unlisted.
    Confirmed working: Rumble uses [data-value="unlisted"] on its custom tab UI.
    Fallbacks cover radio buttons and text-based selectors.
    """
    print("   Step 6a: Setting Visibility to Unlisted...")

    # Give the page a moment to render the visibility section
    rsleep(2)

    # Strategies in priority order — [data-value="unlisted"] confirmed working first
    strategies = [
        # 1. ✅ CONFIRMED: Rumble custom tab UI uses data-value attribute
        ('[data-value="unlisted"]', By.CSS_SELECTOR),
        # 2. Standard radio by ID
        ('visibility_unlisted', By.ID),
        # 3. Radio input with value="unlisted"
        ('input[type="radio"][value="unlisted"]', By.CSS_SELECTOR),
        # 4. Any input with value="unlisted"
        ('input[value="unlisted"]', By.CSS_SELECTOR),
        # 5. Exact text match
        ('//*[normalize-space(text())="Unlisted"]', By.XPATH),
        # 6. Partial text fallback
        ('//*[contains(text(),"Unlisted") and not(self::script)]', By.XPATH),
        # 7. Label text fallback
        ('//label[contains(.,"Unlisted")]', By.XPATH),
    ]

    for i, (selector, by) in enumerate(strategies, 1):
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((by, selector))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            rsleep(0.5)

            tag = element.tag_name.lower()
            input_type = (element.get_attribute("type") or "").lower()

            if tag == "input" and input_type == "radio":
                # Try its label first so the custom widget fires properly
                try:
                    elem_id = element.get_attribute("id")
                    label = driver.find_element(By.XPATH, f'//label[@for="{elem_id}"]')
                    js_click(driver, label)
                except:
                    js_click(driver, element)
            else:
                js_click(driver, element)

            rsleep(1.5)
            print(f"   ✓ Unlisted selected! (strategy {i}: {selector})")
            return  # Trust the click — Rumble's widget doesn't expose state reliably

        except Exception as e:
            print(f"   → Strategy {i} failed ({selector}): {e}")
            continue

    # Last resort: JS scan of all radio inputs for one with "unlisted" in value
    try:
        print("   → Attempting JS brute-force for unlisted...")
        driver.execute_script("""
            var inputs = document.querySelectorAll('input[name*="visibility"], input[name*="access"], input[type="radio"]');
            inputs.forEach(function(inp) {
                if (inp.value.toLowerCase().includes('unlisted')) {
                    inp.checked = true;
                    ['change','input','click'].forEach(function(ev) {
                        inp.dispatchEvent(new Event(ev, {bubbles:true}));
                    });
                }
            });
        """)
        rsleep(1)
        print("   ✓ JS brute-force applied for Unlisted.")
        return
    except Exception as e:
        raise Exception(f"All Unlisted strategies exhausted: {e}")

def select_personal_use(driver):
    """
    Sets the rights to 'Personal Use' using many fallback strategies.
    """
    print("   Step 8: Setting to Personal Use...")

    strategies = [
        # 1. Radio input with value containing "personal"
        lambda: driver.find_element(By.CSS_SELECTOR, 'input[value="personal"]'),
        lambda: driver.find_element(By.CSS_SELECTOR, 'input[type="radio"][value*="personal"]'),
        # 2. data-value attribute
        lambda: driver.find_element(By.CSS_SELECTOR, '[data-value="personal"]'),
        # 3. Exact text match
        lambda: driver.find_element(By.XPATH, '//*[normalize-space(text())="Personal Use"]'),
        # 4. Partial text in any element
        lambda: driver.find_element(By.XPATH, '//*[contains(text(),"Personal Use") and not(self::script)]'),
        # 5. Label containing text
        lambda: driver.find_element(By.XPATH, '//label[contains(.,"Personal Use")]'),
        # 6. Anchor tag (Rumble sometimes uses <a> tabs)
        lambda: driver.find_element(By.XPATH, '//a[contains(text(),"Personal")]'),
    ]

    rsleep(1)

    for i, strategy in enumerate(strategies, 1):
        try:
            element = strategy()
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            rsleep(0.5)

            tag = element.tag_name.lower()
            input_type = (element.get_attribute("type") or "").lower()

            if tag == "input" and input_type == "radio":
                try:
                    elem_id = element.get_attribute("id")
                    label = driver.find_element(By.XPATH, f'//label[@for="{elem_id}"]')
                    js_click(driver, label)
                except:
                    js_click(driver, element)
            else:
                js_click(driver, element)

            rsleep(1.5)
            print(f"   ✓ Personal Use selected! (strategy {i})")
            return

        except Exception as e:
            print(f"   → Strategy {i} failed: {e}")
            continue

    # Not fatal — Personal Use may be optional or already default
    print("   ⚠️ Personal Use not found — it may be optional or already the default. Continuing...")

def wait_for_upload_complete(driver, timeout_minutes=30):
    """
    Waits for the file upload to complete before clicking Submit.

    Rumble's upload page uses these specific elements (confirmed from live DOM):
      - div.progress-wrap  → the container; hidden once upload is done
      - span.green_percent → the green bar; style="width: X%;"
      - span.top_percent   → text label showing "100% (5.2MB/s - 7s)"

    We check all three plus a submit-button fallback.
    """
    print(f"   ⏳ Waiting for video upload to complete (max {timeout_minutes} min)...")
    timeout_secs = timeout_minutes * 60
    start = time.time()
    last_progress = -1

    while time.time() - start < timeout_secs:
        elapsed = int(time.time() - start)

        result = driver.execute_script("""
            // ── 1. Rumble's real progress bar: span.green_percent ──────────────────
            var greenBar = document.querySelector('span.green_percent');
            if (greenBar) {
                var w = greenBar.style.width || '';          // e.g. "73%" or "100%"
                var pct = parseFloat(w);
                if (!isNaN(pct)) {
                    return {status: 'progress', value: pct, source: 'green_percent'};
                }
            }

            // ── 2. Rumble's text label: span.top_percent ───────────────────────────
            var topLabel = document.querySelector('span.top_percent');
            if (topLabel) {
                var txt = topLabel.textContent || '';        // e.g. "100% (5.2MB/s - 7s)"
                var match = txt.match(/([\d.]+)%/);
                if (match) {
                    return {status: 'progress', value: parseFloat(match[1]), source: 'top_percent'};
                }
            }

            // ── 3. progress-wrap hidden → upload done ──────────────────────────────
            var wrap = document.querySelector('.progress-wrap');
            if (wrap) {
                var style = window.getComputedStyle(wrap);
                if (style.display === 'none' || style.visibility === 'hidden') {
                    return {status: 'done', source: 'progress-wrap hidden'};
                }
            } else {
                // No progress-wrap at all — either done or not yet started
                // Only treat as done if we're past the 10s mark
                return {status: 'no_bar'};
            }

            // ── 4. Fallback: submit button enabled ─────────────────────────────────
            var submit = document.querySelector(
                'form:last-of-type input[type="submit"]:not([disabled]), ' +
                'form:last-of-type button[type="submit"]:not([disabled])'
            );
            if (submit) {
                return {status: 'done', source: 'submit_enabled'};
            }

            return {status: 'uploading'};
        """)

        status = result.get('status', 'unknown') if result else 'unknown'
        source = result.get('source', '') if result else ''

        if status == 'progress':
            pct = result.get('value', 0)
            if pct != last_progress:
                print(f"   → Upload progress: {pct:.0f}% ({elapsed}s elapsed)  [{source}]")
                last_progress = pct
            if pct >= 100:
                print(f"   ✓ Upload reached 100%! Waiting 3s for server to process...")
                rsleep(3)
                return True

        elif status == 'done':
            print(f"   ✓ Upload complete! ({source}, {elapsed}s elapsed)")
            return True

        elif status == 'no_bar':
            # Progress wrap not in DOM yet — page may still be loading, wait a bit
            if elapsed > 15:
                # Been long enough; if there's truly no bar, assume it finished fast
                print(f"   ✓ No progress bar found after {elapsed}s — assuming upload already done.")
                return True
            else:
                print(f"   → Waiting for progress bar to appear... ({elapsed}s)")

        else:
            # status == 'uploading' — bar exists but <100%, keep waiting
            if elapsed % 15 == 0 and elapsed > 0:
                print(f"   → Still uploading... ({elapsed}s elapsed)")

        rsleep(3)

    raise Exception(f"Upload timed out after {timeout_minutes} minutes!")

def select_random_category(driver):
    """
    Opens the primary category dropdown and clicks a random valid option.
    """
    print("   Step 5: Selecting Primary Category...")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "category_primary"))
    )

    container = driver.execute_script(
        "return document.getElementById('category_primary').closest('.select-container');"
    )
    if not container:
        raise Exception("Could not find .select-container wrapping #category_primary")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", container)
    rsleep(0.5)

    search_input = container.find_element(By.CLASS_NAME, "select-search-input")
    driver.execute_script("arguments[0].click();", search_input)
    rsleep(1.5)

    all_options = container.find_elements(By.CLASS_NAME, "select-option")
    valid_options = [
        o for o in all_options
        if o.get_attribute("data-value")
        and "select-option-not-available" not in (o.get_attribute("class") or "")
    ]

    if not valid_options:
        print(f"   ⚠️ All options found: {[o.text for o in all_options]}")
        raise Exception("No valid category options found in dropdown!")

    chosen = random.choice(valid_options)
    label = chosen.get_attribute("data-label") or chosen.text.strip()
    value = chosen.get_attribute("data-value")
    print(f"   → Randomly selected category: '{label}' (data-value={value})")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", chosen)
    rsleep(1.0)

    driver.execute_script("""
        var el = arguments[0];
        el.scrollIntoView({block:'center'});
        void el.offsetWidth;
        el.click();
    """, chosen)
    rsleep(2.0)

    actual = driver.execute_script(
        "return document.getElementById('category_primary').value;"
    )
    print(f"   → Hidden input value after click: {actual!r}")

    if actual == "0" or actual == "" or actual is None:
        print("   ⚠️ Component didn't update hidden input — forcing via JS...")
        driver.execute_script(
            """
            var inp = document.getElementById('category_primary');
            inp.value = arguments[0];
            ['input','change','blur'].forEach(function(ev) {
                inp.dispatchEvent(new Event(ev, {bubbles:true}));
            });
            """,
            value
        )
        rsleep(0.5)
        actual = driver.execute_script(
            "return document.getElementById('category_primary').value;"
        )
        print(f"   → Hidden input after JS force: {actual!r}")

    if actual == "0" or actual == "" or actual is None:
        raise Exception(f"Failed to set category — hidden input still '{actual}'")

    print(f"   ✓ Primary category confirmed! (value={actual!r})")

# ============================================================
#  MAIN UPLOAD LOOP
# ============================================================
while True:
    print(f"\n--- Upload #{uploads + 1} Started! ---")

    driver.get("https://rumble.com/upload.php")
    rsleep(5)

    file_path = getFirstFile()
    if not file_path:
        break

    # --- STEP 4: SELECT FILE ---
    try:
        print("   Step 4: Uploading file...")
        file_input = WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.ID, 'Filedata'))
        )
        file_input.send_keys(file_path)
        rsleep(5)
        print("   ✓ File selected! Upload is now in progress in the background.")
    except Exception as e:
        print(f"   ✗ Upload Error: {e}")
        break

    # --- STEP 4b: TITLE (NOW DYNAMIC FROM FILENAME!) ---
    try:
        videoTitle_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/main/div/div/div[2]/section/form[1]/div/div[2]/input[1]'))
        )
        
        # Extract title from filename instead of static config
        video_title = get_clean_filename(file_path)
        print(f"   → Using dynamic title: '{video_title}'")
        
        videoTitle_input.send_keys(video_title)
        rsleep(2)
    except Exception as e:
        print(f"   ✗ Unable to add Video Title: {e}")
        break


    # --- STEP 4c: DESCRIPTION ---
    try:
        video_description_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/main/div/div/div[2]/section/form[1]/div/div[2]/textarea'))
        )
        video_description_input.send_keys(CONFIG["video_description"])
        rsleep(2)
    except Exception as e:
        print(f"   ✗ Unable to add Video Description: {e}")
        break

    # --- STEP 4d: TAGS ---
    try:
        videoTag_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/main/div/div/div[2]/section/form[1]/div/div[2]/input[2]'))
        )
        videoTag_input.send_keys(CONFIG["video_tags"])
        rsleep(2)
    except Exception as e:
        print(f"   ✗ Unable to add Video Tags: {e}")
        break

    # --- STEP 5: PRIMARY CATEGORY ---
    try:
        select_random_category(driver)
    except Exception as e:
        print(f"   ✗ Unable to select Primary Category: {e}")
        break

    # --- STEP 6: VISIBILITY → UNLISTED ---
    try:
        select_unlisted(driver)
    except Exception as e:
        print(f"   ✗ Unable to set Visibility to Unlisted: {e}")
        break

    # --- STEP 5b: CLICK UPLOAD BUTTON (submits metadata form, NOT final submit) ---
    try:
        print("   Step 5b: Clicking Upload/Next button...")
        upload_button = None
        selectors = [
            (By.XPATH, '//form[1]//input[@type="submit"]'),
            (By.XPATH, '//form[1]//input[contains(@value,"Upload") or contains(@value,"upload") or contains(@value,"Submit") or contains(@value,"Next")]'),
            (By.XPATH, '/html/body/main/div/div/div[2]/section/form[1]/div/div[2]/div[7]/input'),
            (By.XPATH, '/html/body/main/div/div/div[2]/section/form[1]//input[@type="submit"]'),
        ]
        for by, sel in selectors:
            try:
                upload_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((by, sel))
                )
                print(f"   → Found upload button with: {sel}")
                break
            except:
                continue
        if not upload_button:
            raise Exception("Upload button not found with any selector")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", upload_button)
        rsleep(0.5)
        driver.execute_script("arguments[0].click();", upload_button)
        rsleep(5)
        print("   ✓ Upload/Next button clicked! Now on terms page...")
    except Exception as e:
        print(f"   ✗ Unable to click on upload button: {e}")
        break

    # --- STEP 7a: TOS CHECKBOX 1 (crights) ---
    try:
        print("   Step 7a: Checking first Terms checkbox (crights)...")
        click_checkbox_robustly(driver, 'crights')
        rsleep(1)
    except Exception as e:
        print(f"   ✗ Unable to check first Terms checkbox: {e}")
        break

    # --- STEP 7b: TOS CHECKBOX 2 (terms) ---
    try:
        print("   Step 7b: Checking second Terms checkbox (terms)...")
        click_checkbox_robustly(driver, 'cterms')
        rsleep(1)
    except Exception as e:
        print(f"   ✗ Unable to check second Terms checkbox: {e}")
        break

    # --- STEP 8: PERSONAL USE ---
    select_personal_use(driver)  # Non-fatal — won't break loop on failure

    # --- STEP 9: WAIT FOR ACTUAL VIDEO UPLOAD TO COMPLETE ---
    # ⚠️ IMPORTANT: The video file is still uploading in the background.
    # We MUST wait before hitting final Submit or Rumble will reject it.
    try:
        wait_for_upload_complete(driver, timeout_minutes=CONFIG["upload_timeout_minutes"])
    except Exception as e:
        print(f"   ✗ Upload wait failed: {e}")
        break

    # --- STEP 10: FINAL SUBMIT ---
    try:
        print("   Step 10: Clicking final Submit button...")
        submit_button = None
        submit_selectors = [
            (By.XPATH, '/html/body/main/div/div/div[2]/section/form[2]/div/div[11]/input[1]'),
            (By.XPATH, '//form[2]//input[@type="submit"]'),
            (By.XPATH, '//form[last()]//input[@type="submit"]'),
            (By.XPATH, '//form[2]//button[@type="submit"]'),
            (By.CSS_SELECTOR, 'form:last-of-type input[type="submit"]'),
        ]
        for by, sel in submit_selectors:
            try:
                submit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((by, sel))
                )
                print(f"   → Found submit button with: {sel}")
                break
            except:
                continue

        if not submit_button:
            raise Exception("Final submit button not found with any selector")

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_button)
        rsleep(0.5)
        driver.execute_script("arguments[0].click();", submit_button)
        rsleep(8)
        print("   ✓ Submitted successfully!")

        # ← DELETE HERE (now conditional on config - prevents infinite loop!)
        deleteTheFile(file_path)  # This will check CONFIG["auto_delete_after_upload"]
        rsleep(5)

        uploads += 1
        print(f"   ✓ Upload #{uploads} complete!")

    except Exception as e:
        print(f"   ✗ Unable to click on Submit button: {e}")
        break
    
# Write upload count so the embed grabber can auto-detect it
try:
    count_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_upload_count")
    with open(count_file, "w") as f:
        f.write(str(uploads))
    print(f"   → Saved upload count ({uploads}) for embed grabber.")
except Exception as e:
    print(f"   ⚠️  Could not save upload count: {e}")


print(f"\n=== All done! {uploads} video(s) uploaded. ===")
