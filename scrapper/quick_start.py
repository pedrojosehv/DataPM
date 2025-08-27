#!/usr/bin/env python3
"""
Quick Start Script for LinkedIn Applied Jobs Scraper
Provides easy options to run the scraper with different configurations.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from linkedin_applied_scraper import LinkedInAppliedScraper
    from test_scraper import run_all_tests
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("💡 Make sure all dependencies are installed:")
    print("   pip install -r requirements.txt")
    sys.exit(1)


def print_header():
    """Print the application header"""
    print("=" * 60)
    print("🚀 LinkedIn Applied Jobs Scraper - Quick Start")
    print("=" * 60)
    print("Extract your applied jobs from LinkedIn and export to CSV")
    print("=" * 60)


def print_menu():
    """Print the main menu options"""
    print("\n📋 Select an option:")
    print("   1. 🚀 Run scraper with default settings (5 pages)")
    print("   2. ⚙️ Run scraper with custom settings")
    print("   3. 🧪 Run tests to verify everything works")
    print("   4. 📖 Show README and instructions")
    print("   5. 🔧 Check configuration")
    print("   6. ❌ Exit")
    print()


def run_default_scraper():
    """Run scraper with default settings"""
    print("🚀 Running scraper with default settings...")
    print("   • Pages to scrape: 5")
    print("   • Manual login required")
    print("   • CSV output: D:\\Work Work\\Upwork\\DataPM\\csv\\src\\scrapped\\Applied\\")
    print()

    scraper = LinkedInAppliedScraper()
    scraper.run_scraper(max_pages=5)


def run_custom_scraper():
    """Run scraper with custom settings"""
    print("⚙️ Custom Scraper Settings")
    print("-" * 30)

    # Get custom number of pages
    try:
        pages_input = input("Enter number of pages to scrape (default 5): ").strip()
        max_pages = int(pages_input) if pages_input else 5

        if max_pages < 1 or max_pages > 50:
            print("⚠️ Invalid number of pages. Using default value of 5.")
            max_pages = 5

    except ValueError:
        print("⚠️ Invalid input. Using default value of 5.")
        max_pages = 5

    print(f"📄 Will scrape {max_pages} pages")
    print("🔐 Manual login will be required")
    print("📊 Results will be saved to CSV")
    print()

    confirm = input("Press Enter to start or 'c' to cancel: ").strip().lower()
    if confirm == 'c':
        print("❌ Operation cancelled")
        return

    scraper = LinkedInAppliedScraper()
    scraper.run_scraper(max_pages=max_pages)


def show_readme():
    """Show README information"""
    readme_path = current_dir / "README.md"
    if readme_path.exists():
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
        except Exception as e:
            print(f"❌ Error reading README: {e}")
    else:
        print("❌ README.md file not found")
        print("📖 Basic instructions:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Run the scraper: python linkedin_applied_scraper.py")
        print("   3. Follow the prompts for manual login")
        print("   4. CSV files will be saved in the Applied folder")


def check_configuration():
    """Check scraper configuration"""
    print("🔧 Checking Configuration")
    print("-" * 30)

    try:
        from config import Config

        # Test output folder
        output_folder = Config.get_output_folder()
        if os.path.exists(output_folder):
            print(f"✅ Output folder exists: {output_folder}")

            # Check write permissions
            try:
                test_file = os.path.join(output_folder, 'config_test.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print("✅ Output folder is writable")
            except:
                print("❌ Output folder is not writable")
        else:
            print(f"❌ Output folder does not exist: {output_folder}")

        # Show configuration info
        print(f"📄 Default pages: {Config.DEFAULT_MAX_PAGES}")
        print(f"🎯 Target URL: {Config.LINKEDIN_APPLIED_JOBS_URL}")
        print(f"📊 CSV Columns: {len(Config.CSV_COLUMNS)}")

        # Validate configuration
        errors = Config.validate_config()
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("✅ Configuration is valid")

    except Exception as e:
        print(f"❌ Error checking configuration: {e}")


def main():
    """Main function for quick start menu"""
    print_header()

    while True:
        print_menu()

        try:
            choice = input("Enter your choice (1-6): ").strip()

            if choice == '1':
                run_default_scraper()
                break
            elif choice == '2':
                run_custom_scraper()
                break
            elif choice == '3':
                print("🧪 Running tests...")
                success = run_all_tests()
                if success:
                    print("✅ All tests passed!")
                else:
                    print("❌ Some tests failed. Check the errors above.")
                break
            elif choice == '4':
                show_readme()
                break
            elif choice == '5':
                check_configuration()
                input("\nPress Enter to continue...")
            elif choice == '6':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-6.")
                input("Press Enter to continue...")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
