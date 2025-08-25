#!/usr/bin/env python3
"""
Intelligent Deduplication Processor for DataPM - SCRAPPED VERSION
Removes duplicates based on absolute field matches across all columns
Optimized for scrapped data to avoid wasting Gemini tokens
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
import hashlib
import argparse

class DeduplicationProcessor:
    """Intelligent deduplication processor for DataPM CSV files"""

    def __init__(self, scrapped_dir: str = "D:/Work Work/Upwork/DataPM/csv/src/scrapped"):
        self.scrapped_dir = Path(scrapped_dir)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for the deduplication process"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'deduplication_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_csv_files(self) -> List[Path]:
        """Get all CSV files in the scrapped directory"""
        csv_files = list(self.scrapped_dir.glob("*.csv"))
        self.logger.info(f"Found {len(csv_files)} CSV files to process")
        return csv_files

    def get_latest_csv_file(self) -> Path:
        """Get the most recent CSV file in the scrapped directory"""
        csv_files = self.get_csv_files()
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.scrapped_dir}")

        latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
        self.logger.info(f"Latest file: {latest_file.name} (modified: {datetime.fromtimestamp(latest_file.stat().st_mtime)})")
        return latest_file
    
    def analyze_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze potential duplicates in the dataframe"""
        analysis = {
            'total_records': len(df),
            'duplicate_analysis': {},
            'field_analysis': {}
        }
        
        # Analyze each field for potential duplicates
        for column in df.columns:
            if df[column].dtype == 'object':  # String columns
                # Count unique values
                unique_count = df[column].nunique()
                total_count = len(df)
                duplicate_percentage = ((total_count - unique_count) / total_count) * 100
                
                analysis['field_analysis'][column] = {
                    'unique_values': unique_count,
                    'duplicate_percentage': duplicate_percentage,
                    'most_common_values': df[column].value_counts().head(5).to_dict()
                }
        
        # Analyze potential duplicate combinations
        key_fields = ['job_title_original', 'company', 'location']
        available_fields = [field for field in key_fields if field in df.columns]
        
        if available_fields:
            # Check for duplicates based on key field combinations
            duplicate_groups = df.groupby(available_fields).size()
            duplicate_combinations = duplicate_groups[duplicate_groups > 1]
            
            analysis['duplicate_analysis'] = {
                'key_fields_used': available_fields,
                'duplicate_combinations_count': len(duplicate_combinations),
                'total_duplicate_records': duplicate_combinations.sum() - len(duplicate_combinations)
            }
        
        return analysis
    
    def create_hash_signature(self, row: pd.Series) -> str:
        """Create a hash signature for a row based on all fields"""
        # Convert all values to strings and concatenate
        row_string = "|".join([str(val) if pd.notna(val) else "" for val in row])
        return hashlib.md5(row_string.encode('utf-8')).hexdigest()
    
    def find_absolute_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Find records with absolute matches across all fields"""

        self.logger.info(f"Analyzing {len(df)} records for absolute duplicates...")

        # Create hash signatures for each row based on ALL fields
        df_with_hash = df.copy()
        df_with_hash['_hash_signature'] = df_with_hash.apply(self.create_hash_signature, axis=1)

        # Find duplicate hashes
        hash_counts = df_with_hash['_hash_signature'].value_counts()
        duplicate_hashes = hash_counts[hash_counts > 1].index

        if len(duplicate_hashes) == 0:
            self.logger.info("No absolute duplicates found")
            return df, pd.DataFrame()
        
        # Separate duplicates and unique records
        duplicate_mask = df_with_hash['_hash_signature'].isin(duplicate_hashes)
        duplicates_df = df_with_hash[duplicate_mask].drop('_hash_signature', axis=1)
        unique_df = df_with_hash[~duplicate_mask].drop('_hash_signature', axis=1)
        
        # Keep only one copy of each duplicate group
        unique_duplicates = df_with_hash[duplicate_mask].drop_duplicates(subset=['_hash_signature']).drop('_hash_signature', axis=1)
        
        final_unique_df = pd.concat([unique_df, unique_duplicates], ignore_index=True)
        
        self.logger.info(f"Found {len(duplicates_df)} duplicate records")
        self.logger.info(f"Kept {len(unique_duplicates)} unique records from duplicates")
        self.logger.info(f"Final unique records: {len(final_unique_df)}")
        
        return final_unique_df, duplicates_df
    
    def find_similar_duplicates(self, df: pd.DataFrame, similarity_threshold: float = 0.95) -> Dict[str, Any]:
        """Find records that are very similar but not absolutely identical"""
        
        self.logger.info(f"Analyzing {len(df)} records for similar duplicates...")
        
        similar_groups = []
        
        # Focus on key fields for similarity analysis
        key_fields = ['job_title_original', 'company', 'location', 'seniority']
        available_fields = [field for field in key_fields if field in df.columns]
        
        if len(available_fields) < 2:
            self.logger.warning("Not enough key fields for similarity analysis")
            return {'similar_groups': [], 'total_similar_records': 0}
        
        # Group by company first to reduce comparison space
        for company in df['company'].unique():
            company_df = df[df['company'] == company]
            
            if len(company_df) <= 1:
                continue
            
            # Compare records within the same company
            for i in range(len(company_df)):
                for j in range(i + 1, len(company_df)):
                    record1 = company_df.iloc[i]
                    record2 = company_df.iloc[j]
                    
                    # Calculate similarity score
                    similarity_score = self.calculate_similarity(record1, record2, available_fields)
                    
                    if similarity_score >= similarity_threshold:
                        similar_groups.append({
                            'record1_index': company_df.index[i],
                            'record2_index': company_df.index[j],
                            'similarity_score': similarity_score,
                            'company': company,
                            'record1_title': record1.get('job_title_original', 'Unknown'),
                            'record2_title': record2.get('job_title_original', 'Unknown')
                        })
        
        return {
            'similar_groups': similar_groups,
            'total_similar_records': len(similar_groups) * 2
        }
    
    def calculate_similarity(self, record1: pd.Series, record2: pd.Series, fields: List[str]) -> float:
        """Calculate similarity between two records"""
        matches = 0
        total_fields = len(fields)
        
        for field in fields:
            val1 = str(record1.get(field, '')).lower().strip()
            val2 = str(record2.get(field, '')).lower().strip()
            
            if val1 == val2:
                matches += 1
            elif val1 and val2:
                # Check for partial matches
                if val1 in val2 or val2 in val1:
                    matches += 0.8
        
        return matches / total_fields if total_fields > 0 else 0
    
    def process_file(self, file_path: Path, output_dir: Path = None) -> Dict[str, Any]:
        """Process a single CSV file for deduplication"""
        
        self.logger.info(f"Processing file: {file_path.name}")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path, encoding='utf-8')
            original_count = len(df)
            
            # Analyze duplicates
            analysis = self.analyze_duplicates(df)
            
            # Find absolute duplicates
            unique_df, duplicates_df = self.find_absolute_duplicates(df)
            
            # Find similar duplicates
            similar_analysis = self.find_similar_duplicates(unique_df)
            
            # Prepare results
            results = {
                'file_name': file_path.name,
                'original_records': original_count,
                'final_records': len(unique_df),
                'duplicates_removed': len(duplicates_df),
                'analysis': analysis,
                'similar_duplicates': similar_analysis
            }
            
            # Save deduplicated file
            if output_dir:
                output_dir.mkdir(exist_ok=True)
                output_file = output_dir / f"deduplicated_{file_path.name}"
                unique_df.to_csv(output_file, index=False, encoding='utf-8')
                results['output_file'] = str(output_file)
                
                # Save duplicates for review
                if len(duplicates_df) > 0:
                    duplicates_file = output_dir / f"duplicates_{file_path.name}"
                    duplicates_df.to_csv(duplicates_file, index=False, encoding='utf-8')
                    results['duplicates_file'] = str(duplicates_file)
            
            self.logger.info(f"✅ Processed {file_path.name}: {original_count} → {len(unique_df)} records")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error processing {file_path.name}: {e}")
            return {
                'file_name': file_path.name,
                'error': str(e),
                'original_records': 0,
                'final_records': 0
            }
    
    def process_all_files(self, output_dir: str = None) -> Dict[str, Any]:
        """Process all CSV files in the directory"""
        
        if output_dir is None:
            # Cambiar a la nueva carpeta de duplicados
            output_dir = self.csv_processed_dir.parent / "csv_duplicates" / "deduplicated"
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        csv_files = self.get_csv_files()
        
        if not csv_files:
            self.logger.warning("No CSV files found to process")
            return {'error': 'No CSV files found'}
        
        all_results = {
            'total_files': len(csv_files),
            'processed_files': 0,
            'total_original_records': 0,
            'total_final_records': 0,
            'total_duplicates_removed': 0,
            'file_results': []
        }
        
        for file_path in csv_files:
            result = self.process_file(file_path, output_path)
            all_results['file_results'].append(result)
            
            if 'error' not in result:
                all_results['processed_files'] += 1
                all_results['total_original_records'] += result['original_records']
                all_results['total_final_records'] += result['final_records']
                all_results['total_duplicates_removed'] += result['duplicates_removed']
        
        # Generate summary report
        self.generate_summary_report(all_results, output_path)
        
        return all_results
    
    def generate_summary_report(self, results: Dict[str, Any], output_dir: Path):
        """Generate a summary report of the deduplication process"""
        
        report_file = output_dir / "deduplication_summary.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("DATAPM DEDUPLICATION SUMMARY REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Total Files Processed: {results['processed_files']}/{results['total_files']}\n")
            f.write(f"Total Original Records: {results['total_original_records']:,}\n")
            f.write(f"Total Final Records: {results['total_final_records']:,}\n")
            f.write(f"Total Duplicates Removed: {results['total_duplicates_removed']:,}\n")
            f.write(f"Reduction Percentage: {((results['total_duplicates_removed'] / results['total_original_records']) * 100):.2f}%\n\n")
            
            f.write("DETAILED RESULTS:\n")
            f.write("-" * 40 + "\n")
            
            for result in results['file_results']:
                if 'error' not in result:
                    f.write(f"\nFile: {result['file_name']}\n")
                    f.write(f"  Original: {result['original_records']:,} records\n")
                    f.write(f"  Final: {result['final_records']:,} records\n")
                    f.write(f"  Duplicates Removed: {result['duplicates_removed']:,}\n")
                    f.write(f"  Reduction: {((result['duplicates_removed'] / result['original_records']) * 100):.2f}%\n")
                    
                    if result['similar_duplicates']['total_similar_records'] > 0:
                        f.write(f"  Similar Records Found: {result['similar_duplicates']['total_similar_records']}\n")
                else:
                    f.write(f"\nFile: {result['file_name']} - ERROR: {result['error']}\n")
        
        self.logger.info(f"📊 Summary report generated: {report_file}")

    def process_all_files_cross_duplicates(self) -> Dict[str, Any]:
        """Process ALL CSV files in scrapped directory and find cross-file duplicates"""
        try:
            # Get all CSV files
            csv_files = self.get_csv_files()
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found in {self.scrapped_dir}")

            print(f"📁 Processing {len(csv_files)} files for cross-duplicate analysis")
            print("🔍 Looking for duplicates ACROSS all files, not just within each file")

            # Load all files and concatenate
            all_dfs = []
            file_info = []

            for csv_file in csv_files:
                df = pd.read_csv(csv_file)
                df['_source_file'] = csv_file.name
                df['_source_path'] = str(csv_file)
                all_dfs.append(df)
                file_info.append({
                    'file_name': csv_file.name,
                    'record_count': len(df),
                    'modified': datetime.fromtimestamp(csv_file.stat().st_mtime)
                })

            # Concatenate all data
            combined_df = pd.concat(all_dfs, ignore_index=True)
            total_original_records = len(combined_df)

            print(f"📊 Combined dataset: {total_original_records:,} records from {len(csv_files)} files")

            # Show file breakdown
            print("\n📋 File breakdown:")
            for info in sorted(file_info, key=lambda x: x['record_count'], reverse=True):
                print(f"   {info['file_name']}: {info['record_count']:,} records")

            # Analyze duplicates across all files
            analysis = self.analyze_duplicates(combined_df)
            print("\n🔍 Cross-file Duplicate Analysis:")
            print(f"   Total records: {analysis['total_records']:,}")

            if analysis['duplicate_analysis']:
                print(f"   Key fields used: {', '.join(analysis['duplicate_analysis']['key_fields_used'])}")
                print(f"   Duplicate combinations: {analysis['duplicate_analysis']['duplicate_combinations_count']:,}")
                print(f"   Duplicate records: {analysis['duplicate_analysis']['total_duplicate_records']:,}")

            # Find absolute duplicates across all files
            unique_df, duplicates_df = self.find_absolute_duplicates(combined_df)

            # Create output directory
            output_dir = self.scrapped_dir.parent / "scrapped_deduplicated"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save deduplicated file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"cross_deduplicated_all_files_{timestamp}.csv"

            # Remove helper columns before saving
            unique_df_clean = unique_df.drop(['_source_file', '_source_path'], axis=1, errors='ignore')
            unique_df_clean.to_csv(output_file, index=False)

            # Save duplicates file with source information
            if len(duplicates_df) > 0:
                duplicates_file = output_dir / f"cross_duplicates_all_files_{timestamp}.csv"
                duplicates_df.to_csv(duplicates_file, index=False)

                # Show duplicate sources
                print("\n📋 Duplicate sources:")
                source_counts = duplicates_df['_source_file'].value_counts()
                for source, count in source_counts.items():
                    print(f"   {source}: {count} duplicates")

            result = {
                'total_files': len(csv_files),
                'original_records': total_original_records,
                'final_records': len(unique_df),
                'duplicates_removed': len(duplicates_df),
                'duplicates_file': str(duplicates_file) if len(duplicates_df) > 0 else None,
                'output_file': str(output_file),
                'file_info': file_info,
                'analysis': analysis
            }

            print("\n✅ Cross-file deduplication completed!")
            print(f"📁 Output file: {output_file}")
            if len(duplicates_df) > 0:
                print(f"📁 Duplicates file: {duplicates_file}")
            print("📊 Results:")
            print(f"   Total files processed: {len(csv_files)}")
            print(f"   Original records: {total_original_records:,}")
            print(f"   Final records: {len(unique_df):,}")
            print(f"   Duplicates removed: {len(duplicates_df):,}")
            if total_original_records > 0:
                print(f"   Reduction: {((len(duplicates_df) / total_original_records) * 100):.2f}%")

            return result

        except Exception as e:
            self.logger.error(f"Error in cross-file deduplication: {str(e)}")
            return {'error': str(e)}

    def process_latest_file_only(self) -> Dict[str, Any]:
        """Process only the most recent CSV file in scrapped directory"""
        try:
            # Get the latest file
            latest_file = self.get_latest_csv_file()

            print(f"📁 Processing latest file: {latest_file.name}")
            print(f"📅 Modified: {datetime.fromtimestamp(latest_file.stat().st_mtime)}")

            # Load and process the file
            df = pd.read_csv(latest_file)
            print(f"📊 Original records: {len(df):,}")

            # Analyze duplicates
            analysis = self.analyze_duplicates(df)
            print("🔍 Duplicate Analysis:")
            print(f"   Total records: {analysis['total_records']:,}")

            if analysis['duplicate_analysis']:
                print(f"   Key fields used: {', '.join(analysis['duplicate_analysis']['key_fields_used'])}")
                print(f"   Duplicate combinations: {analysis['duplicate_analysis']['duplicate_combinations_count']:,}")
                print(f"   Duplicate records: {analysis['duplicate_analysis']['total_duplicate_records']:,}")

            # Find and remove absolute duplicates
            unique_df, duplicates_df = self.find_absolute_duplicates(df)

            # Create output directory
            output_dir = self.scrapped_dir.parent / "scrapped_deduplicated"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save deduplicated file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"deduplicated_{latest_file.name}"

            unique_df.to_csv(output_file, index=False)

            # Save duplicates file for review
            if len(duplicates_df) > 0:
                duplicates_file = output_dir / f"duplicates_{latest_file.name}"
                duplicates_df.to_csv(duplicates_file, index=False)

            result = {
                'file_name': latest_file.name,
                'original_records': len(df),
                'final_records': len(unique_df),
                'duplicates_removed': len(duplicates_df),
                'duplicates_file': str(duplicates_file) if len(duplicates_df) > 0 else None,
                'output_file': str(output_file),
                'analysis': analysis
            }

            print("\n✅ Processing completed!")
            print(f"📁 Output file: {output_file}")
            if len(duplicates_df) > 0:
                print(f"📁 Duplicates file: {duplicates_file}")
            print("📊 Results:")
            print(f"   Original records: {len(df):,}")
            print(f"   Final records: {len(unique_df):,}")
            print(f"   Duplicates removed: {len(duplicates_df):,}")
            if len(df) > 0:
                print(f"   Reduction: {((len(duplicates_df) / len(df)) * 100):.2f}%")

            return result

        except Exception as e:
            self.logger.error(f"Error processing latest file: {str(e)}")
            return {'error': str(e)}

def main():
    """Main function to run the deduplication process on latest scrapped file"""

    parser = argparse.ArgumentParser(description="DataPM Deduplication Processor for Scrapped Data")
    parser.add_argument('--mode', choices=['latest', 'cross', 'all'], default='cross',
                       help='Process mode: latest (latest file only), cross (all files for duplicates across files), all (legacy mode)')
    parser.add_argument('--scrapped-dir', type=str,
                       default="D:/Work Work/Upwork/DataPM/csv/src/scrapped",
                       help='Directory containing scrapped CSV files')

    args = parser.parse_args()

    processor = DeduplicationProcessor(scrapped_dir=args.scrapped_dir)

    print("🧹 DataPM Scrapped Deduplication Processor")
    print("=" * 50)
    print(f"📂 Working directory: {args.scrapped_dir}")

    if args.mode == 'latest':
        # Process only the latest file
        print("🔍 Mode: Latest file only (within-file duplicates)")
        result = processor.process_latest_file_only()

        if 'error' not in result:
            print("\n✅ Latest file deduplication completed!")
            print(f"📁 Output directory: {processor.scrapped_dir.parent}/scrapped_deduplicated")
        else:
            print(f"❌ Error: {result['error']}")
    elif args.mode == 'cross':
        # Process all files for cross-file duplicates (NEW RECOMMENDED MODE)
        print("🔍 Mode: Cross-file duplicates (recommended)")
        result = processor.process_all_files_cross_duplicates()

        if 'error' not in result:
            print("\n✅ Cross-file deduplication completed!")
            print(f"📁 Output directory: {processor.scrapped_dir.parent}/scrapped_deduplicated")
        else:
            print(f"❌ Error: {result['error']}")
    else:
        # Process all files (legacy mode)
        print("⚠️  Mode: Legacy mode (all files separately)")
        results = processor.process_all_files()

        if 'error' not in results:
            print("\n✅ All files deduplication completed!")
            print(f"📁 Output directory: {processor.scrapped_dir.parent}/csv_duplicates/deduplicated")
            print("📊 Summary:")
            print(f"   Files processed: {results['processed_files']}/{results['total_files']}")
            print(f"   Original records: {results['total_original_records']:,}")
            print(f"   Final records: {results['total_final_records']:,}")
            print(f"   Duplicates removed: {results['total_duplicates_removed']:,}")
            print(f"   Reduction: {((results['total_duplicates_removed'] / results['total_original_records']) * 100):.2f}%")
        else:
            print(f"❌ Error: {results['error']}")

if __name__ == "__main__":
    main()
