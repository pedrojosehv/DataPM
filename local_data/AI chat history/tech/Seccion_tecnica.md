## 1) Dependencias exactas (versiones sugeridas)
- Python 3.10–3.13
- Paquetes Python (requirements.txt):
  - google-generativeai>=0.8.0
  - requests>=2.31.0
  - pandas>=2.2.2 (usado en normalización post-proceso)

## 2) Comandos para ejecutar
1. Activar entorno (Windows PowerShell):
   - `& env\Scripts\Activate.ps1`
2. Instalar dependencias:
   - `pip install -r requirements.txt`
3. Ejecutar pipeline (Gemini):
   - `python csv_engine/engines/datapm_processor.py latest --llm gemini --api-key YOUR_GEMINI_KEY`
   - También: `python csv_engine/engines/datapm_processor.py csv/src/scrapped/20250818_132611_linkedin_jobs.csv --llm gemini --api-key YOUR_GEMINI_KEY`
4. Ejecutar pipeline (Ollama, opcional):
   - Iniciar servidor: `ollama serve`
   - Ejemplo: `python csv_engine/engines/datapm_processor.py latest --llm ollama`

## 3) Estructura de carpetas (relevante)
- `csv_engine/`
  - `engines/datapm_processor.py` (motor principal por lotes, manejo de rate limiting)
  - `utils/config.py` (taxonomías, prompts, rutas)
  - `normalization/title_normalizer.py` (normalización adicional de títulos)
  - `tests/*.py` (tests puntuales)
- `csv/src/scrapped/*.csv` (CSV de entrada más recientes)
- `csv/src/csv_processed/*.csv` (salidas por lote: `<timestamp>_DataPM_result_batch_<n>.csv`)
- `csv/src/archive/*` (histórico de resultados)

## 4) Muestras de prompts (producción)
- System prompt (extracto real):
  """
  You are a strict data extractor and standardizer. You MUST return ONLY a valid JSON object and nothing else.
  The JSON must follow this schema:
  job_title_original (string)
  job_title_short (one of: [Product Manager, Data Analyst, ...])
  experience_years ("0-3" | "3-5" | "5+")
  job_schedule_type (one of: [Full-time, Part-time, Contract, Internship, Unknown])
  seniority (one of: [Intern, Junior, Mid, Senior, Lead, Manager, Unknown])
  city, state, country, degrees[], skills[], software[], company_name
  If you cannot determine a value, use "Unknown" for strings and keep arrays empty. No extra text.
  """

- User prompt:
  """
  INPUT: {"text":"<DESCRIPTION_FROM_CSV>"}
  TASK: Analyze INPUT.text and return the JSON according to the schema in the system instructions.
  """

## 5) Manejo de errores y rate limiting
- Reintentos (Gemini): hasta 5 intentos si aparece 429/quota/rate, con backoff leyendo `retry_delay` del propio error; espera por defecto 60s si no hay `retry_delay`.
- Validación de respuesta: si la respuesta es inválida (todos los campos Unknown), se reintenta 1 vez adicional para esa fila.
- Pausa entre filas (Gemini): 5s (ajustable).
- Persistencia por lotes: cada 10 filas se escribe un CSV parcial; si hay fallo, no se pierde el progreso previo.

## 6) Tests y cómo replicarlos
- Tests disponibles en `csv_engine/tests/` (p. ej. `test_processor.py`, `gpt2_test.py`).
- Ejecución sugerida:
  - `python -m pytest csv_engine/tests -q` (si se usa pytest) o ejecutar directamente scripts de test.
- Pruebas manuales:
  - Crear un CSV pequeño: `linkedin_jobs_detailed_head5.csv`.
  - Ejecutar: `python csv_engine/engines/datapm_processor.py linkedin_jobs_detailed_head5.csv --llm gemini --api-key YOUR_KEY`.

## 7) Ejemplos de entrada y salida
- Entrada (1 registro, CSV):
  ```csv
  title,company,location,description
  Product Designer,Acme Inc.,Madrid, Spain,"We are hiring a Product Designer with strong Figma and UX research skills..."
  ```
- Salida (JSON extraído por LLM; un registro):
  ```json
  {
    "job_title_original": "Product Designer",
    "job_title_short": "Product Designer",
    "experience_years": "3-5",
    "job_schedule_type": "Full-time",
    "seniority": "Mid",
    "city": "Madrid",
    "state": "Unknown",
    "country": "Spain",
    "degrees": ["Bachelor's Degree"],
    "skills": ["UI/UX Design", "User Research", "Design Systems"],
    "software": ["Figma"],
    "company_name": "Acme Inc."
  }
  ```
- Salida (CSV final, columnas clave):
  ```csv
  Job title (original),Job title (short),Company,Country,State,City,Schedule type,Experience years,Seniority,Skills,Degrees,Software
  Product Designer,Product Designer,Acme Inc.,Spain,Unknown,Madrid,Full-time,3-5,Mid,"UI/UX Design; User Research; Design Systems","Bachelor's Degree","Figma"
  ```

## 8) Métricas observadas
- nº registros procesados: Métrica no disponible (varía por archivo; ver `csv/src/csv_processed/*`).
- % Unknowns antes/después: Métrica no disponible (depende del dataset y del normalizador en `title_normalizer.py`).

## 9) Recomendaciones de mejoras
1. Añadir soporte nativo a Anthropic Claude como tercer LLM para reducir rate limiting.
2. Persistencia de estado entre lotes con reporte de métricas (nº unknowns por campo, % normalizaciones exitosas).
3. Cache de resultados por hash de descripción para evitar reprocesar descripciones idénticas.
4. Añadir `--max-concurrency` y colas internas con back-pressure para Gemini.
5. Validación JSON con esquema pydantic antes de escribir el CSV.
6. Añadir CLI para reintentar únicamente filas fallidas (`--retry-failed`).
```
