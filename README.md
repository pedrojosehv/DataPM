## DataPM Processor (LLM Extraction & Normalization)

Run the processor to transform a jobs CSV into the standardized output while writing JSONL audit logs.

### Setup
- Python 3.9+
- Optional: `pip install google-generativeai requests pandas`

Environment variables (optional):
- `GEMINI_API_KEY`: required when using Gemini
- `OLLAMA_URL`: override Ollama endpoint (default `http://localhost:11434`)

### Run
Example:
```bash
python -m csv_engine.engines.datapm_processor <path_or_latest> --llm gemini --api-key $GEMINI_API_KEY
```

Output CSV files are written to `csv/src/csv_processed/` with the exact header:
[`Job title (original)`,`Job title (short)`,`Company`,`Country`,`State`,`City`,`Schedule type`,`Experience years`,`Seniority`,`Skills`,`Degrees`,`Software`]

Audit logs (JSON Lines) are written to `logs/datapm_mappings.jsonl`.

### Tests
Install test deps (pytest):
```bash
pip install pytest
pytest -q
```

### Sample Logs
See `examples/output_sample.jsonl` for 3 sample entries.

# DataPM Processor

🚀 **Replica la automatización de Make.com para análisis de descripciones de trabajo**

Este programa convierte tu blueprint de Make.com en una aplicación Python que:
- ✅ Lee archivos CSV locales (no necesita Google Drive)
- ✅ Usa Google Gemini o Ollama para análisis de LLM
- ✅ Produce CSV limpio y estructurado igual que Make.com
- ✅ Normaliza datos según el mismo schema que tu automatización

## 📋 Características

- **Compatibilidad total** con tu blueprint de Make.com
- **Múltiples LLMs**: Google Gemini y Ollama
- **Mismo schema de normalización** que tu automatización original
- **Procesamiento por lotes** con manejo de errores
- **CSV de salida limpio** listo para análisis y visualización

## 🛠️ Instalación

### 1. Clonar o descargar el proyecto
```bash
# Si tienes git
git clone <tu-repositorio>
cd DataPM

# O simplemente descarga los archivos
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar API Keys (solo para Gemini)

#### Opción A: Variable de entorno
```bash
# Windows
set GEMINI_API_KEY=tu_api_key_aqui

# Linux/Mac
export GEMINI_API_KEY=tu_api_key_aqui
```

#### Opción B: Proporcionar al ejecutar
El programa te pedirá la API key cuando la necesite.

## 🚀 Uso

### Método 1: Script interactivo (Recomendado para principiantes)

```bash
python run_datapm.py
```

Sigue las instrucciones en pantalla para:
1. Seleccionar el LLM (Gemini u Ollama)
2. Configurar las credenciales
3. Ejecutar el procesamiento

### Método 2: Línea de comandos (Para usuarios avanzados)

#### Con Google Gemini
```bash
python datapm_processor.py csv/linkedin_jobs_make.csv --llm gemini --api-key TU_API_KEY
```

#### Con Ollama
```bash
# Asegúrate de que Ollama esté corriendo
python datapm_processor.py csv/linkedin_jobs_make.csv --llm ollama
```

#### Opciones disponibles
```bash
python datapm_processor.py --help
```

**Opciones:**
- `input_file`: Archivo CSV de entrada (requerido)
- `--output, -o`: Archivo CSV de salida (opcional)
- `--llm`: Tipo de LLM: `gemini` o `ollama` (default: gemini)
- `--api-key`: API key para Gemini (requerido si --llm=gemini)
- `--ollama-url`: URL del servidor Ollama (default: http://localhost:11434)

### Método 3: Como módulo Python

```python
from datapm_processor import DataPMProcessor

# Configurar procesador
processor = DataPMProcessor(
    llm_type="gemini",
    api_key="tu_api_key_aqui"
)

# Ejecutar procesamiento
processor.run("csv/linkedin_jobs_make.csv", "resultado.csv")
```

## 📊 Formato de Datos

### Entrada (CSV)
El programa espera un CSV con estas columnas:
```csv
title,company,location,description
"Product Designer","Revolut","Spain","About the job..."
```

### Salida (CSV)
El programa genera un CSV con estas columnas normalizadas:
```csv
Job title (original),Job title (short),Company,Country,State,City,Schedule type,Experience years,Seniority,Skills,Degrees,Software
"Product Designer","Product Designer","Revolut","Spain","Unknown","Unknown","Full-time","0-3","Junior","UI/UX Design; Product Design","Bachelor's Degree","Figma; Adobe XD"
```

## 🔧 Configuración de LLMs

### Google Gemini
1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una nueva API key
3. Usa la API key en el programa

### Ollama
1. Instala Ollama desde [ollama.ai](https://ollama.ai)
2. Descarga un modelo: `ollama pull llama3.2:3b`
3. Inicia el servidor: `ollama serve`
4. El programa se conectará automáticamente

## 📁 Estructura de Archivos

```
DataPM/
├── datapm_processor.py      # Programa principal
├── run_datapm.py           # Script interactivo
├── requirements.txt        # Dependencias
├── README.md              # Este archivo
├── csv/
│   ├── linkedin_jobs_make.csv    # Archivo de entrada
│   └── archive/                  # Resultados generados
└── DataPM.blueprint.json   # Tu blueprint original
```

## 🎯 Schema de Normalización

El programa usa exactamente el mismo schema que tu automatización de Make.com:

### Títulos de trabajo normalizados:
- Product Manager, Data Analyst, Data Scientist, Data Engineer
- UX/UI Designer, Software Engineer, Marketing Specialist
- Project Manager, Business Analyst, Process Designer
- Product Compliance Specialist, Product Designer, IT Analyst
- Machine Learning Engineer, DevOps Engineer, Other

### Experiencia:
- "0-3" (menos de 3 años)
- "3-5" (3-5 años)
- "5+" (5 o más años)

### Tipos de trabajo:
- Full-time, Part-time, Contract, Internship, Unknown

### Seniority:
- Intern, Junior, Mid, Senior, Lead, Manager, Unknown

### Y muchos más campos normalizados...

## 🔍 Ejemplos de Uso

### Procesar un archivo específico
```bash
python datapm_processor.py mi_archivo.csv --output resultado.csv
```

### Usar Ollama con URL personalizada
```bash
python datapm_processor.py datos.csv --llm ollama --ollama-url http://192.168.1.100:11434
```

### Procesar con Gemini usando variable de entorno
```bash
export GEMINI_API_KEY=tu_key
python datapm_processor.py datos.csv --llm gemini
```

## 🐛 Solución de Problemas

### Error: "Google Gemini no disponible"
```bash
pip install google-generativeai
```

### Error: "Requests no disponible"
```bash
pip install requests
```

### Error: "API key requerida para Gemini"
- Obtén tu API key en: https://makersuite.google.com/app/apikey
- Configúrala como variable de entorno o proporciónala al ejecutar

### Error: "Archivo no encontrado"
- Verifica que el archivo CSV esté en la ubicación correcta
- Usa rutas absolutas si es necesario

### Ollama no responde
- Verifica que Ollama esté corriendo: `ollama serve`
- Comprueba la URL: `curl http://localhost:11434/api/tags`

## 📈 Comparación con Make.com

| Característica | Make.com | DataPM Processor |
|---|---|---|
| **Fuente de datos** | Google Drive | Archivo local |
| **LLM** | Gemini | Gemini + Ollama |
| **Costo** | Créditos Make.com | Solo API calls |
| **Velocidad** | Limitada por Make.com | Solo limitada por LLM |
| **Personalización** | Limitada | Completa |
| **Offline** | No | Sí (con Ollama) |

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Si tienes problemas:
1. Revisa la sección de solución de problemas
2. Verifica que todas las dependencias estén instaladas
3. Comprueba que tu API key sea válida
4. Abre un issue en el repositorio

---

**¡Disfruta procesando tus datos de trabajo! 🎉**
