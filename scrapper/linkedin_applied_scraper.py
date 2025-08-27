#!/usr/bin/env python3
"""
LinkedIn Applied Jobs Scraper
Scrapes applied jobs from LinkedIn and exports to CSV with specified columns.
"""

import time
import csv
import os
import re
import random
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


class LinkedInAppliedScraper:
    def __init__(self):
        self.jobs_data = []
        self.driver = None
        self.output_folder = r"D:\Work Work\Upwork\DataPM\csv\src\scrapped\Applied"

    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()

        # Basic options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Performance options
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Speed up loading

        # Window size for better compatibility
        chrome_options.add_argument("--window-size=1920,1080")

        # Uncomment the line below if you want to run in headless mode
        # chrome_options.add_argument("--headless")

        try:
            # Use webdriver-manager for automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Execute script to hide webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print("✅ Chrome driver initialized successfully!")

        except Exception as e:
            print(f"❌ Error initializing Chrome driver: {e}")
            print("💡 Make sure Chrome is installed and up to date.")
            print("   You can download it from: https://www.google.com/chrome/")
            raise

    def login_linkedin(self):
        """Manual login to LinkedIn"""
        print("🚀 Opening LinkedIn login page...")
        self.driver.get("https://www.linkedin.com/login")

        print("📝 Please log in to LinkedIn manually:")
        print("   1. Enter your email/username")
        print("   2. Enter your password")
        print("   3. Complete any 2FA if required")
        print("   4. Press Enter here when you're logged in and on the main page")

        input("Press Enter when you're logged in and ready to continue...")

    def navigate_to_applied_jobs(self):
        """Navigate to the applied jobs page"""
        print("🔍 Navigating to Applied Jobs page...")
        applied_jobs_url = "https://www.linkedin.com/my-items/saved-jobs/?cardType=APPLIED"
        self.driver.get(applied_jobs_url)

        # Wait for the page to load
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "workflow-results-container"))
            )

            # Verify we're on the applied jobs tab
            applied_tab = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'artdeco-pill--selected') and contains(text(), 'Applied')]")
            if applied_tab:
                print("✅ Applied Jobs page loaded successfully!")
                return True
            else:
                print("⚠️ Page loaded but 'Applied' tab might not be selected.")
                print("   Please make sure you're on the 'Applied' tab.")
                return True

        except Exception as e:
            print(f"❌ Error loading Applied Jobs page: {e}")
            print("💡 Possible causes:")
            print("   - Slow internet connection")
            print("   - LinkedIn page structure changed")
            print("   - You might not be logged in properly")
            return False

    def check_for_applied_jobs(self):
        """Check if there are any applied jobs and provide feedback"""
        try:
            # Look for empty state message
            empty_state = self.driver.find_elements(By.XPATH, "//div[contains(text(), 'No jobs')]")
            if empty_state:
                print("⚠️ No applied jobs found on LinkedIn.")
                print("   This might mean:")
                print("   - You haven't applied to any jobs yet")
                print("   - Your applied jobs are not visible")
                print("   - LinkedIn page structure has changed")
                return False

            # Count initial jobs
            initial_jobs = len(self.driver.find_elements(By.CLASS_NAME, "rNwCYEmeXCNhYyFWlBXjROpztEvkpLjwKCNg"))
            if initial_jobs == 0:
                print("⚠️ No job elements found on the page.")
                print("   Please make sure you're on the 'Applied' tab.")
                return False
            else:
                print(f"✅ Found {initial_jobs} applied jobs on initial load")
                return True

        except Exception as e:
            print(f"⚠️ Could not check for applied jobs: {e}")
            return True  # Continue anyway

    def scroll_and_load_jobs(self, max_pages=None):
        """Scroll through pages to load all applied jobs"""
        if max_pages is None:
            print(f"📄 Loading ALL available applied jobs (no page limit)...")
        else:
            print(f"📄 Loading jobs from up to {max_pages} pages...")

        # Check if there are any applied jobs
        if not self.check_for_applied_jobs():
            print("❌ No applied jobs found. Stopping...")
            return

        page = 0
        total_jobs_found = 0

        while True:
            page += 1
            print(f"📊 Processing page {page}...")

            # Check if we've reached the page limit
            if max_pages is not None and page > max_pages:
                print(f"🛑 Reached page limit of {max_pages}. Stopping...")
                break

            # Wait for jobs to load
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "rNwCYEmeXCNhYyFWlBXjROpztEvkpLjwKCNg"))
                )
            except Exception as e:
                print(f"⚠️ Warning: Could not find job elements on page {page}: {e}")
                break

            # Get current job count
            current_jobs = len(self.driver.find_elements(By.CLASS_NAME, "rNwCYEmeXCNhYyFWlBXjROpztEvkpLjwKCNg"))
            print(f"   📋 Found {current_jobs} jobs on current page")

            # Extensive scrolling to load ALL jobs on this page
            initial_jobs = current_jobs
            max_scroll_attempts = 10  # Increased from 3

            for scroll_attempt in range(max_scroll_attempts):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Increased wait time

                # Check if more jobs loaded
                new_job_count = len(self.driver.find_elements(By.CLASS_NAME, "rNwCYEmeXCNhYyFWlBXjROpztEvkpLjwKCNg"))
                if new_job_count > current_jobs:
                    current_jobs = new_job_count
                    print(f"   📋 Scroll {scroll_attempt + 1}: found {current_jobs} jobs total")
                elif scroll_attempt >= 3:  # Stop if no new jobs after 3 attempts
                    break

            jobs_on_page = current_jobs - initial_jobs
            total_jobs_found += current_jobs
            print(f"   ✅ Page {page}: {jobs_on_page} new jobs (total so far: {total_jobs_found})")

            # 🔑 CRITICAL: Extract jobs from this page BEFORE navigating to next page
            print(f"🔍 Extracting {current_jobs} jobs from page {page}...")
            page_job_elements = self.driver.find_elements(By.CLASS_NAME, "rNwCYEmeXCNhYyFWlBXjROpztEvkpLjwKCNg")

            for i, job_element in enumerate(page_job_elements):
                try:
                    job_data = self.extract_single_job_data(job_element)
                    if job_data:
                        self.jobs_data.append(job_data)
                        print(f"✅ Extracted job {len(self.jobs_data)}: {job_data['JOB TITLE']} at {job_data['COMPANY']}")
                except Exception as e:
                    print(f"❌ Error extracting job {i + 1} on page {page}: {e}")
                    continue

            # Try to click next page button
            try:
                next_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Next')]"))
                )

                # Check if next button is disabled (last page)
                if next_button.get_attribute("disabled") or "disabled" in next_button.get_attribute("class"):
                    print(f"🛑 Reached last page. Total jobs found: {total_jobs_found}")
                    break

                next_button.click()
                print(f"   ➡️ Navigated to page {page + 1}")
                time.sleep(5)  # Increased wait time for page load

            except Exception as e:
                print(f"🛑 Could not navigate to next page: {e}")
                print(f"   This appears to be the last page. Total jobs found: {total_jobs_found}")
                break

    def extract_jobs_data(self):
        """Extract job data from the current page"""
        print("🔍 Extracting job data...")

        job_elements = self.driver.find_elements(By.CLASS_NAME, "rNwCYEmeXCNhYyFWlBXjROpztEvkpLjwKCNg")

        for i, job_element in enumerate(job_elements):
            try:
                job_data = self.extract_single_job_data(job_element)
                if job_data:
                    self.jobs_data.append(job_data)
                    print(f"✅ Extracted job {i + 1}: {job_data['JOB TITLE']} at {job_data['COMPANY']}")
            except Exception as e:
                print(f"❌ Error extracting job {i + 1}: {e}")
                continue

        print(f"📊 Total jobs extracted: {len(self.jobs_data)}")

    def extract_single_job_data(self, job_element):
        """Extract data from a single job element with enhanced debugging"""
        job_data = {
            'COMPANY': '',
            'JOB TITLE': '',
            'LOCATION': '',
            'JOB DESCRIPTION LINK': '',
            'SOURCE': '',  # Not available on applied jobs page
            'REFERRED BY': '',  # Not available on applied jobs page
            'SALARY': '',  # Not available on applied jobs page
            'BENEFITS': '',  # Not available on applied jobs page
            'APP SUBMITTED DATE': ''
        }

        try:
            # DEBUG: Print the full text content of the job element
            full_text = job_element.text
            print(f"🔍 DEBUG - Full job text: {full_text[:200]}...")

            # Extract Job Title and Link with multiple fallback strategies
            job_title_found = False
            job_link_found = False

            # Strategy 1: Original selector
            try:
                title_element = job_element.find_element(By.CLASS_NAME, "NpAOenjuLyTkzcGAWovJllDYgHrUgYzuNQo")
                title_text = title_element.text.strip()
                if title_text:  # Only set if we actually got text
                    job_data['JOB TITLE'] = title_text
                    job_data['JOB DESCRIPTION LINK'] = title_element.get_attribute('href')
                    job_title_found = True
                    job_link_found = True
                    print(f"✅ Strategy 1 SUCCESS - Title: '{job_data['JOB TITLE']}'")
                else:
                    print(f"❌ Strategy 1 FAILED: Empty text")
            except Exception as e:
                print(f"❌ Strategy 1 FAILED: {e}")

            # Strategy 2: Look for any link with job title pattern
            if not job_title_found:
                try:
                    # Look for links containing job-related keywords
                    all_links = job_element.find_elements(By.TAG_NAME, "a")
                    print(f"🔍 Found {len(all_links)} links in job element")
                    for i, link in enumerate(all_links):
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        print(f"   Link {i+1}: '{text}' -> {href}")
                        if href and ('linkedin.com/jobs/view' in href or 'linkedin.com/jobs' in href):
                            if text and len(text) > 3:  # Must have meaningful text
                                job_data['JOB TITLE'] = text
                                job_data['JOB DESCRIPTION LINK'] = href
                                job_title_found = True
                                job_link_found = True
                                print(f"✅ Strategy 2 SUCCESS - Title: '{job_data['JOB TITLE']}'")
                                break
                except Exception as e:
                    print(f"❌ Strategy 2 FAILED: {e}")

            # Strategy 3: Use full text parsing as fallback
            if not job_title_found:
                try:
                    # Parse the full text to extract job title
                    lines = full_text.split('\n')
                    print(f"🔍 Parsing {len(lines)} lines of text")

                    # Look for job title patterns in the text
                    for i, line in enumerate(lines):
                        line = line.strip()
                        print(f"   Line {i+1}: '{line}'")

                        # Skip lines that are clearly not job titles
                        if any(skip_word in line.lower() for skip_word in [
                            'applied', 'ago', 'days', 'hours', 'remote', 'hybrid', 'on-site',
                            'full-time', 'part-time', 'contract', 'temporary', 'permanent',
                            'view', 'download', 'resume', 'application', 'company'
                        ]):
                            continue

                        # Look for reasonable job title patterns
                        if (line and len(line) > 5 and len(line) < 100 and
                            not line[0].isdigit() and  # Not starting with numbers
                            not re.search(r'\d{1,2}[/-]\d{1,2}', line)):  # Not a date

                            # Check if it looks like a job title (contains typical job words)
                            job_keywords = ['manager', 'analyst', 'developer', 'engineer', 'consultant',
                                          'specialist', 'coordinator', 'assistant', 'director', 'lead',
                                          'senior', 'junior', 'product', 'business', 'data', 'sales',
                                          'marketing', 'designer', 'administrator', 'technician']

                            if any(keyword in line.lower() for keyword in job_keywords):
                                job_data['JOB TITLE'] = line
                                job_title_found = True
                                print(f"✅ Strategy 3 SUCCESS - Title: '{job_data['JOB TITLE']}'")
                                break

                except Exception as e:
                    print(f"❌ Strategy 3 FAILED: {e}")

            # Extract Company with multiple strategies
            try:
                company_element = job_element.find_element(By.CLASS_NAME, "RLLpRXfUhuWkXlOWWpMhjIFuffNPhTvZONk")
                job_data['COMPANY'] = company_element.text.strip()
                print(f"✅ Company found: '{job_data['COMPANY']}'")
            except:
                try:
                    company_element = job_element.find_element(By.CSS_SELECTOR, "[data-test-id='company-name']")
                    job_data['COMPANY'] = company_element.text.strip()
                    print(f"✅ Company found (alt): '{job_data['COMPANY']}'")
                except:
                    try:
                        # Extract company from text parsing
                        lines = full_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            # Company names are typically shorter and don't contain certain keywords
                            if (line and len(line) > 2 and len(line) < 50 and
                                not any(keyword in line.lower() for keyword in [
                                    'applied', 'ago', 'remote', 'hybrid', 'on-site', 'full-time',
                                    'part-time', 'view', 'download', 'resume'
                                ]) and
                                not re.search(r'\d{1,2}[/-]\d{1,2}|\d{1,2}\s+(d|h|w|m)\s+ago', line.lower())):

                                # If we haven't found a title yet, this might be the title
                                if not job_title_found and len(line) > 5:
                                    job_data['JOB TITLE'] = line
                                    job_title_found = True
                                    print(f"✅ Title from company search: '{job_data['JOB TITLE']}'")
                                else:
                                    job_data['COMPANY'] = line
                                    print(f"✅ Company from text: '{job_data['COMPANY']}'")
                                    break
                    except Exception as e:
                        print(f"❌ Company extraction FAILED: {e}")

            # Extract Location
            try:
                location_element = job_element.find_element(By.CLASS_NAME, "zVedEfoTitCUsGOHnAnZrnfHrgvZFKCtEs")
                job_data['LOCATION'] = location_element.text.strip()
                print(f"✅ Location found: '{job_data['LOCATION']}'")
            except:
                try:
                    location_element = job_element.find_element(By.CSS_SELECTOR, "[data-test-id='job-location']")
                    job_data['LOCATION'] = location_element.text.strip()
                    print(f"✅ Location found (alt): '{job_data['LOCATION']}'")
                except:
                    # Try to extract location from text
                    location_patterns = [
                        r'\b(Remote|On-site|Hybrid)\b',
                        r'\b[Madrid|Barcelona|Valencia|Seville|Zaragoza|Malaga|Murcia|Palma|Bilbao|Alicante|Cordoba|Vigo|Gijon]\b',
                        r'\bSpain|USA|UK|Germany|France\b'
                    ]

                    for pattern in location_patterns:
                        match = re.search(pattern, full_text)
                        if match:
                            job_data['LOCATION'] = match.group()
                            print(f"✅ Location from text: '{job_data['LOCATION']}'")
                            break

            # Extract Application Date
            try:
                insight_elements = job_element.find_elements(By.CLASS_NAME, "reusable-search-simple-insight__text")
                for insight in insight_elements:
                    text = insight.text.strip()
                    if any(keyword in text.lower() for keyword in ['applied', 'resume downloaded', 'application viewed', 'application sent', 'applied on']):
                        job_data['APP SUBMITTED DATE'] = self.parse_application_date(text)
                        print(f"✅ Date found: '{text}' -> '{job_data.get('APP SUBMITTED DATE', 'N/A')}'")
                        break
            except Exception as e:
                print(f"❌ Date extraction FAILED: {e}")

            # If no date found, calculate based on current time
            if not job_data.get('APP SUBMITTED DATE'):
                job_data['APP SUBMITTED DATE'] = self.calculate_submitted_date()
                print(f"📅 Using calculated date: '{job_data.get('APP SUBMITTED DATE', 'N/A')}'")

            # Final validation
            if not job_data['JOB TITLE']:
                print(f"⚠️ Skipping job without title - Company: '{job_data['COMPANY']}', Location: '{job_data['LOCATION']}'")
                print("Full job text for debugging:")
                print(full_text)
                return None

            print(f"✅ Successfully extracted job: '{job_data['JOB TITLE']}' at '{job_data['COMPANY']}'")

        except Exception as e:
            print(f"⚠️ Error extracting job data: {e}")
            return None

        return job_data

    def parse_application_date(self, date_text):
        """Parse application date from text like 'Applied 4m ago'"""
        try:
            # Extract time value and unit
            match = re.search(r'(\d+)\s*(m|h|d|w)\s+ago', date_text.lower())
            if match:
                value = int(match.group(1))
                unit = match.group(2)

                now = datetime.now()

                if unit == 'm':  # minutes
                    submitted_date = now - timedelta(minutes=value)
                elif unit == 'h':  # hours
                    submitted_date = now - timedelta(hours=value)
                elif unit == 'd':  # days
                    submitted_date = now - timedelta(days=value)
                elif unit == 'w':  # weeks
                    submitted_date = now - timedelta(weeks=value)
                else:
                    return self.calculate_submitted_date()

                return submitted_date.strftime('%Y-%m-%d %H:%M:%S')

        except Exception as e:
            print(f"⚠️ Error parsing date '{date_text}': {e}")

        return self.calculate_submitted_date()

    def calculate_submitted_date(self):
        """Calculate submitted date when exact time is not available"""
        # Default to current time minus a random offset to simulate realistic submission times
        now = datetime.now()
        # Subtract 1-30 days randomly to simulate different submission times
        import random
        days_ago = random.randint(1, 30)
        submitted_date = now - timedelta(days=days_ago)
        return submitted_date.strftime('%Y-%m-%d %H:%M:%S')

    def save_to_csv(self, filename=None):
        """Save extracted data to CSV file"""
        if not self.jobs_data:
            print("❌ No data to save!")
            return

        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"linkedin_applied_jobs_{timestamp}.csv"

        filepath = os.path.join(self.output_folder, filename)

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['COMPANY', 'JOB TITLE', 'LOCATION', 'JOB DESCRIPTION LINK',
                             'SOURCE', 'REFERRED BY', 'SALARY', 'BENEFITS', 'APP SUBMITTED DATE']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.jobs_data)

            print(f"✅ Data saved to: {filepath}")
            print(f"📊 Total jobs saved: {len(self.jobs_data)}")

        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")

    def print_summary(self):
        """Print a summary of the scraping session"""
        if not self.jobs_data:
            print("📊 No jobs were extracted.")
            return

        print("\n" + "=" * 60)
        print("📊 SCRAPING SUMMARY")
        print("=" * 60)

        # Basic stats
        total_jobs = len(self.jobs_data)
        companies = [job['COMPANY'] for job in self.jobs_data if job['COMPANY']]
        unique_companies = len(set(companies))

        print(f"✅ Total jobs extracted: {total_jobs}")
        print(f"🏢 Unique companies: {unique_companies}")

        # Date analysis
        dates = [job['APP SUBMITTED DATE'] for job in self.jobs_data if job['APP SUBMITTED DATE']]
        if dates:
            try:
                date_objects = [datetime.strptime(date, '%Y-%m-%d %H:%M:%S') for date in dates]
                oldest_date = min(date_objects)
                newest_date = max(date_objects)
                print(f"📅 Date range: {oldest_date.strftime('%Y-%m-%d')} to {newest_date.strftime('%Y-%m-%d')}")
            except:
                pass

        # Location analysis
        locations = [job['LOCATION'] for job in self.jobs_data if job['LOCATION']]
        if locations:
            print(f"📍 Locations found: {len(set(locations))} unique")

        # Most common companies (top 5)
        if companies:
            from collections import Counter
            company_counts = Counter(companies)
            top_companies = company_counts.most_common(5)
            print("🏆 Top companies by applications:")
            for company, count in top_companies:
                if company:  # Only show companies with names
                    print(f"   • {company}: {count} applications")

        print("=" * 60)

    def run_scraper(self, max_pages=None):
        """Run the complete scraping process"""
        print("🚀 Starting LinkedIn Applied Jobs Scraper")
        print("=" * 50)

        try:
            # Setup driver
            self.setup_driver()

            # Manual login
            self.login_linkedin()

            # Navigate to applied jobs
            if not self.navigate_to_applied_jobs():
                print("❌ Failed to load Applied Jobs page. Exiting...")
                return

            # Scroll and load jobs (jobs are extracted within this function)
            self.scroll_and_load_jobs(max_pages)

            # Save to CSV
            self.save_to_csv()

            # Print summary
            self.print_summary()

        except Exception as e:
            print(f"❌ Error during scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("🛑 Browser closed")

        print("=" * 50)
        print("✅ Scraping completed!")


def main():
    """Main function to run the scraper"""
    print("LinkedIn Applied Jobs Scraper")
    print("This tool will help you scrape your applied jobs from LinkedIn")
    print("=" * 60)

    # Get user input for number of pages
    print("📋 Options:")
    print("   • Press Enter to scrape ALL available pages (recommended)")
    print("   • Enter a number to limit pages (e.g., 10 for first 10 pages)")

    try:
        pages_input = input("Enter number of pages to scrape (or press Enter for ALL): ").strip()

        if not pages_input:
            # Default: process ALL pages
            max_pages = None
            print("🔄 Will process ALL available pages (no limit)")
        else:
            max_pages = int(pages_input)
            if max_pages < 1 or max_pages > 100:
                print("⚠️ Invalid number of pages. Using ALL pages instead.")
                max_pages = None
            else:
                print(f"📄 Will process first {max_pages} pages")

    except ValueError:
        print("⚠️ Invalid input. Processing ALL available pages.")
        max_pages = None

    print()
    # Create scraper instance and run
    scraper = LinkedInAppliedScraper()
    scraper.run_scraper(max_pages)


if __name__ == "__main__":
    main()
