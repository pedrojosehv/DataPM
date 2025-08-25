# DataPM Scrapped Deduplication Processor

## 🚀 Descripción

Este programa está optimizado para eliminar duplicados de archivos CSV en la carpeta `scrapped` antes de procesarlos con Gemini, evitando así el gasto innecesario de tokens en registros duplicados.

## 🎯 Objetivos

- **Eliminar duplicados antes del procesamiento con LLM**: Reduce costos al evitar procesar registros idénticos
- **Validación completa de campos**: Compara TODOS los campos de cada fila para identificar duplicados exactos
- **Procesamiento del archivo más reciente**: Solo procesa el archivo CSV más reciente en la carpeta scrapped
- **Optimización de recursos**: Ahorra tokens de Gemini al limpiar datos antes del procesamiento

## 📁 Estructura de Directorios

```
D:\Work Work\Upwork\DataPM\
├── csv/
│   └── src/
│       ├── scrapped/           # 📥 Archivos CSV originales del scraper
│       └── scrapped_deduplicated/  # 📤 Archivos deduplicados (salida)
└── csv_engine/
    └── engines/
        ├── deduplication_processor.py  # 🧹 Programa principal
        └── run_scrapped_deduplication.py  # 🚀 Script de ejecución
```

## 🔧 Funcionamiento

### Validación de Duplicados

El programa valida duplicados comparando **TODOS los campos** de cada fila:
- `title` (título del trabajo)
- `company` (empresa)
- `location` (ubicación)
- `description` (descripción completa)

Dos registros se consideran duplicados si **todos los campos son idénticos**.

### Procesamiento

1. **Identifica el archivo más reciente** en `csv/src/scrapped/`
2. **Carga y analiza** todos los registros
3. **Genera hash signatures** basadas en todos los campos
4. **Identifica duplicados exactos** mediante comparación de hashes
5. **Guarda archivo deduplicado** en `csv/src/scrapped_deduplicated/`
6. **Guarda archivo de duplicados** para revisión (si existen)

## 🚀 Uso

### Opción 1: Script Automático (Recomendado)

```bash
python csv_engine/engines/run_scrapped_deduplication.py
```

### Opción 2: Ejecución Directa

```bash
# Procesar solo el archivo más reciente (default)
python csv_engine/engines/deduplication_processor.py --mode latest

# Procesar todos los archivos (modo legacy)
python csv_engine/engines/deduplication_processor.py --mode all

# Especificar directorio personalizado
python csv_engine/engines/deduplication_processor.py --scrapped-dir "D:/custom/path"
```

## 📊 Salida

### Archivos Generados

1. **`deduplicated_{timestamp}_{original_filename}.csv`**
   - Archivo limpio sin duplicados
   - Listo para procesamiento con DataPM processor

2. **`duplicates_{timestamp}_{original_filename}.csv`** (solo si hay duplicados)
   - Registros identificados como duplicados
   - Para revisión manual si es necesario

### Reporte en Consola

```
🧹 DataPM Scrapped Deduplication Processor
==================================================
📂 Working directory: D:/Work Work/Upwork/DataPM/csv/src/scrapped
📁 Processing latest file: 20250820_154912_linkedin_jobs.csv
📅 Modified: 2025-08-20 15:49:12
📊 Original records: 50
🔍 Duplicate Analysis:
   Total records: 50
   Key fields used: title, company, location
   Duplicate combinations: 3
   Duplicate records: 8

✅ Processing completed!
📁 Output file: D:/Work Work/Upwork/DataPM/csv/src/scrapped_deduplicated/deduplicated_20250820_154912_linkedin_jobs.csv
📁 Duplicates file: D:/Work Work/Upwork/DataPM/csv/src/scrapped_deduplicated/duplicates_20250820_154912_linkedin_jobs.csv
📊 Results:
   Original records: 50
   Final records: 42
   Duplicates removed: 8
   Reduction: 16.00%
```

## 💡 Beneficios

### Antes del Procesamiento con Gemini
- ✅ **Ahorro de tokens**: No procesar registros duplicados
- ✅ **Tiempo reducido**: Menos registros = procesamiento más rápido
- ✅ **Mejor calidad**: Datos limpios desde el inicio

### Comparación de Costos

**Sin deduplicación:**
- 50 registros × costo por registro = Costo Total

**Con deduplicación:**
- 42 registros únicos × costo por registro = Costo Reducido
- **Ahorro: 16%** (en el ejemplo anterior)

## 🔄 Flujo de Trabajo Recomendado

1. **Ejecutar scraper** → Genera CSV en `scrapped/`
2. **Ejecutar deduplicación** → Genera CSV limpio en `scrapped_deduplicated/`
3. **Ejecutar DataPM processor** → Procesa solo registros únicos

## ⚙️ Configuración

### Parámetros por Defecto

```python
DEFAULT_SCRAPPED_DIR = "D:/Work Work/Upwork/DataPM/csv/src/scrapped"
DEFAULT_MODE = "latest"  # Solo archivo más reciente
```

### Personalización

Modifica estos valores en `deduplication_processor.py`:
- `scrapped_dir`: Directorio de entrada
- `output_dir`: Directorio de salida

## 🚨 Consideraciones

- **Archivos grandes**: Para archivos muy grandes (>1000 registros), el procesamiento puede tardar varios minutos
- **Memoria**: Asegúrate de tener suficiente RAM para archivos grandes
- **Backup**: Los archivos originales en `scrapped/` no se modifican
- **Reversibilidad**: Puedes revisar los duplicados eliminados en el archivo `duplicates_*.csv`

## 🆘 Solución de Problemas

### Error: "No CSV files found"
- Verifica que existan archivos `.csv` en la carpeta `scrapped/`
- Revisa los permisos de lectura del directorio

### Error: "Permission denied"
- Asegúrate de tener permisos de escritura en `scrapped_deduplicated/`
- Cierra archivos CSV que puedan estar abiertos

### Advertencia: "No duplicates found"
- Es normal si el scraper ya genera datos únicos
- No afecta el funcionamiento del sistema

## 📈 Métricas de Rendimiento

El programa reporta automáticamente:
- **Registros originales**: Total de registros en el archivo
- **Registros finales**: Registros únicos después de deduplicación
- **Duplicados eliminados**: Número absoluto de registros duplicados
- **Porcentaje de reducción**: Eficiencia de la deduplicación

---

**💡 Recomendación**: Ejecuta este programa **antes** de procesar con DataPM para optimizar el uso de tokens de Gemini.

