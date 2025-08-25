# DataPM Processor - Versión Ollama

🚀 **Versión local del procesador de descripciones de trabajo usando Ollama**

Esta versión del programa usa Ollama (LLM local) en lugar de Google Gemini, eliminando completamente los límites de rate limiting y permitiendo procesamiento ilimitado.

## 🎯 **Ventajas de la versión Ollama:**

- ✅ **Sin límites de rate limiting** - Procesa tantos registros como quieras
- ✅ **Completamente local** - No necesitas API keys ni conexión a internet
- ✅ **Mismo schema y prompts** - Compatibilidad total con la versión Gemini
- ✅ **Múltiples modelos** - Usa cualquier modelo disponible en Ollama
- ✅ **Procesamiento más rápido** - Sin pausas por rate limiting

## 📋 **Requisitos:**

### 1. **Instalar Ollama**
```bash
# Windows (PowerShell)
winget install Ollama.Ollama

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. **Instalar dependencias Python**
```bash
pip install requests
```

### 3. **Descargar un modelo**
```bash
# Modelo recomendado (3B parámetros, rápido)
ollama pull llama3.2:3b

# Modelo más potente (7B parámetros, más lento)
ollama pull llama3.2:7b

# Modelo especializado en código
ollama pull codellama:7b
```

## 🚀 **Uso:**

### **Uso básico:**
```bash
python datapm_processor_ollama.py linkedin_jobs_detailed.csv
```

### **Especificar modelo:**
```bash
python datapm_processor_ollama.py linkedin_jobs_detailed.csv --model llama3.2:7b
```

### **Especificar URL de Ollama:**
```bash
python datapm_processor_ollama.py linkedin_jobs_detailed.csv --ollama-url http://localhost:11434
```

### **Especificar archivo de salida:**
```bash
python datapm_processor_ollama.py linkedin_jobs_detailed.csv --output mi_resultado.csv
```

## 📊 **Modelos recomendados:**

| Modelo | Tamaño | Velocidad | Calidad | Uso recomendado |
|--------|--------|-----------|---------|-----------------|
| `llama3.2:3b` | 3B | ⚡⚡⚡ | ⭐⭐⭐ | Procesamiento rápido |
| `llama3.2:7b` | 7B | ⚡⚡ | ⭐⭐⭐⭐ | Balance calidad/velocidad |
| `codellama:7b` | 7B | ⚡⚡ | ⭐⭐⭐⭐⭐ | Análisis técnico |
| `mistral:7b` | 7B | ⚡⚡ | ⭐⭐⭐⭐ | Análisis general |

## 🔧 **Configuración:**

### **Parámetros disponibles:**
- `--model`: Modelo de Ollama a usar (default: llama3.2:3b)
- `--ollama-url`: URL del servidor Ollama (default: http://localhost:11434)
- `--output`: Archivo de salida personalizado
- `--help`: Mostrar ayuda

### **Configuración de Ollama:**
```bash
# Verificar que Ollama esté ejecutándose
ollama list

# Ver modelos disponibles
ollama list

# Ejecutar Ollama en segundo plano
ollama serve
```

## 📈 **Rendimiento:**

### **Comparación con Gemini:**
| Aspecto | Gemini | Ollama |
|---------|--------|--------|
| Rate Limiting | 10 req/min | Sin límites |
| Velocidad | ⚡⚡⚡ | ⚡⚡⚡⚡ |
| Calidad | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Costo | Gratis/Paid | Gratis |
| Privacidad | Cloud | Local |

### **Tiempos estimados:**
- **50 registros**: ~2-3 minutos
- **100 registros**: ~4-6 minutos  
- **500 registros**: ~15-25 minutos

## 🛠️ **Solución de problemas:**

### **Error de conexión:**
```bash
# Verificar que Ollama esté ejecutándose
ollama serve

# Verificar en otro terminal
curl http://localhost:11434/api/tags
```

### **Modelo no encontrado:**
```bash
# Descargar el modelo
ollama pull llama3.2:3b

# Ver modelos disponibles
ollama list
```

### **Memoria insuficiente:**
- Usar modelos más pequeños (3B en lugar de 7B)
- Cerrar otras aplicaciones
- Aumentar memoria virtual

## 📁 **Archivos generados:**

El programa genera archivos CSV con el formato:
```
csv/archive/YYYYMMDD_HHMMSS_DataPM_Ollama_result.csv
```

### **Estructura del CSV:**
- `Job title (original)`: Título original del trabajo
- `Job title (short)`: Título normalizado
- `Company`: Nombre de la empresa
- `Country`, `State`, `City`: Ubicación
- `Schedule type`: Tipo de horario
- `Experience years`: Años de experiencia
- `Seniority`: Nivel de seniority
- `Skills`: Habilidades identificadas
- `Degrees`: Grados académicos
- `Software`: Software mencionado

## 🔄 **Migración desde Gemini:**

Si ya tienes la versión Gemini funcionando:

1. **Instalar Ollama** (ver requisitos arriba)
2. **Descargar modelo**:
   ```bash
   ollama pull llama3.2:3b
   ```
3. **Cambiar comando**:
   ```bash
   # Antes (Gemini)
   python datapm_processor.py archivo.csv --llm gemini --api-key TU_API_KEY
   
   # Ahora (Ollama)
   python datapm_processor_ollama.py archivo.csv
   ```

## 🎉 **¡Listo para usar!**

Con Ollama, puedes procesar archivos de cualquier tamaño sin preocuparte por límites de rate limiting. El programa mantiene la misma calidad de análisis que la versión Gemini pero con procesamiento ilimitado.

