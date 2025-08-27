#!/usr/bin/env python3
"""
Configuration file for LinkedIn Applied Jobs Scraper
"""

import os
from pathlib import Path


class Config:
    """Configuration class for the LinkedIn scraper"""

    # Default settings
    DEFAULT_MAX_PAGES = 5
    DEFAULT_OUTPUT_FOLDER = r"D:\Work Work\Upwork\DataPM\csv\src\scrapped\Applied"

    # LinkedIn URLs
    LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
    LINKEDIN_APPLIED_JOBS_URL = "https://www.linkedin.com/my-items/saved-jobs/?cardType=APPLIED"

    # CSS Selectors for data extraction
    SELECTORS = {
        'job_elements': 'rNwCYEmeXCNhYyFWlBXjROpztEvkpLjwKCNg',
        'job_title': 'NpAOenjuLyTkzcGAWovJllDYgHrUgYzuNQo',
        'company': 'RLLpRXfUhuWkXlOWWpMhjIFuffNPhTvZONk',
        'location': 'zVedEfoTitCUsGOHnAnZrnfHrgvZFKCtEs',
        'applied_insight': 'reusable-search-simple-insight__text',
        'next_button': "//button[contains(@aria-label, 'Next')]"
    }

    # CSV Column names
    CSV_COLUMNS = [
        'COMPANY',
        'JOB TITLE',
        'LOCATION',
        'JOB DESCRIPTION LINK',
        'SOURCE',
        'REFERRED BY',
        'SALARY',
        'BENEFITS',
        'APP SUBMITTED DATE'
    ]

    # Time patterns for date parsing
    DATE_PATTERNS = [
        r'(\d+)\s*m\s+ago',  # minutes
        r'(\d+)\s*h\s+ago',  # hours
        r'(\d+)\s*d\s+ago',  # days
        r'(\d+)\s*w\s+ago',  # weeks
    ]

    # Keywords to identify application-related insights
    APPLICATION_KEYWORDS = [
        'applied',
        'resume downloaded',
        'application viewed',
        'application sent'
    ]

    @classmethod
    def get_output_folder(cls):
        """Get the output folder path, creating it if it doesn't exist"""
        Path(cls.DEFAULT_OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)
        return cls.DEFAULT_OUTPUT_FOLDER

    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []

        # Check if output folder is writable
        try:
            test_file = os.path.join(cls.get_output_folder(), 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            errors.append(f"Output folder is not writable: {e}")

        return errors

    @classmethod
    def print_config_info(cls):
        """Print configuration information"""
        print("🔧 LinkedIn Scraper Configuration:")
        print(f"   📁 Output Folder: {cls.DEFAULT_OUTPUT_FOLDER}")
        print(f"   📄 Default Pages: {cls.DEFAULT_MAX_PAGES}")
        print(f"   📊 CSV Columns: {len(cls.CSV_COLUMNS)}")
        print(f"   🎯 Target URL: {cls.LINKEDIN_APPLIED_JOBS_URL}")
        print()


# Global configuration instance
config = Config()
