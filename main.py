# from playwright.sync_api import sync_playwright
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin, urlparse, parse_qs
# import pandas as pd
# import time, re
# from datetime import datetime

# URL = "https://www.pib.gov.in/allRel.aspx?reg=3&lang=1"
# PRID_RE = re.compile(r"PRID=(\d+)", flags=re.IGNORECASE)
# DEBUG_HTML = "debug_page.html"
# DEBUG_SCREEN = "debug_screenshot.png"

# def parse_content_area_flexible(html, base_url):
#     """Robust parser for PIB structure."""
#     soup = BeautifulSoup(html, "lxml")
#     records = []

#     # Strategy: Find departments (h3) and extract links
#     h3_nodes = soup.find_all("h3")
#     if h3_nodes:
#         for h3 in h3_nodes:
#             department = h3.get_text(" ", strip=True)
#             parent_li = h3.find_parent("li")
#             nested_ul = None
#             if parent_li:
#                 nested_ul = parent_li.find("ul", class_="num")
#                 if not nested_ul:
#                     nested_ul = parent_li.find("ul")
#             if not nested_ul:
#                 sib = h3.find_next_sibling()
#                 if sib and sib.name == "ul":
#                     nested_ul = sib
#             if not nested_ul:
#                 next_ul = h3.find_next("ul")
#                 if next_ul:
#                     nested_ul = next_ul

#             a_tags = []
#             if nested_ul:
#                 a_tags = nested_ul.find_all("a", href=True)
#             elif parent_li:
#                 a_tags = parent_li.find_all("a", href=True)
#             else:
#                 a_tags = h3.find_all("a", href=True)

#             for a in a_tags:
#                 title = (a.get("title") or a.get_text(" ", strip=True)).strip()
#                 href = a.get("href")
#                 full_url = urljoin(base_url, href) if href else None
#                 pr_id = None
#                 if href:
#                     qs = urlparse(href).query
#                     parsed = parse_qs(qs)
#                     if "PRID" in parsed:
#                         pr_id = parsed["PRID"][0]
#                     else:
#                         m = PRID_RE.search(href)
#                         if m:
#                             pr_id = m.group(1)
#                 parent_li_for_a = a.find_parent("li")
#                 snippet = None
#                 if parent_li_for_a:
#                     parent_text = parent_li_for_a.get_text(" ", strip=True)
#                     snippet = parent_text.replace(title, "").strip()
#                     if snippet == "":
#                         snippet = None

#                 records.append({
#                     "department": department,
#                     "title": title,
#                     "url": full_url,
#                     "pr_id": pr_id,
#                     "snippet": snippet
#                 })

#     # Fallback Strategy: Scan all lists if no H3 found
#     if not records:
#         candidate_links = []
#         for outer_ul in soup.find_all("ul"):
#             for li in outer_ul.find_all("li", recursive=False):
#                 inner_ul = li.find("ul")
#                 if inner_ul:
#                     for inner_li in inner_ul.find_all("li", recursive=False):
#                         for a in inner_li.find_all("a", href=True):
#                             candidate_links.append((None, a))
#         if not candidate_links:
#             for a in soup.find_all("a", href=True):
#                 candidate_links.append((None, a))

#         for dept, a in candidate_links:
#             title = (a.get("title") or a.get_text(" ", strip=True)).strip()
#             href = a.get("href")
#             full_url = urljoin(base_url, href) if href else None
#             pr_id = None
#             if href:
#                 qs = urlparse(href).query
#                 parsed = parse_qs(qs)
#                 if "PRID" in parsed:
#                     pr_id = parsed["PRID"][0]
#                 else:
#                     m = PRID_RE.search(href)
#                     if m:
#                         pr_id = m.group(1)
#             parent_li_for_a = a.find_parent("li")
#             snippet = None
#             if parent_li_for_a:
#                 parent_text = parent_li_for_a.get_text(" ", strip=True)
#                 snippet = parent_text.replace(title, "").strip()
#                 if snippet == "":
#                     snippet = None
#             records.append({
#                 "department": dept,
#                 "title": title,
#                 "url": full_url,
#                 "pr_id": pr_id,
#                 "snippet": snippet
#             })

#     if records:
#         df = pd.DataFrame(records)
#         if "department" in df.columns:
#             df["department"] = df["department"].ffill()
#         return df
#     else:
#         return pd.DataFrame(records)

# def run(headless=False, max_wait=60):
#     with sync_playwright() as pw:
#         print(f"Launching browser (Headless: {headless}) with Manual Stealth...")
        
#         # 1. BROWSER ARGUMENTS TO HIDE AUTOMATION
#         browser = pw.chromium.launch(
#             headless=headless,
#             channel="chrome", # Tries to use your installed Google Chrome (More stealthy)
#             args=[
#                 "--disable-blink-features=AutomationControlled", 
#                 "--no-sandbox", 
#                 "--disable-setuid-sandbox",
#                 "--disable-infobars",
#                 "--window-size=1920,1080"
#             ]
#         )

#         ctx = browser.new_context(
#             viewport={"width": 1920, "height": 1080},
#             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#             locale="en-US"
#         )
        
#         page = ctx.new_page()

#         # 2. MANUAL JAVASCRIPT INJECTION (The "Stealth" part)
#         # This overwrites the properties that the website checks to see if you are a robot.
#         stealth_scripts = [
#             "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
#             "window.navigator.chrome = { runtime: {} };",
#             "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});",
#             "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});"
#         ]
#         for script in stealth_scripts:
#             page.add_init_script(script)

#         print("Navigating to", URL)
#         try:
#             page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
#         except Exception as e:
#             print(f"Navigation warning: {e}")

#         # Basic wait for stability
#         time.sleep(2) 
        
#         print(f"Page Title: {page.title()}")
#         if "Access Denied" in page.title():
#             print("CRITICAL: Blocked by WAF (Access Denied).")
#             page.screenshot(path=DEBUG_SCREEN)
#             return

#         print(f"Waiting up to {max_wait}s for content area...")
        
#         try:
#             # Explicitly wait for the .content-area div
#             page.wait_for_selector(".content-area", state="visible", timeout=45_000)
            
#             # Wait for list items to actually populate inside it
#             # Using a function to poll for count > 0
#             page.wait_for_function("document.querySelectorAll('.content-area ul li').length > 0", timeout=max_wait*1000)
            
#             print("Content detected.")

#             # Try loading more
#             for i in range(3):
#                 load_more = page.locator("text='Load more'")
#                 if load_more.is_visible():
#                     print("Clicking Load More...")
#                     load_more.click()
#                     time.sleep(3)
#                 else:
#                     break

#         except Exception as e:
#             print(f"Error waiting for content: {e}")
#             # We continue, to capture whatever HTML IS present

#         # Capture HTML
#         try:
#             container = page.query_selector(".content-area")
#             html = container.inner_html() if container else page.content()
#         except:
#             html = page.content()

#         # Save Debug
#         with open(DEBUG_HTML, "w", encoding="utf-8") as f:
#             f.write(html)
#         page.screenshot(path=DEBUG_SCREEN, full_page=True)
#         print("Debug files saved.")

#         # Parse
#         df = parse_content_area_flexible(html, base_url=URL)
#         if df.empty:
#             print("No records parsed. Please inspect debug_screenshot.png and debug_page.html")
#         else:
#             df["department"] = df["department"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
#             df["title"] = df["title"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
#             outname = f"pib_releases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
#             df.to_csv(outname, index=False, encoding="utf-8-sig")
#             print(f"SUCCESS: Saved {len(df)} records to {outname}")
#             print(df.head(10).to_string(index=False))

#         ctx.close()
#         browser.close()

# if __name__ == "__main__":
#     run(headless=True, max_wait=60)

import os
import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from google.cloud import storage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

# --- CONFIGURATION ---
URL = "https://www.pib.gov.in/allRel.aspx?reg=3&lang=1"
BUCKET_NAME = os.environ.get("BUCKET_NAME", "source_pib") 
PRID_RE = re.compile(r"PRID=(\d+)", flags=re.IGNORECASE)

# --- GCS HELPERS ---
def get_bucket():
    """Singleton-like bucket retrieval."""
    client = storage.Client()
    return client.bucket(BUCKET_NAME)

def upload_to_gcs(local_path, blob_name):
    """Uploads a file to GCS."""
    try:
        bucket = get_bucket()
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path)
        print(f"Uploaded: gs://{BUCKET_NAME}/{blob_name}")
    except Exception as e:
        print(f"GCS Upload Error: {e}")

def parse_content_area_flexible(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    records = []
    
    # 1. Try finding the main department headers
    h3_nodes = soup.find_all("h3")
    if h3_nodes:
        for h3 in h3_nodes:
            department = h3.get_text(" ", strip=True)
            parent_li = h3.find_parent("li")
            nested_ul = None
            if parent_li:
                nested_ul = parent_li.find("ul", class_="num") or parent_li.find("ul")
            if not nested_ul:
                sib = h3.find_next_sibling()
                if sib and sib.name == "ul": nested_ul = sib
            
            a_tags = nested_ul.find_all("a", href=True) if nested_ul else []
            if not a_tags and parent_li:
                a_tags = parent_li.find_all("a", href=True)

            for a in a_tags:
                title = (a.get("title") or a.get_text(" ", strip=True)).strip()
                href = a.get("href")
                full_url = urljoin(base_url, href) if href else None
                pr_id = None
                if href:
                    m = PRID_RE.search(href)
                    if m: pr_id = m.group(1)

                records.append({
                    "department": department,
                    "title": title,
                    "url": full_url,
                    "pr_id": pr_id,
                    "scraped_at": datetime.utcnow().isoformat()
                })
    
    # 2. Fallback: If strict parsing failed, grab ALL links in the content area
    if not records:
        print("Strict parsing found 0 records. Attempting fallback...")
        content_div = soup.select_one(".content-area")
        if content_div:
            for a in content_div.find_all("a", href=True):
                 records.append({
                    "department": "Unknown",
                    "title": (a.get("title") or a.get_text()).strip(),
                    "url": urljoin(base_url, a['href']),
                    "scraped_at": datetime.utcnow().isoformat()
                })

    if records:
        df = pd.DataFrame(records)
        if "department" in df.columns:
            df["department"] = df["department"].ffill()
        return df
    return pd.DataFrame(records)

def run():
    with sync_playwright() as pw:
        print("Launching Playwright (Headless New Mode)...")
        
        browser = pw.chromium.launch(
            headless=False, # Forced via args below
            args=[
                "--headless=new", 
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1920,1080"
            ]
        )

        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="Asia/Kolkata",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.pib.gov.in/",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        
        page = ctx.new_page()

        # Stealth JS
        stealth_js = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.navigator.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        """
        page.add_init_script(stealth_js)

        print(f"Navigating to {URL}")
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            # 1. Wait for the Container
            print("Waiting for .content-area...")
            page.wait_for_selector(".content-area", timeout=30000)
            
            # 2. CRITICAL FIX: Wait for the actual DATA (list items) to appear
            print("Container found. Waiting for list items (ul li)...")
            try:
                # Wait until there is at least 1 list item inside content-area
                page.wait_for_selector(".content-area ul li a", timeout=30000)
                print("List items loaded!")
            except Exception:
                print("Warning: List items did not appear. Page might be empty.")

            # 3. Optional: Click 'Load More' to get more data
            try:
                if page.locator("text='Load more'").is_visible():
                    print("Clicking 'Load more'...")
                    page.locator("text='Load more'").click()
                    time.sleep(3) # Wait for AJAX
            except:
                pass

            # 4. Extract HTML
            content_html = page.locator(".content-area").inner_html()
            print(f"DEBUG: Captured {len(content_html)} characters of HTML.")

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            browser.close()
            return

        browser.close()

        # Parse & Save
        print("Parsing extracted HTML...")
        df = parse_content_area_flexible(content_html, URL)
        
        if not df.empty:
            print(f"SUCCESS: Extracted {len(df)} records.")
            filename = f"pib_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Save locally
            df.to_csv(filename, index=False)
            print(f"Saved local file: {filename}")
            
            # Upload to GCS
            upload_to_gcs(filename, f"data/{filename}")
        else:
            print("Parser returned 0 records.")
            # Save the HTML to see what went wrong
            with open("debug_failed_parse.html", "w", encoding="utf-8") as f:
                f.write(content_html)
            print("Saved 'debug_failed_parse.html' for inspection.")

if __name__ == "__main__":
    run()