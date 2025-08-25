#!/usr/bin/env python3
"""
Script to run deduplication on the latest scrapped CSV file
Optimized to avoid wasting Gemini tokens by removing duplicates before processing
"""

import subprocess
import sys
import os
from pathlib import Path

def run_scrapped_deduplication():
    """Run deduplication on the latest scrapped file"""

    # Path to the deduplication processor
    processor_path = Path(__file__).parent / "deduplication_processor.py"

    if not processor_path.exists():
        print("❌ Error: deduplication_processor.py not found")
        return False

    # Default scrapped directory
    scrapped_dir = "D:/Work Work/Upwork/DataPM/csv/src/scrapped"

    print("🧹 Running DataPM Cross-File Deduplication")
    print("=" * 50)
    print(f"📂 Processing ALL files from: {scrapped_dir}")
    print("🔍 Looking for duplicates ACROSS all files (not just within each file)")

    try:
        # Run the deduplication processor (using cross mode by default)
        cmd = [
            sys.executable,
            str(processor_path),
            "--mode", "cross",
            "--scrapped-dir", scrapped_dir
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        print(result.stdout)
        if result.stderr:
            print("⚠️  Warnings/Errors:", result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error running deduplication: {e}")
        return False

if __name__ == "__main__":
    success = run_scrapped_deduplication()
    if success:
        print("\n✅ Deduplication completed successfully!")
        print("💡 You can now run the DataPM processor on the deduplicated file")
        print("   to avoid wasting Gemini tokens on duplicate records.")
    else:
        print("\n❌ Deduplication failed!")
        sys.exit(1)
