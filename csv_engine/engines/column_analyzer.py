#!/usr/bin/env python3
"""
Column Analyzer for DataPM CSV files
Analyzes the structure and columns of CSV files
"""

import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

class ColumnAnalyzer:
    """Analyzes column structure of CSV files"""
    
    def __init__(self, csv_processed_dir: str = "D:/Work Work/Upwork/DataPM/csv/src/csv_processed"):
        self.csv_processed_dir = Path(csv_processed_dir)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze_columns(self):
        """Analyze columns across all CSV files"""
        
        csv_files = list(self.csv_processed_dir.glob("*.csv"))
        
        if not csv_files:
            print("No CSV files found")
            return
        
        print("📊 DataPM CSV Column Analysis")
        print("=" * 50)
        
        all_columns = set()
        file_columns = {}
        
        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
                columns = list(df.columns)
                all_columns.update(columns)
                file_columns[file_path.name] = columns
                
                print(f"\n📄 {file_path.name}:")
                print(f"   Records: {len(df)}")
                print(f"   Columns: {len(columns)}")
                print(f"   Column names: {', '.join(columns)}")
                
            except Exception as e:
                print(f"❌ Error reading {file_path.name}: {e}")
        
        print(f"\n📋 SUMMARY:")
        print(f"   Total files: {len(csv_files)}")
        print(f"   Total unique columns: {len(all_columns)}")
        print(f"   All column names: {', '.join(sorted(all_columns))}")
        
        # Check for common columns
        common_columns = set.intersection(*[set(cols) for cols in file_columns.values()])
        print(f"   Common columns (in all files): {', '.join(sorted(common_columns))}")
        
        # Check for company-related columns
        company_columns = [col for col in all_columns if 'company' in col.lower()]
        print(f"   Company-related columns: {', '.join(company_columns)}")
        
        # Check for job-related columns
        job_columns = [col for col in all_columns if 'job' in col.lower() or 'title' in col.lower()]
        print(f"   Job-related columns: {', '.join(job_columns)}")
        
        # Check for location-related columns
        location_columns = [col for col in all_columns if 'location' in col.lower() or 'city' in col.lower() or 'country' in col.lower()]
        print(f"   Location-related columns: {', '.join(location_columns)}")
        
        return {
            'all_columns': sorted(all_columns),
            'common_columns': sorted(common_columns),
            'company_columns': company_columns,
            'job_columns': job_columns,
            'location_columns': location_columns,
            'file_columns': file_columns
        }

def main():
    """Main function"""
    analyzer = ColumnAnalyzer()
    analyzer.analyze_columns()

if __name__ == "__main__":
    main()
