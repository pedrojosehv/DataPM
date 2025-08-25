Transformamos descripciones de empleo en datos listos para BI con un pipeline robusto y trazable. Diseñamos un flujo por lotes (persistencia cada 10 filas) que integra extracción semántica con LLM (Gemini) y una segunda pasada de normalización para reducir “Unknowns”. El sistema aplica reintentos inteligentes y backoff ante rate limiting, y guarda resultados incrementales para no perder progreso.

¿Qué aporta? Velocidad de análisis, consistencia en taxonomías (roles, skills, software) y archivos CSV limpios para su consumo directo en Power BI. En producción soporta ajustes dinámicos (modelo, claves, directorios) y cuenta con scripts auxiliares para depurar y normalizar títulos. Métricas clave como nº de registros procesados o % de “Unknowns” antes/después dependen del dataset (Métrica no disponible en este comunicado), pero la arquitectura está preparada para auditarlas por lote.

Una lección clave: los prompts importan. Al imponer JSON estricto y listas de valores destino, la calidad de la extracción mejora notablemente. El procesamiento incremental y los reintentos granulares elevan la resiliencia del sistema.

¿Le interesa explorar un pipeline similar para su organización o evaluar migración a otro LLM (p. ej., Claude) para ampliar capacidad sin afectar costos? Contácteme para una demostración técnica y hojas de ruta de adopción. Podemos adaptar el flujo a sus fuentes de datos, su taxonomía interna y sus KPIs de talento.

#DataEngineering #LLM #AI #ProductAnalytics #PeopleAnalytics #ETL #Gemini #Ollama #Python #PowerBI
