-- Create BigQuery External Table that automatically reads from GCS processed folder
-- This table will automatically include any new CSV files added to gs://datapm/processed/

CREATE OR REPLACE EXTERNAL TABLE `datapm-471620.datapm_jobs.processed_jobs`
OPTIONS (
  format = 'CSV',
  uris = ['gs://datapm/processed/*/*.csv'],
  skip_leading_rows = 1,
  allow_jagged_rows = false,
  allow_quoted_newlines = false
)
AS (
  SELECT
    _FILE_NAME as source_file,
    EXTRACT(DATE FROM PARSE_TIMESTAMP('%Y%m%d_%H%M%S', 
      REGEXP_EXTRACT(_FILE_NAME, r'(\d{8}_\d{6})')
    )) as processing_date,
    REGEXP_EXTRACT(_FILE_NAME, r'batch_(\d+)') as batch_number,
    job_title_original,
    job_title_short,
    company,
    country,
    state,
    city,
    schedule_type,
    experience_years,
    seniority,
    skills,
    degrees,
    software
  FROM (
    SELECT
      _FILE_NAME,
      STRING(COLUMN_1) as job_title_original,
      STRING(COLUMN_2) as job_title_short,
      STRING(COLUMN_3) as company,
      STRING(COLUMN_4) as country,
      STRING(COLUMN_5) as state,
      STRING(COLUMN_6) as city,
      STRING(COLUMN_7) as schedule_type,
      STRING(COLUMN_8) as experience_years,
      STRING(COLUMN_9) as seniority,
      STRING(COLUMN_10) as skills,
      STRING(COLUMN_11) as degrees,
      STRING(COLUMN_12) as software
  )
);

-- Create a view for easier querying
CREATE OR REPLACE VIEW `datapm-471620.datapm_jobs.jobs_unified` AS
SELECT 
  source_file,
  processing_date,
  CAST(batch_number AS INT64) as batch_number,
  job_title_original,
  job_title_short,
  company,
  country,
  state,
  city,
  schedule_type,
  experience_years,
  seniority,
  SPLIT(skills, '; ') as skills_array,
  skills,
  SPLIT(degrees, '; ') as degrees_array, 
  degrees,
  SPLIT(software, '; ') as software_array,
  software,
  CURRENT_TIMESTAMP() as last_queried
FROM `datapm-471620.datapm_jobs.processed_jobs`
WHERE job_title_original IS NOT NULL 
  AND job_title_original != '';

-- Query to test the table
SELECT 
  COUNT(*) as total_jobs,
  COUNT(DISTINCT company) as unique_companies,
  COUNT(DISTINCT job_title_short) as unique_job_titles,
  MIN(processing_date) as earliest_processing,
  MAX(processing_date) as latest_processing
FROM `datapm-471620.datapm_jobs.jobs_unified`;
