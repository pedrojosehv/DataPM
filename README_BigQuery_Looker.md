# DataPM - Pipeline de Análisis de Ofertas de Trabajo

## 🏗️ Arquitectura del Proyecto

Este proyecto implementa un pipeline completo de análisis de ofertas de trabajo que va desde el procesamiento de descripciones con LLM hasta visualizaciones automáticas en Looker Studio.

### 📊 Flujo de Datos

```
CSV Local → Python + LLM → Google Cloud Storage → BigQuery → Looker Studio
```

## 🗃️ Modelo Dimensional en BigQuery

### Dataset: `datapm-471620.csv_processed`

#### 📋 Tabla de Hechos Principal
- **`job_offers_fact`** - Tabla central con información de ofertas de trabajo
  - `job_id` (INT64) - Identificador único secuencial
  - `job_title_long` (STRING) - Título completo original
  - `job_title_short` (STRING) - Título normalizado
  - `company` (STRING) - Empresa
  - `city` (STRING) - Ciudad
  - `country` (STRING) - País
  - `schedule_type` (STRING) - Tipo de horario
  - `experience_years` (STRING) - Años de experiencia requeridos
  - `seniority` (STRING) - Nivel de seniority
  - `skills` (STRING) - Habilidades requeridas (separadas por ;)
  - `degrees` (STRING) - Títulos universitarios requeridos (separados por ;)
  - `software` (STRING) - Software requerido (separado por ;)

#### 🏢 Tablas de Dimensiones
- **`dim_companies`** - Catálogo de empresas
- **`dim_skills`** - Catálogo de habilidades
- **`dim_software`** - Catálogo de software y herramientas

#### 🔗 Tablas de Relaciones (Many-to-Many)
- **`dim_skill_job`** - Relación entre trabajos y habilidades
- **`dim_software_job`** - Relación entre trabajos y software
- **`dim_degree_job`** - Relación entre trabajos y títulos universitarios

## 🎯 Características Técnicas Implementadas

### ✅ Actualización Automática
- **External Tables** conectadas a Google Cloud Storage
- **Wildcard patterns** para inclusión automática de nuevos archivos
- **Schema auto-detection** para flexibilidad en la estructura

### ✅ Modelo Estrella Completo
- Tabla de hechos central optimizada para análisis
- Dimensiones normalizadas para evitar redundancia
- Relaciones many-to-many manejadas correctamente

### ✅ Calidad de Datos
- **Job IDs consistentes** entre todas las tablas
- **Manejo de valores NULL** y campos vacíos
- **Validaciones de integridad** incluidas en el código SQL

## 📈 Dashboards en Looker Studio

### 🔍 Análisis Implementados

#### 1. **Distribución de Roles por Título**
- Gráfico de barras mostrando los roles más demandados
- Filtros por empresa, ubicación y seniority

#### 2. **Requisitos Educativos**
- **Problema identificado y corregido**: Inicialmente todos los trabajos aparecían como "requieren título"
- **Solución**: Separación explícita entre trabajos CON y SIN requisitos universitarios
- Distribución porcentual de trabajos que requieren vs no requieren títulos

#### 3. **Análisis de Habilidades**
- Top skills más demandadas
- Correlación entre habilidades y nivel de seniority
- Análisis por industria/empresa

#### 4. **Tecnologías y Software**
- Stack tecnológico más solicitado
- Tendencias de herramientas por tipo de rol
- Análisis de combinaciones de tecnologías

#### 5. **Análisis Geográfico**
- Distribución de ofertas por ciudad/país
- Análisis de seniority por ubicación
- Comparativa de requisitos por región

### 🔄 Actualización Automática
Los dashboards se actualizan automáticamente cuando:
1. Se procesan nuevos archivos CSV con el pipeline Python
2. Los archivos se suben a Google Cloud Storage
3. BigQuery detecta automáticamente los nuevos datos
4. Looker Studio refleja los cambios en tiempo real

## 🛠️ Implementación Técnica

### Google Cloud Storage
```
gs://datapm/
├── unified_processed/          # CSVs procesados (entrada a BigQuery)
└── raw/                       # Archivos originales por categoría
```

### BigQuery External Tables
```sql
CREATE OR REPLACE EXTERNAL TABLE `datapm-471620.csv_processed.jobs_external`
OPTIONS (
  format = 'CSV',
  uris = ['gs://datapm/unified_processed/*.csv'],
  allow_jagged_rows = true,
  skip_leading_rows = 1
);
```

### Looker Studio Connection
- **Data Source**: BigQuery
- **Connection Type**: Service Account
- **Auto-refresh**: Enabled
- **Cache**: Disabled para datos en tiempo real

## 📊 Métricas de Calidad

### Cobertura de Datos
- ✅ **100% de trabajos** representados en todas las tablas de relación
- ✅ **Consistencia de job_id** verificada entre tablas
- ✅ **Manejo correcto** de trabajos sin requisitos universitarios

### Performance
- ⚡ **External tables** para acceso directo desde GCS
- ⚡ **Índices implícitos** en job_id para JOINs rápidos
- ⚡ **Particionamiento automático** por fecha de procesamiento

## 🔍 Consultas de Verificación

El modelo incluye consultas automáticas de verificación:

```sql
-- Verificar distribución de títulos universitarios
SELECT has_degrees, COUNT(DISTINCT job_id) as unique_jobs
FROM dim_degree_job GROUP BY has_degrees;

-- Verificar consistencia de job_id
SELECT COUNT(DISTINCT f.job_id) as jobs_in_fact,
       COUNT(DISTINCT dj.job_id) as jobs_in_relations
FROM job_offers_fact f
FULL OUTER JOIN dim_degree_job dj ON f.job_id = dj.job_id;
```

## 🚀 Escalabilidad

### Preparado para Crecimiento
- **Wildcard patterns** permiten agregar archivos sin modificar código
- **Schema flexible** se adapta a nuevas columnas automáticamente  
- **Modelo dimensional** optimizado para análisis complejos
- **Looker Studio** maneja grandes volúmenes de datos eficientemente

## 🔗 Enlaces Importantes

### 📊 Dashboard en Producción
**[Ver Dashboard en Looker Studio](https://lookerstudio.google.com/reporting/b55a0154-496b-4c8e-89b7-2ee31318d0d4)**

### 🗃️ Recursos BigQuery
- **Dataset**: `datapm-471620.csv_processed`
- **External Tables**: Conectadas a `gs://datapm/unified_processed/*.csv`
- **Auto-refresh**: Habilitado para actualizaciones en tiempo real

---

**Autor**: Pedro José  
**Fecha**: Septiembre 2024  
**Tecnologías**: Python, Google Cloud Storage, BigQuery, Looker Studio, LLM (Gemini)  
**Dashboard Live**: [lookerstudio.google.com/reporting/b55a0154-496b-4c8e-89b7-2ee31318d0d4](https://lookerstudio.google.com/reporting/b55a0154-496b-4c8e-89b7-2ee31318d0d4)
