#!/usr/bin/env python3
"""
Advanced Deduplication Processor for DataPM
Analyzes duplicates across all files and provides intelligent duplicate detection
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
import hashlib

class AdvancedDeduplicationProcessor:
    """Advanced deduplication processor for DataPM CSV files"""
    
    def __init__(self, csv_processed_dir: str = "D:/Work Work/Upwork/DataPM/csv/src/csv_processed"):
        self.csv_processed_dir = Path(csv_processed_dir)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for the deduplication process"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'advanced_deduplication_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_csv_files(self) -> List[Path]:
        """Get all CSV files in the processed directory"""
        csv_files = list(self.csv_processed_dir.glob("*.csv"))
        self.logger.info(f"Found {len(csv_files)} CSV files to process")
        return csv_files
    
    def load_all_data(self) -> pd.DataFrame:
        """Load all CSV files into a single dataframe with file tracking"""
        csv_files = self.get_csv_files()
        all_data = []
        
        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
                df['_source_file'] = file_path.name
                df['_source_index'] = range(len(df))
                all_data.append(df)
                self.logger.info(f"Loaded {len(df)} records from {file_path.name}")
            except Exception as e:
                self.logger.error(f"Error loading {file_path.name}: {e}")
        
        if not all_data:
            return pd.DataFrame()
        
        combined_df = pd.concat(all_data, ignore_index=True)
        self.logger.info(f"Combined {len(combined_df)} total records from {len(csv_files)} files")
        return combined_df
    
    def analyze_cross_file_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze duplicates across all files"""
        
        analysis = {
            'total_records': len(df),
            'unique_companies': df['company'].nunique() if 'company' in df.columns else 0,
            'duplicate_analysis': {},
            'cross_file_duplicates': []
        }
        
        # Check for duplicates based on key combinations
        key_combinations = [
            ['job_title_original', 'company'],
            ['job_title_original', 'company', 'location'],
            ['job_title_original', 'company', 'seniority'],
            ['company', 'location', 'seniority']
        ]
        
        for combo in key_combinations:
            available_fields = [field for field in combo if field in df.columns]
            if len(available_fields) >= 2:
                duplicate_groups = df.groupby(available_fields).size()
                duplicate_combinations = duplicate_groups[duplicate_groups > 1]
                
                if len(duplicate_combinations) > 0:
                    analysis['duplicate_analysis'][f"duplicates_by_{'_'.join(available_fields)}"] = {
                        'fields_used': available_fields,
                        'duplicate_groups': len(duplicate_combinations),
                        'total_duplicate_records': duplicate_combinations.sum() - len(duplicate_combinations)
                    }
                    
                    # Get detailed duplicate information
                    for combo_values, count in duplicate_combinations.items():
                        if isinstance(combo_values, tuple):
                            combo_dict = dict(zip(available_fields, combo_values))
                        else:
                            combo_dict = {available_fields[0]: combo_values}
                        
                        duplicate_records = df.copy()
                        for field, value in combo_dict.items():
                            duplicate_records = duplicate_records[duplicate_records[field] == value]
                        
                        analysis['cross_file_duplicates'].append({
                            'fields': available_fields,
                            'values': combo_dict,
                            'count': count,
                            'records': duplicate_records[['_source_file', 'job_title_original', 'company', 'location'] + 
                                                        [col for col in duplicate_records.columns if col not in 
                                                         ['_source_file', 'job_title_original', 'company', 'location', '_source_index']]].to_dict('records')
                        })
        
        return analysis
    
    def find_absolute_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Find records with absolute matches across all fields"""
        
        self.logger.info(f"Analyzing {len(df)} records for absolute duplicates...")
        
        # Create hash signatures for each row (excluding file tracking columns)
        data_columns = [col for col in df.columns if not col.startswith('_')]
        df_data = df[data_columns].copy()
        
        # Create hash signatures
        df_data['_hash_signature'] = df_data.apply(self.create_hash_signature, axis=1)
        
        # Find duplicate hashes
        hash_counts = df_data['_hash_signature'].value_counts()
        duplicate_hashes = hash_counts[hash_counts > 1].index
        
        if len(duplicate_hashes) == 0:
            self.logger.info("No absolute duplicates found")
            return df, pd.DataFrame()
        
        # Separate duplicates and unique records
        duplicate_mask = df_data['_hash_signature'].isin(duplicate_hashes)
        duplicates_df = df[duplicate_mask].copy()
        unique_df = df[~duplicate_mask].copy()
        
        # Keep only one copy of each duplicate group
        unique_duplicates = df[duplicate_mask].drop_duplicates(subset=data_columns)
        
        final_unique_df = pd.concat([unique_df, unique_duplicates], ignore_index=True)
        
        self.logger.info(f"Found {len(duplicates_df)} duplicate records")
        self.logger.info(f"Kept {len(unique_duplicates)} unique records from duplicates")
        self.logger.info(f"Final unique records: {len(final_unique_df)}")
        
        return final_unique_df, duplicates_df
    
    def create_hash_signature(self, row: pd.Series) -> str:
        """Create a hash signature for a row based on all fields"""
        # Convert all values to strings and concatenate
        row_string = "|".join([str(val) if pd.notna(val) else "" for val in row])
        return hashlib.md5(row_string.encode('utf-8')).hexdigest()
    
    def find_similar_jobs(self, df: pd.DataFrame, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Find jobs that are very similar but not identical"""
        
        similar_jobs = []
        
        # Group by company to reduce comparison space
        for company in df['company'].unique():
            company_df = df[df['company'] == company]
            
            if len(company_df) <= 1:
                continue
            
            # Compare job titles within the same company
            for i in range(len(company_df)):
                for j in range(i + 1, len(company_df)):
                    record1 = company_df.iloc[i]
                    record2 = company_df.iloc[j]
                    
                    # Calculate similarity score
                    similarity_score = self.calculate_job_similarity(record1, record2)
                    
                    if similarity_score >= similarity_threshold:
                        similar_jobs.append({
                            'record1': {
                                'file': record1['_source_file'],
                                'title': record1.get('job_title_original', 'Unknown'),
                                'location': record1.get('location', 'Unknown'),
                                'seniority': record1.get('seniority', 'Unknown')
                            },
                            'record2': {
                                'file': record2['_source_file'],
                                'title': record2.get('job_title_original', 'Unknown'),
                                'location': record2.get('location', 'Unknown'),
                                'seniority': record2.get('seniority', 'Unknown')
                            },
                            'similarity_score': similarity_score,
                            'company': company
                        })
        
        return similar_jobs
    
    def calculate_job_similarity(self, record1: pd.Series, record2: pd.Series) -> float:
        """Calculate similarity between two job records"""
        
        # Compare job titles
        title1 = str(record1.get('job_title_original', '')).lower().strip()
        title2 = str(record2.get('job_title_original', '')).lower().strip()
        
        if title1 == title2:
            title_similarity = 1.0
        elif title1 and title2:
            # Check for partial matches
            words1 = set(title1.split())
            words2 = set(title2.split())
            
            if words1 and words2:
                intersection = words1.intersection(words2)
                union = words1.union(words2)
                title_similarity = len(intersection) / len(union)
            else:
                title_similarity = 0.0
        else:
            title_similarity = 0.0
        
        # Compare other fields
        location_match = (str(record1.get('location', '')) == str(record2.get('location', '')))
        seniority_match = (str(record1.get('seniority', '')) == str(record2.get('seniority', '')))
        
        # Weighted similarity score
        similarity = (title_similarity * 0.6 + 
                     (1.0 if location_match else 0.0) * 0.2 + 
                     (1.0 if seniority_match else 0.0) * 0.2)
        
        return similarity
    
    def process_all_files(self, output_dir: str = None) -> Dict[str, Any]:
        """Process all CSV files for advanced deduplication"""
        
        if output_dir is None:
            # Cambiar a la nueva carpeta de duplicados
            output_dir = self.csv_processed_dir.parent / "csv_duplicates" / "advanced_deduplicated"
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Load all data
        combined_df = self.load_all_data()
        
        if len(combined_df) == 0:
            return {'error': 'No data loaded'}
        
        # Analyze cross-file duplicates
        analysis = self.analyze_cross_file_duplicates(combined_df)
        
        # Find absolute duplicates
        unique_df, duplicates_df = self.find_absolute_duplicates(combined_df)
        
        # Find similar jobs
        similar_jobs = self.find_similar_jobs(unique_df)
        
        # Prepare results
        results = {
            'total_files': len(self.get_csv_files()),
            'total_original_records': len(combined_df),
            'total_final_records': len(unique_df),
            'total_duplicates_removed': len(duplicates_df),
            'cross_file_analysis': analysis,
            'similar_jobs_found': len(similar_jobs)
        }
        
        # Save deduplicated data
        if len(duplicates_df) > 0:
            # Save unique records
            unique_output = output_path / "unique_records.csv"
            unique_df.to_csv(unique_output, index=False, encoding='utf-8')
            results['unique_output_file'] = str(unique_output)
            
            # Save duplicates for review
            duplicates_output = output_path / "duplicate_records.csv"
            duplicates_df.to_csv(duplicates_output, index=False, encoding='utf-8')
            results['duplicates_output_file'] = str(duplicates_output)
        else:
            # No duplicates found, save original data
            original_output = output_path / "all_records_unique.csv"
            combined_df.to_csv(original_output, index=False, encoding='utf-8')
            results['output_file'] = str(original_output)
        
        # Save similar jobs analysis
        if similar_jobs:
            similar_output = output_path / "similar_jobs_analysis.csv"
            similar_df = pd.DataFrame(similar_jobs)
            similar_df.to_csv(similar_output, index=False, encoding='utf-8')
            results['similar_jobs_file'] = str(similar_output)
        
        # Generate detailed report
        self.generate_advanced_report(results, analysis, similar_jobs, output_path)
        
        return results
    
    def generate_advanced_report(self, results: Dict[str, Any], analysis: Dict[str, Any], 
                               similar_jobs: List[Dict[str, Any]], output_dir: Path):
        """Generate a detailed report of the advanced deduplication process"""
        
        report_file = output_dir / "advanced_deduplication_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("DATAPM ADVANCED DEDUPLICATION ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("SUMMARY:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total Files Analyzed: {results['total_files']}\n")
            f.write(f"Total Records: {results['total_original_records']:,}\n")
            f.write(f"Unique Records: {results['total_final_records']:,}\n")
            f.write(f"Duplicates Removed: {results['total_duplicates_removed']:,}\n")
            f.write(f"Similar Jobs Found: {results['similar_jobs_found']}\n")
            f.write(f"Unique Companies: {analysis['unique_companies']}\n\n")
            
            f.write("CROSS-FILE DUPLICATE ANALYSIS:\n")
            f.write("-" * 40 + "\n")
            
            if analysis['duplicate_analysis']:
                for key, data in analysis['duplicate_analysis'].items():
                    f.write(f"\n{key.replace('_', ' ').title()}:\n")
                    f.write(f"  Fields: {', '.join(data['fields_used'])}\n")
                    f.write(f"  Duplicate Groups: {data['duplicate_groups']}\n")
                    f.write(f"  Total Duplicate Records: {data['total_duplicate_records']}\n")
            else:
                f.write("No cross-file duplicates found based on key field combinations.\n")
            
            f.write("\nDETAILED DUPLICATE GROUPS:\n")
            f.write("-" * 40 + "\n")
            
            for i, duplicate_group in enumerate(analysis['cross_file_duplicates'], 1):
                f.write(f"\nGroup {i}:\n")
                f.write(f"  Fields: {', '.join(duplicate_group['fields'])}\n")
                f.write(f"  Values: {duplicate_group['values']}\n")
                f.write(f"  Count: {duplicate_group['count']}\n")
                f.write("  Records:\n")
                
                for record in duplicate_group['records']:
                    f.write(f"    - {record['_source_file']}: {record.get('job_title_original', 'Unknown')} at {record.get('company', 'Unknown')}\n")
            
            f.write("\nSIMILAR JOBS ANALYSIS:\n")
            f.write("-" * 40 + "\n")
            
            if similar_jobs:
                for i, similar_job in enumerate(similar_jobs[:10], 1):  # Show first 10
                    f.write(f"\nSimilar Job Pair {i}:\n")
                    f.write(f"  Company: {similar_job['company']}\n")
                    f.write(f"  Similarity Score: {similar_job['similarity_score']:.2f}\n")
                    f.write(f"  Job 1: {similar_job['record1']['title']} ({similar_job['record1']['file']})\n")
                    f.write(f"  Job 2: {similar_job['record2']['title']} ({similar_job['record2']['file']})\n")
                
                if len(similar_jobs) > 10:
                    f.write(f"\n... and {len(similar_jobs) - 10} more similar job pairs.\n")
            else:
                f.write("No similar jobs found.\n")
        
        self.logger.info(f"Advanced report generated: {report_file}")

def main():
    """Main function to run the advanced deduplication process"""
    
    processor = AdvancedDeduplicationProcessor()
    
    print("🧹 DataPM Advanced Deduplication Processor")
    print("=" * 60)
    
    # Process all files
    results = processor.process_all_files()
    
    if 'error' not in results:
        print(f"\n✅ Advanced deduplication completed successfully!")
        print(f"📁 Output directory: {processor.csv_processed_dir.parent}/csv_duplicates/advanced_deduplicated")
        print(f"📊 Summary:")
        print(f"   Files analyzed: {results['total_files']}")
        print(f"   Total records: {results['total_original_records']:,}")
        print(f"   Unique records: {results['total_final_records']:,}")
        print(f"   Duplicates removed: {results['total_duplicates_removed']:,}")
        print(f"   Similar jobs found: {results['similar_jobs_found']}")
        
        if results['total_original_records'] > 0:
            reduction = ((results['total_duplicates_removed'] / results['total_original_records']) * 100)
            print(f"   Reduction: {reduction:.2f}%")
    else:
        print(f"❌ Error: {results['error']}")

if __name__ == "__main__":
    main()
