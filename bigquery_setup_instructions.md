# Configuración Automática de BigQuery para DataPM

## 🎯 Objetivo
Crear una tabla externa que automáticamente lea todos los CSVs de `gs://datapm/processed/` y se actualice cada vez que agregues nuevos archivos.

## 📋 Pasos a seguir:

### 1. Abrir BigQuery Console
- Ve a: https://console.cloud.google.com/bigquery
- Asegúrate de estar en el proyecto `datapm-471620`

### 2. Crear Dataset (si no existe)
```sql
CREATE SCHEMA IF NOT EXISTS `datapm-471620.csv_processed`
OPTIONS (
  location = 'us'
);
```

### 3. Crear Tabla Externa Automática
```sql
CREATE OR REPLACE EXTERNAL TABLE `datapm-471620.csv_processed.processed_jobs`
OPTIONS (
  format = 'CSV',
  uris = ['gs://datapm/unified_processed/*.csv'],
  skip_leading_rows = 1,
  allow_jagged_rows = true,
  allow_quoted_newlines = true,
  max_bad_records = 100
);
```

### 4. Crear Vista Limpia para Consultas
```sql
CREATE OR REPLACE VIEW `datapm-471620.csv_processed.jobs_unified` AS
SELECT 
  _FILE_NAME as source_file,
  REGEXP_EXTRACT(_FILE_NAME, r'(\d{8}_\d{6})') as processing_timestamp,
  CAST(REGEXP_EXTRACT(_FILE_NAME, r'batch_(\d+)') AS INT64) as batch_number,
  
  -- Información del trabajo
  string_field_0 as job_title_original,
  IFNULL(string_field_1, '') as job_title_short, 
  IFNULL(string_field_2, '') as company,
  
  -- Ubicación
  IFNULL(string_field_3, '') as country,
  IFNULL(string_field_4, '') as state,
  IFNULL(string_field_5, '') as city,
  
  -- Detalles del trabajo
  IFNULL(string_field_6, '') as schedule_type,
  IFNULL(string_field_7, '') as experience_years,
  IFNULL(string_field_8, '') as seniority,
  
  -- Habilidades y requisitos (pueden estar vacías)
  IFNULL(string_field_9, '') as skills,
  IFNULL(string_field_10, '') as degrees,
  IFNULL(string_field_11, '') as software,
  
  CURRENT_TIMESTAMP() as last_updated
  
FROM `datapm-471620.csv_processed.processed_jobs`
WHERE string_field_0 IS NOT NULL 
  AND string_field_0 != ''
  AND string_field_0 != 'Job title (original)';
```

### 5. Query de Prueba
```sql
SELECT 
  COUNT(*) as total_jobs,
  COUNT(DISTINCT company) as unique_companies,
  COUNT(DISTINCT job_title_short) as unique_job_titles,
  COUNT(DISTINCT source_file) as total_files
FROM `datapm-471620.csv_processed.jobs_unified`;
```

## ✅ Ventajas de este Enfoque:

1. **Automático**: Cualquier CSV que subas a `gs://datapm/processed/` aparecerá automáticamente
2. **Sin límites**: No hay límite de archivos o tamaño (dentro de los límites de BigQuery)
3. **Tiempo Real**: Los cambios se reflejan inmediatamente
4. **Sin costos extra**: Solo pagas por las consultas que hagas
5. **Escalable**: Puede manejar miles de archivos

## 🔄 Flujo de Trabajo:
1. Subes nuevos CSVs a `gs://datapm/unified_processed/`
2. BigQuery automáticamente los incluye en la tabla
3. Consultas `jobs_unified` para ver todos los datos unificados
4. ¡Listo para análisis!

## 📊 Consultas Útiles:

### Ver archivos más recientes:
```sql
SELECT DISTINCT source_file, processing_timestamp
FROM `datapm-471620.csv_processed.jobs_unified`
ORDER BY processing_timestamp DESC
LIMIT 10;
```

### Contar jobs por fecha:
```sql
SELECT 
  processing_timestamp,
  COUNT(*) as jobs_count
FROM `datapm-471620.csv_processed.jobs_unified`
GROUP BY processing_timestamp
ORDER BY processing_timestamp DESC;
```

### Top companies:
```sql
SELECT 
  company,
  COUNT(*) as job_count
FROM `datapm-471620.csv_processed.jobs_unified`
WHERE company != 'Unknown'
GROUP BY company
ORDER BY job_count DESC
LIMIT 20;
```
