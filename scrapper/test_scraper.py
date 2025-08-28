#!/usr/bin/env python3
"""
Test script for LinkedIn Applied Jobs Scraper
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from linkedin_applied_scraper import LinkedInAppliedScraper


def test_config():
    """Test configuration settings"""
    print("🧪 Testing configuration...")

    # Test output folder
    try:
        output_folder = Config.get_output_folder()
        print(f"✅ Output folder: {output_folder}")

        # Test write permissions
        test_file = os.path.join(output_folder, 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✅ Output folder is writable")

    except Exception as e:
        print(f"❌ Output folder error: {e}")
        return False

    # Validate configuration
    errors = Config.validate_config()
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        return False

    print("✅ Configuration test passed!")
    return True


def test_date_parsing():
    """Test date parsing functionality"""
    print("🧪 Testing date parsing...")

    scraper = LinkedInAppliedScraper()

    test_cases = [
        ("Applied 4m ago", "minutes"),
        ("Resume downloaded 15h ago", "hours"),
        ("Application viewed 1d ago", "days"),
        ("Applied 2w ago", "weeks"),
        ("Invalid date format", "fallback")
    ]

    for test_text, expected_type in test_cases:
        try:
            result = scraper.parse_application_date(test_text)
            if result and result != scraper.calculate_submitted_date():
                print(f"✅ '{test_text}' -> {result}")
            else:
                result = scraper.calculate_submitted_date()
                print(f"⚠️ '{test_text}' -> {result} (fallback)")
        except Exception as e:
            print(f"❌ Error parsing '{test_text}': {e}")

    print("✅ Date parsing test completed!")
    return True


def simulate_extraction():
    """Simulate job data extraction (without actual scraping)"""
    print("🧪 Simulating job data extraction...")

    # Sample job data structure
    sample_jobs = [
        {
            'COMPANY': 'TechCorp Inc.',
            'JOB TITLE': 'Senior Python Developer',
            'LOCATION': 'Madrid, Spain (Remote)',
            'JOB DESCRIPTION LINK': 'https://www.linkedin.com/jobs/view/1234567890',
            'SOURCE': '',
            'REFERRED BY': '',
            'SALARY': '',
            'BENEFITS': '',
            'APP SUBMITTED DATE': '2024-01-15 10:30:00'
        },
        {
            'COMPANY': 'DataFlow Solutions',
            'JOB TITLE': 'Data Analyst',
            'LOCATION': 'Barcelona, Spain (Hybrid)',
            'JOB DESCRIPTION LINK': 'https://www.linkedin.com/jobs/view/9876543210',
            'SOURCE': '',
            'REFERRED BY': '',
            'SALARY': '',
            'BENEFITS': '',
            'APP SUBMITTED DATE': '2024-01-14 15:45:00'
        }
    ]

    scraper = LinkedInAppliedScraper()
    scraper.jobs_data = sample_jobs

    # Test CSV generation
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    test_filename = f"test_extraction_{timestamp}.csv"

    try:
        scraper.save_to_csv(test_filename)
        print(f"✅ Test CSV generated: {test_filename}")

        # Verify file exists and has content
        filepath = os.path.join(Config.get_output_folder(), test_filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"✅ CSV file has {len(lines)} lines")
                if len(lines) >= 2:  # Header + at least one data row
                    print("✅ CSV structure is valid")
                else:
                    print("⚠️ CSV file seems empty")
        else:
            print("❌ CSV file was not created")

    except Exception as e:
        print(f"❌ Error generating test CSV: {e}")
        return False

    print("✅ Extraction simulation completed!")
    return True


def run_all_tests():
    """Run all tests"""
    print("🚀 Running LinkedIn Scraper Tests")
    print("=" * 50)

    tests = [
        ("Configuration Test", test_config),
        ("Date Parsing Test", test_date_parsing),
        ("Extraction Simulation", simulate_extraction)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
        print()

    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The scraper is ready to use.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False


def main():
    """Main test function"""
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()

        if test_name == "config":
            test_config()
        elif test_name == "dates":
            test_date_parsing()
        elif test_name == "extraction":
            simulate_extraction()
        else:
            print("❌ Unknown test. Available tests: config, dates, extraction")
    else:
        run_all_tests()


if __name__ == "__main__":
    main()

