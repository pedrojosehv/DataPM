```markdown
1. Ingesta de datos (CSV)
   - Entrada: CSV con columnas `title, company, location, description` (p. ej. `csv/src/scrapped/*.csv` o `csv/linkedin_jobs_make.csv`).
   - Si se llama con `latest`, el programa toma el CSV más reciente de `csv/src/scrapped/`.
   - Detección: `csv_engine/engines/datapm_processor.py -> read_csv()`.

2. Configuración del LLM y prompts
   - LLM por defecto: Gemini (modelo `gemini-2.0-flash-exp`). Alternativa: Ollama (`llama3.2:3b`).
   - API Key Gemini requerida vía `--api-key` o `GEMINI_API_KEY`.
   - Prompts (system + user) construidos desde `csv_engine/utils/config.py` y `datapm_processor.py`:
     - System (resumen): extractor estricto que devuelve SOLO JSON con los campos: job_title_original, job_title_short, experience_years, job_schedule_type, seniority, city, state, country, degrees[], skills[], software[], company_name.
     - User: `INPUT: {"text":"<description>"}` + `TASK: ... return the JSON according to the schema`.

3. Extracción con LLM por lotes
   - Procesamiento en lotes de 10 filas: `run()` divide, `process_data()` itera y llama a `process_description()`.
   - Manejo de errores y rate limiting:
     - Gemini: reintentos con backoff leyendo `retry_delay` del error (cód. 429).
     - Validación: si la respuesta es inválida (todo Unknown), reintenta una vez.
     - Pausa entre filas (Gemini): 5s (ajustable en código).

4. Normalización post-LLM
   - Segunda pasada de normalización de títulos (si disponible): `csv_engine/normalization/title_normalizer.py`.
   - Objetivo: reducir “Unknown” y mapear variantes a la taxonomía definida en `config.py`.

5. Persistencia incremental
   - Cada lote procesado se guarda en `csv/src/csv_processed/<timestamp>_DataPM_result_batch_<n>.csv`.
   - Escritura CSV con encabezados y codificación UTF-8.

6. Salida final y monitoreo
   - Los archivos por lote son el output oficial para BI/Power BI.
   - Logs de deduplicación y transformaciones auxiliares en `csv/src/logs/` y `csv/src/archive/`.
```
