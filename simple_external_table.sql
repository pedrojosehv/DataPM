-- Create BigQuery dataset first
CREATE SCHEMA IF NOT EXISTS `datapm-471620.datapm_jobs`
OPTIONS (
  location = 'us'
);

-- Create External Table that auto-reads all CSV files from processed folder
CREATE OR REPLACE EXTERNAL TABLE `datapm-471620.datapm_jobs.processed_jobs_raw`
OPTIONS (
  format = 'CSV',
  uris = ['gs://datapm/processed/*/*.csv'],
  skip_leading_rows = 1,
  allow_jagged_rows = false,
  allow_quoted_newlines = true
);

-- Create a clean view with proper column names and data types
CREATE OR REPLACE VIEW `datapm-471620.datapm_jobs.jobs_clean` AS
SELECT 
  _FILE_NAME as source_file,
  REGEXP_EXTRACT(_FILE_NAME, r'(\d{8}_\d{6})') as processing_timestamp,
  REGEXP_EXTRACT(_FILE_NAME, r'batch_(\d+)') as batch_number,
  
  -- Job information
  string_field_1 as job_title_original,
  string_field_2 as job_title_short,
  string_field_3 as company,
  
  -- Location
  string_field_4 as country,
  string_field_5 as state, 
  string_field_6 as city,
  
  -- Job details
  string_field_7 as schedule_type,
  string_field_8 as experience_years,
  string_field_9 as seniority,
  
  -- Skills and requirements
  string_field_10 as skills,
  string_field_11 as degrees,
  string_field_12 as software,
  
  -- Metadata
  CURRENT_TIMESTAMP() as last_updated
  
FROM `datapm-471620.datapm_jobs.processed_jobs_raw`
WHERE string_field_1 IS NOT NULL 
  AND string_field_1 != ''
  AND string_field_1 != 'Job title (original)';  -- Skip any header rows

-- Test query to count records
SELECT 
  'Total Jobs' as metric,
  COUNT(*) as value
FROM `datapm-471620.datapm_jobs.jobs_clean`

UNION ALL

SELECT 
  'Unique Companies' as metric,
  COUNT(DISTINCT company) as value  
FROM `datapm-471620.datapm_jobs.jobs_clean`

UNION ALL

SELECT 
  'Processing Batches' as metric,
  COUNT(DISTINCT source_file) as value
FROM `datapm-471620.datapm_jobs.jobs_clean`;
