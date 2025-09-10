-- ========================================
-- MODELO DIMENSIONAL DATAPM EN BIGQUERY
-- ========================================

-- 1. TABLA DE HECHOS PRINCIPAL: job_offers_fact
-- ========================================
CREATE OR REPLACE TABLE `datapm-471620.csv_processed.job_offers_fact` AS
SELECT 
  -- Job ID secuencial simple (números naturales)
  ROW_NUMBER() OVER (ORDER BY source_file, batch_number, job_title_original) as job_id,
  
  -- Información básica del trabajo
  job_title_original as job_title_long,
  job_title_short,
  company,
  
  -- Ubicación
  city,
  country,
  
  -- Detalles del trabajo
  schedule_type,
  experience_years,
  seniority,
  
  -- Campos para relaciones (mantener para crear dimensiones)
  skills,
  degrees,
  software,
  
  -- Metadatos
  source_file,
  processing_timestamp,
  batch_number,
  CURRENT_TIMESTAMP() as created_at
  
FROM `datapm-471620.csv_processed.jobs_unified`
WHERE job_title_original IS NOT NULL 
  AND job_title_original != '';

-- 2. DIMENSIÓN: dim_companies
-- ========================================
CREATE OR REPLACE TABLE `datapm-471620.csv_processed.dim_companies` AS
SELECT DISTINCT
  ROW_NUMBER() OVER (ORDER BY company) as company_id,
  company,
  COUNT(*) OVER (PARTITION BY company) as total_job_offers,
  CURRENT_TIMESTAMP() as created_at
FROM `datapm-471620.csv_processed.jobs_unified`
WHERE company IS NOT NULL 
  AND company != ''
  AND company != 'Unknown';

-- 3. DIMENSIÓN: dim_skills
-- ========================================
CREATE OR REPLACE TABLE `datapm-471620.csv_processed.dim_skills` AS
WITH skills_exploded AS (
  SELECT DISTINCT
    TRIM(skill) as skill
  FROM `datapm-471620.csv_processed.jobs_unified`,
  UNNEST(SPLIT(skills, ';')) as skill
  WHERE skills IS NOT NULL 
    AND skills != ''
    AND TRIM(skill) != ''
)
SELECT 
  ROW_NUMBER() OVER (ORDER BY skill) as skill_id,
  skill,
  CURRENT_TIMESTAMP() as created_at
FROM skills_exploded
ORDER BY skill;

-- 4. RELACIÓN: dim_skill_job
-- ========================================
CREATE OR REPLACE TABLE `datapm-471620.csv_processed.dim_skill_job` AS
WITH job_skills AS (
  SELECT 
    f.job_id,  -- Tomar job_id directamente de la tabla de hechos
    f.job_title_short,
    TRIM(skill) as skill
  FROM `datapm-471620.csv_processed.job_offers_fact` f,
  UNNEST(SPLIT(f.skills, ';')) as skill  -- Usar skills de la tabla de hechos
  WHERE f.skills IS NOT NULL 
    AND f.skills != ''
    AND TRIM(skill) != ''
)
SELECT DISTINCT
  js.skill,
  js.job_id,
  js.job_title_short,
  ds.skill_id
FROM job_skills js
JOIN `datapm-471620.csv_processed.dim_skills` ds ON js.skill = ds.skill;

-- 5. DIMENSIÓN: dim_software
-- ========================================
CREATE OR REPLACE TABLE `datapm-471620.csv_processed.dim_software` AS
WITH software_exploded AS (
  SELECT DISTINCT
    TRIM(software_item) as software
  FROM `datapm-471620.csv_processed.jobs_unified`,
  UNNEST(SPLIT(software, ';')) as software_item
  WHERE software IS NOT NULL 
    AND software != ''
    AND TRIM(software_item) != ''
)
SELECT 
  ROW_NUMBER() OVER (ORDER BY software) as software_id,
  software,
  CURRENT_TIMESTAMP() as created_at
FROM software_exploded
ORDER BY software;

-- 6. RELACIÓN: dim_software_job
-- ========================================
CREATE OR REPLACE TABLE `datapm-471620.csv_processed.dim_software_job` AS
WITH job_software AS (
  SELECT 
    f.job_id,  -- Tomar job_id directamente de la tabla de hechos
    f.job_title_short,
    TRIM(software_item) as software
  FROM `datapm-471620.csv_processed.job_offers_fact` f,
  UNNEST(SPLIT(f.software, ';')) as software_item  -- Usar software de la tabla de hechos
  WHERE f.software IS NOT NULL 
    AND f.software != ''
    AND TRIM(software_item) != ''
)
SELECT DISTINCT
  js.software,
  js.job_id,
  js.job_title_short,
  ds.software_id
FROM job_software js
JOIN `datapm-471620.csv_processed.dim_software` ds ON js.software = ds.software;

-- 7. RELACIÓN: dim_degree_job
-- ========================================
CREATE OR REPLACE TABLE `datapm-471620.csv_processed.dim_degree_job` AS
WITH job_degrees AS (
  -- Trabajos CON títulos específicos requeridos
  SELECT 
    f.job_id,
    f.job_title_short,
    TRIM(degree_item) as degrees,
    'Yes' as has_degrees
  FROM `datapm-471620.csv_processed.job_offers_fact` f,
  UNNEST(SPLIT(f.degrees, ';')) as degree_item
  WHERE f.degrees IS NOT NULL 
    AND f.degrees != ''
    AND TRIM(degree_item) != ''
    AND f.job_title_short IS NOT NULL
    
  UNION ALL
  
  -- Trabajos SIN títulos requeridos
  SELECT 
    f.job_id,
    f.job_title_short,
    'No degree required' as degrees,
    'No' as has_degrees
  FROM `datapm-471620.csv_processed.job_offers_fact` f
  WHERE (f.degrees IS NULL OR f.degrees = '' OR TRIM(f.degrees) = '')
    AND f.job_title_short IS NOT NULL
)
SELECT DISTINCT
  degrees,
  has_degrees,
  job_id,
  job_title_short
FROM job_degrees;

-- ========================================
-- CONSULTAS DE VERIFICACIÓN
-- ========================================

-- Verificar distribución de títulos universitarios
SELECT 
  'degree_requirements_check' as test,
  has_degrees,
  COUNT(DISTINCT job_id) as unique_jobs,
  COUNT(*) as total_records
FROM `datapm-471620.csv_processed.dim_degree_job`
GROUP BY has_degrees
ORDER BY has_degrees;

-- Verificar que todos los jobs están representados en degree_job
SELECT 
  'job_coverage_check' as test,
  COUNT(DISTINCT f.job_id) as jobs_in_fact,
  COUNT(DISTINCT dj.job_id) as jobs_in_degree_relation,
  CASE 
    WHEN COUNT(DISTINCT f.job_id) = COUNT(DISTINCT dj.job_id) THEN 'PASS'
    ELSE 'FAIL - Missing jobs in degree relation'
  END as status
FROM `datapm-471620.csv_processed.job_offers_fact` f
FULL OUTER JOIN `datapm-471620.csv_processed.dim_degree_job` dj ON f.job_id = dj.job_id;

-- Verificar que los job_id coinciden entre tablas
SELECT 
  'job_id_consistency_check' as test,
  COUNT(DISTINCT f.job_id) as jobs_in_fact,
  COUNT(DISTINCT sj.job_id) as jobs_in_skill_relation,
  COUNT(DISTINCT swj.job_id) as jobs_in_software_relation,
  COUNT(DISTINCT dj.job_id) as jobs_in_degree_relation
FROM `datapm-471620.csv_processed.job_offers_fact` f
FULL OUTER JOIN `datapm-471620.csv_processed.dim_skill_job` sj ON f.job_id = sj.job_id
FULL OUTER JOIN `datapm-471620.csv_processed.dim_software_job` swj ON f.job_id = swj.job_id
FULL OUTER JOIN `datapm-471620.csv_processed.dim_degree_job` dj ON f.job_id = dj.job_id;

-- Ejemplo de job_id para verificar formato
SELECT 
  'sample_job_ids' as test,
  job_id,
  job_title_short,
  source_file
FROM `datapm-471620.csv_processed.job_offers_fact`
LIMIT 5;

-- Contar registros en cada tabla
SELECT 'job_offers_fact' as tabla, COUNT(*) as registros 
FROM `datapm-471620.csv_processed.job_offers_fact`

UNION ALL

SELECT 'dim_companies' as tabla, COUNT(*) as registros 
FROM `datapm-471620.csv_processed.dim_companies`

UNION ALL

SELECT 'dim_skills' as tabla, COUNT(*) as registros 
FROM `datapm-471620.csv_processed.dim_skills`

UNION ALL

SELECT 'dim_skill_job' as tabla, COUNT(*) as registros 
FROM `datapm-471620.csv_processed.dim_skill_job`

UNION ALL

SELECT 'dim_software' as tabla, COUNT(*) as registros 
FROM `datapm-471620.csv_processed.dim_software`

UNION ALL

SELECT 'dim_software_job' as tabla, COUNT(*) as registros 
FROM `datapm-471620.csv_processed.dim_software_job`

UNION ALL

SELECT 'dim_degree_job' as tabla, COUNT(*) as registros 
FROM `datapm-471620.csv_processed.dim_degree_job`

ORDER BY tabla;

-- ========================================
-- CONSULTAS DE ANÁLISIS EJEMPLO
-- ========================================

-- Top 10 skills más demandadas
SELECT 
  ds.skill,
  COUNT(*) as job_count,
  COUNT(DISTINCT dsj.job_title_short) as unique_job_titles
FROM `datapm-471620.csv_processed.dim_skill_job` dsj
JOIN `datapm-471620.csv_processed.dim_skills` ds ON dsj.skill_id = ds.skill_id
GROUP BY ds.skill
ORDER BY job_count DESC
LIMIT 10;

-- Top 10 software más demandado
SELECT 
  ds.software,
  COUNT(*) as job_count,
  COUNT(DISTINCT dsj.job_title_short) as unique_job_titles
FROM `datapm-471620.csv_processed.dim_software_job` dsj
JOIN `datapm-471620.csv_processed.dim_software` ds ON dsj.software_id = ds.software_id
GROUP BY ds.software
ORDER BY job_count DESC
LIMIT 10;

-- Empresas con más ofertas
SELECT 
  company,
  COUNT(*) as job_offers,
  COUNT(DISTINCT job_title_short) as unique_positions
FROM `datapm-471620.csv_processed.job_offers_fact`
WHERE company != 'Unknown'
GROUP BY company
ORDER BY job_offers DESC
LIMIT 10;
