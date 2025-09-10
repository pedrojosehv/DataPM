# Looker Studio Dashboards - DataPM

## 📊 Dashboards Implementados

### 🎯 Overview del Sistema

**Data Source**: BigQuery `datapm-471620.csv_processed`  
**Update Frequency**: Tiempo real (auto-refresh habilitado)  
**Connection**: Service Account con permisos de lectura  

## 📈 Dashboard Principal: Job Market Analysis

### 1. **Distribución de Roles**
```
Visualization: Horizontal Bar Chart
Data Source: job_offers_fact
Dimension: job_title_short
Metric: COUNT(DISTINCT job_id)
Filters: company, city, seniority
```

**Insights Obtenidos**:
- Roles más demandados en el mercado
- Concentración de ofertas por tipo de posición
- Variación por empresa y ubicación

### 2. **Análisis de Requisitos Educativos** ⭐
```
Visualization: Donut Chart + Data Table
Data Source: dim_degree_job
Dimension: has_degrees
Metric: COUNT(DISTINCT job_id)
Breakdown: degrees (when has_degrees = 'Yes')
```

**Problema Resuelto**:
- ❌ **Antes**: Todos los trabajos aparecían como "requieren título"
- ✅ **Después**: Separación clara entre trabajos CON y SIN requisitos

**Insights Actuales**:
- % de trabajos que requieren título universitario
- Tipos de títulos más solicitados
- Correlación entre seniority y requisitos educativos

### 3. **Top Skills Demandadas**
```
Visualization: Word Cloud + Ranking Table
Data Source: dim_skill_job
Dimension: skill
Metric: COUNT(DISTINCT job_id)
Filters: job_title_short, seniority
```

**Análisis Disponibles**:
- Skills más solicitadas globalmente
- Skills por tipo de rol (Frontend, Backend, Data, etc.)
- Evolución de demanda por skill

### 4. **Stack Tecnológico**
```
Visualization: Treemap + Bar Chart
Data Source: dim_software_job  
Dimension: software
Metric: COUNT(DISTINCT job_id)
Cross-filter: skills, job_title_short
```

**Insights Técnicos**:
- Tecnologías más demandadas
- Combinaciones de herramientas populares
- Stack por tipo de empresa/industria

### 5. **Análisis Geográfico**
```
Visualization: Geo Map + Table
Data Source: job_offers_fact
Dimensions: country, city
Metrics: COUNT(job_id), AVG(experience_years)
```

**Análisis Regional**:
- Concentración de ofertas por ciudad
- Requisitos de experiencia por ubicación
- Distribución de seniority geográfica

### 6. **Seniority Distribution**
```
Visualization: Stacked Column Chart
Data Source: job_offers_fact
Dimension: seniority
Metric: COUNT(job_id)
Breakdown: job_title_short
```

**Career Insights**:
- Distribución de niveles por rol
- Progresión de carrera visible
- Demanda por nivel de experiencia

## 🔧 Configuración Técnica

### Data Refresh Strategy
```
Refresh Mode: Auto
Frequency: Real-time (on data change)
Cache: Disabled
Data Freshness: < 5 minutes
```

### Performance Optimizations
- **Pre-aggregated metrics** en BigQuery views
- **Efficient filtering** usando dimensiones indexadas  
- **Partitioned queries** para fechas
- **Cached calculations** para métricas complejas

### Filter Interactions
```
Global Filters:
├── Date Range (processing_timestamp)
├── Company (multi-select)
├── Location (city/country)
├── Seniority Level
└── Job Title Category

Cross-filtering: Enabled entre todos los charts
Drill-down: job_title_short → specific requirements
```

## 📊 Métricas Clave Monitoreadas

### Volume Metrics
- **Total Job Postings**: COUNT(DISTINCT job_id)
- **Active Companies**: COUNT(DISTINCT company)  
- **Geographic Coverage**: COUNT(DISTINCT city)
- **Processing Batches**: COUNT(DISTINCT batch_number)

### Quality Metrics  
- **Data Completeness**: % fields populated
- **Unknown Values**: % "Unknown" vs valid data
- **Degree Coverage**: % jobs with degree info
- **Skills Coverage**: % jobs with skills parsed

### Business Metrics
- **Market Demand**: Jobs by title/skill trend
- **Skill Premium**: Correlation experience ↔ requirements
- **Geographic Hotspots**: City concentration analysis
- **Education ROI**: Degree requirement vs seniority

## 🎨 Visual Design

### Color Scheme
```css
Primary: #1f77b4 (Blue)
Secondary: #ff7f0e (Orange)  
Success: #2ca02c (Green)
Warning: #d62728 (Red)
Neutral: #7f7f7f (Gray)
```

### Chart Types Rationale
- **Bar Charts**: Categorical comparisons (roles, skills)
- **Donut Charts**: Part-to-whole (degree requirements)
- **Treemaps**: Hierarchical data (tech stack)
- **Geo Maps**: Location-based analysis
- **Line Charts**: Trends over time (future: temporal analysis)

## 🚀 Dashboard URLs

### Production Dashboards
- **Main Dashboard**: [DataPM Job Market Analysis](https://lookerstudio.google.com/reporting/b55a0154-496b-4c8e-89b7-2ee31318d0d4)
- **Live Dashboard URL**: `https://lookerstudio.google.com/reporting/b55a0154-496b-4c8e-89b7-2ee31318d0d4`

### Sharing & Access
- **View Access**: Anyone with link (read-only)
- **Edit Access**: Owner account only
- **Embed**: Available for external websites
- **PDF Export**: Automated weekly reports

## 🔄 Update Workflow

### Automatic Pipeline
```
1. New CSV processed → GCS upload
2. BigQuery external table detects file  
3. Views refresh automatically
4. Looker Studio pulls latest data
5. Dashboard updates in real-time
```

### Manual Interventions
- **Schema changes**: Require view updates
- **New dimensions**: May need chart modifications
- **Filter additions**: Dashboard configuration updates

## 📈 Future Enhancements

### Planned Features
- [ ] **Time series analysis** (job posting trends)
- [ ] **Salary correlation** (when salary data available)
- [ ] **Company comparison** detailed views
- [ ] **Skills gap analysis** (supply vs demand)
- [ ] **Automated alerts** for significant changes

### Technical Improvements
- [ ] **Mobile optimization** for dashboard viewing
- [ ] **API integration** for external data sources
- [ ] **Advanced filtering** with custom parameters
- [ ] **Export capabilities** to Excel/PDF

---

**Dashboard Status**: ✅ Live in Production  
**Data Quality**: 95%+ completeness  
**Update Latency**: < 5 minutes  
**User Access**: Stakeholder ready
