#!/usr/bin/env python3
"""
Single URL Pipeline for DataPM

Usage:
  python single_url_pipeline.py --url "<job_url>" [--pageshot] [--headless]

Behavior:
  1) Scrape one job URL → title, company, location, description
     - LinkedIn URLs: open Selenium (manual login if required)
     - Other domains: requests + BeautifulSoup
  2) Save CSV to csv/src/scrapped/{timestamp}_single_url.csv
  3) Run DataPM engine to produce csv/src/csv_processed/*_DataPM_result_batch_1.csv

Notes:
  - This script does NOT store credentials. LinkedIn requires manual login once per session.
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

def is_linkedin(url: str) -> bool:
    return 'linkedin.com' in (url or '').lower()

def ensure_repo_paths() -> dict:
    # Resolve repo root from this file location
    scrapper_dir = Path(__file__).resolve().parent
    repo_root = scrapper_dir.parent
    scrapped_dir = repo_root / 'csv' / 'src' / 'scrapped'
    processed_dir = repo_root / 'csv' / 'src' / 'csv_processed'
    return {
        'repo_root': repo_root,
        'scrapper_dir': scrapper_dir,
        'scrapped_dir': scrapped_dir,
        'processed_dir': processed_dir,
    }

def scrape_non_linkedin(url: str) -> dict:
    try:
        import requests
        from bs4 import BeautifulSoup
    except Exception as e:
        print(f"❌ Missing dependencies for non-LinkedIn scraping: {e}")
        print("   pip install requests beautifulsoup4")
        sys.exit(1)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/127.0.0.1 Safari/537.36'
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    def pick_text(node):
        return (node.get_text(strip=True) if node else '').strip()

    title = pick_text(soup.find(['h1','h2'], attrs={'class': lambda c: True})) or pick_text(soup.find('h1'))
    company = ''
    location = ''
    description = ''

    # Heuristics
    company_node = soup.find(attrs={'class': lambda c: c and 'company' in c.lower()}) or soup.find('meta', attrs={'property':'og:site_name'})
    if company_node and company_node.name == 'meta':
        company = company_node.get('content','')
    else:
        company = pick_text(company_node)

    loc_node = soup.find(attrs={'class': lambda c: c and 'location' in c.lower()})
    location = pick_text(loc_node)

    # Prefer main article/content area
    main = soup.find('article') or soup.find('main') or soup.find('div', attrs={'class': lambda c: c and 'description' in c.lower()})
    description = pick_text(main) or pick_text(soup.find('body'))[:4000]

    return {
        'title': title or 'Unknown',
        'company': company or 'Unknown',
        'location': location or 'Unknown',
        'description': (description or '').replace('\n', ' ').strip(),
    }

def scrape_linkedin(url: str, headless: bool = False, pageshot: bool = False) -> dict:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except Exception as e:
        print(f"❌ Selenium not available: {e}")
        print("   pip install selenium webdriver-manager")
        sys.exit(1)

    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1280, 1200)
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 30)

        # If login required, give user time to login
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        except Exception:
            pass

        # Heuristics for job page content
        title = ''
        company = ''
        location = ''
        description = ''

        # Try multiple locators
        try:
            title = driver.find_element(By.CSS_SELECTOR, 'h1').text.strip()
        except Exception:
            pass
        # Company
        for sel in ['a.topcard__org-name-link','span.topcard__flavor','a[href*="/company/"]']:
            try:
                company = driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                if company:
                    break
            except Exception:
                continue
        # Location
        for sel in ['span.topcard__flavor--bullet','span.jobs-unified-top-card__bullet']:
            try:
                location = driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                if location:
                    break
            except Exception:
                continue
        # Description
        for sel in ['div.show-more-less-html__markup','div.description__text','div.jobs-description-content__text']:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                description = elem.text.strip()
                if description:
                    break
            except Exception:
                continue

        if pageshot:
            try:
                shot_path = Path('single_url_pageshot.png')
                driver.save_screenshot(str(shot_path))
                print(f"📸 Saved screenshot: {shot_path}")
            except Exception:
                pass

        return {
            'title': title or 'Unknown',
            'company': company or 'Unknown',
            'location': location or 'Unknown',
            'description': (description or '').replace('\n', ' ').strip(),
        }
    finally:
        driver.quit()

def write_scrapped_csv(row: dict, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = target_dir / f"{ts}_single_url.csv"
    header = 'title,company,location,description\n'
    import csv
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['title','company','location','description'])
        w.writeheader()
        w.writerow(row)
    print(f"📝 Scrapped CSV: {out}")
    return out

def run_datapm_engine(input_csv: Path) -> None:
    """Invoke DataPM engine to process the single CSV."""
    try:
        import subprocess, sys as _sys
        cmd = [
            _sys.executable,
            '-m','DataPM.csv_engine.engines.datapm_processor',
            str(input_csv),
            '--llm','gemini'
        ]
        print("🚀 Running DataPM engine...")
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"⚠️ Failed to run DataPM engine: {e}")

def main():
    ap = argparse.ArgumentParser(description='Single URL → scrapped CSV → DataPM processed CSV')
    ap.add_argument('--url', required=True, help='Job URL to scrape')
    ap.add_argument('--headless', action='store_true', help='Run browser headless for LinkedIn (may reduce success)')
    ap.add_argument('--pageshot', action='store_true', help='Save a page screenshot (LinkedIn)')
    ap.add_argument('--no-process', action='store_true', help='Skip DataPM engine step')
    args = ap.parse_args()

    paths = ensure_repo_paths()
    url = args.url.strip()

    if is_linkedin(url):
        print('🌐 LinkedIn URL detected - opening Selenium (manual login may be required)')
        row = scrape_linkedin(url, headless=args.headless, pageshot=args.pageshot)
    else:
        print('🌐 Non-LinkedIn URL detected - using requests + BeautifulSoup')
        row = scrape_non_linkedin(url)

    csv_path = write_scrapped_csv(row, paths['scrapped_dir'])

    if not args.no_process:
        run_datapm_engine(csv_path)
    else:
        print('⏭️ Skipping DataPM engine as requested')

if __name__ == '__main__':
    main()


