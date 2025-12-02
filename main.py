import os
from google.cloud import storage
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import pandas as pd
import time, re
from datetime import datetime

# --- CONFIGURATION ---
URL = "https://www.pib.gov.in/allRel.aspx"
BUCKET_NAME = os.environ.get("BUCKET_NAME", "source_pib") # Set this in Cloud Run env vars
PRID_RE = re.compile(r"PRID=(\d+)", flags=re.IGNORECASE)

def upload_to_gcs(local_filename, destination_blob_name):
    """Uploads a file to the bucket."""
    print(f"Uploading {local_filename} to gs://{BUCKET_NAME}/{destination_blob_name}...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_filename)
    print("Upload complete.")

def parse_content_area_flexible(html, base_url):
    """(Your existing parser logic - kept identical)"""
    soup = BeautifulSoup(html, "lxml")
    records = []
    
    # ... [PASTE YOUR EXISTING PARSER LOGIC HERE TO SAVE SPACE] ...
    # For brevity in this answer, I am summarizing the parser. 
    # Please ensure your full parse_content_area_flexible function is included here.
    
    # <--- INSERT FULL PARSER CODE HERE --->
    
    # Quick re-implementation of the H3 loop for completeness of the example:
    h3_nodes = soup.find_all("h3")
    if h3_nodes:
        for h3 in h3_nodes:
            department = h3.get_text(" ", strip=True)
            parent_li = h3.find_parent("li")
            nested_ul = parent_li.find("ul", class_="num") or parent_li.find("ul")
            
            # simplified lookup for demo
            if not nested_ul:
                sib = h3.find_next_sibling()
                if sib and sib.name == "ul": nested_ul = sib
            
            a_tags = nested_ul.find_all("a", href=True) if nested_ul else []
            if not a_tags and parent_li: a_tags = parent_li.find_all("a", href=True)

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
    
    if records:
        df = pd.DataFrame(records)
        if "department" in df.columns: df["department"] = df["department"].ffill()
        return df
    return pd.DataFrame(records)

def run():
    with sync_playwright() as pw:
        print("Launching Playwright (Chromium)...")
        # NOTE: Removed channel="chrome" because Cloud Run uses Linux Chromium
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage" # Crucial for Docker/Cloud Run
            ]
        )

        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = ctx.new_page()

        # Stealth Scripts
        stealth_scripts = [
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            "window.navigator.chrome = { runtime: {} };",
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});",
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});"
        ]
        for script in stealth_scripts:
            page.add_init_script(script)

        print(f"Navigating to {URL}")
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector(".content-area", timeout=45000)
            
            # Wait for content to populate
            page.wait_for_function("document.querySelectorAll('.content-area ul li').length > 0", timeout=60000)
            
            # Load more logic
            for _ in range(3):
                if page.locator("text='Load more'").is_visible():
                    page.locator("text='Load more'").click()
                    time.sleep(3)
                else:
                    break
        except Exception as e:
            print(f"Scraping warning (proceeding to extraction): {e}")

        # Extract
        try:
            container = page.query_selector(".content-area")
            html = container.inner_html() if container else page.content()
        except:
            html = page.content()

        browser.close()

        # Parse and Save
        df = parse_content_area_flexible(html, URL)
        if not df.empty:
            filename = f"pib_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            # 1. Save locally (temporary)
            df.to_csv(filename, index=False)
            print(f"Saved locally: {filename}")
            
            # 2. Upload to Cloud Storage
            try:
                upload_to_gcs(filename, filename)
            except Exception as e:
                print(f"FAILED to upload to GCS: {e}")
        else:
            print("No records found.")

if __name__ == "__main__":
    run()