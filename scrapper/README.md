# LinkedIn Applied Jobs Scraper

Un scraper automatizado para extraer información de trabajos aplicados desde LinkedIn y exportarlos a CSV con las columnas especificadas.

## 📋 Características

- ✅ **Login manual**: Introduce tus credenciales de LinkedIn manualmente
- ✅ **Paginación automática**: Navega por múltiples páginas de trabajos aplicados
- ✅ **Extracción inteligente**: Extrae datos usando selectores CSS específicos
- ✅ **Manejo de fechas**: Convierte fechas relativas ("Applied 4m ago") a fechas absolutas
- ✅ **Exportación CSV**: Genera archivos CSV con las columnas requeridas
- ✅ **Campos opcionales**: Maneja campos vacíos cuando no hay información disponible

## 📊 Columnas del CSV

| Columna | Descripción | Disponibilidad |
|---------|-------------|----------------|
| `COMPANY` | Nombre de la empresa | ✅ Disponible |
| `JOB TITLE` | Título del puesto | ✅ Disponible |
| `LOCATION` | Ubicación del trabajo | ✅ Disponible |
| `JOB DESCRIPTION LINK` | Enlace a la descripción completa | ✅ Disponible |
| `SOURCE` | Fuente del trabajo | ❌ No disponible |
| `REFERRED BY` | Persona que refirió | ❌ No disponible |
| `SALARY` | Información salarial | ❌ No disponible |
| `BENEFITS` | Beneficios del puesto | ❌ No disponible |
| `APP SUBMITTED DATE` | Fecha de aplicación | ✅ Disponible |

## 🚀 Instalación

### 1. Instalar dependencias

```bash
# Instalar Selenium y webdriver-manager
pip install selenium webdriver-manager
```

O usando el archivo requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Instalar ChromeDriver

El scraper usa ChromeDriver automáticamente gestionado por webdriver-manager, por lo que no necesitas instalarlo manualmente.

## 📖 Uso

### Método 1: Ejecución directa

```bash
cd "D:\Work Work\Upwork\DataPM\scrapper"
python linkedin_applied_scraper.py
```

### Método 2: Con número de páginas específico

El script te pedirá que introduzcas el número de páginas a scrapear.

### Método 3: Ejecución desde código

```python
from linkedin_applied_scraper import LinkedInAppliedScraper

scraper = LinkedInAppliedScraper()
scraper.run_scraper(max_pages=10)  # Scrapea 10 páginas
```

## 🔧 Configuración

### Archivo de configuración

El archivo `config.py` contiene todas las configuraciones importantes:

- **URLs de LinkedIn**: URLs de login y trabajos aplicados
- **Selectores CSS**: Para la extracción de datos
- **Columnas CSV**: Definición de columnas del archivo de salida
- **Patrones de fecha**: Para el parsing de fechas

### Cambiar carpeta de salida

Por defecto, los archivos se guardan en:
```
D:\Work Work\Upwork\DataPM\csv\src\scrapped\Applied
```

Para cambiar esto, modifica `Config.DEFAULT_OUTPUT_FOLDER` en `config.py`.

## 📋 Proceso de Scraping

### 1. Inicio del programa
```
🚀 Starting LinkedIn Applied Jobs Scraper
==================================================
```

### 2. Configuración del navegador
- Se abre Chrome con las opciones optimizadas
- Se configuran opciones para evitar detección de automatización

### 3. Login manual
```
📝 Please log in to LinkedIn manually:
   1. Enter your email/username
   2. Enter your password
   3. Complete any 2FA if required
   4. Press Enter here when you're logged in and on the main page
```

### 4. Navegación a trabajos aplicados
- El scraper navega automáticamente a la página de trabajos aplicados
- Espera a que se cargue completamente la página

### 5. Carga de trabajos
```
📄 Loading jobs from X pages...
📊 Processing page 1/X...
```

### 6. Extracción de datos
```
🔍 Extracting job data...
✅ Extracted job 1: Senior Python Developer at TechCorp Inc.
✅ Extracted job 2: Data Analyst at DataFlow Solutions
```

### 7. Guardado de resultados
```
✅ Data saved to: D:\Work Work\Upwork\DataPM\csv\src\scrapped\Applied\linkedin_applied_jobs_20240115_143022.csv
📊 Total jobs saved: 25
```

## 🧪 Pruebas

Para ejecutar las pruebas y verificar que todo funciona correctamente:

```bash
# Ejecutar todas las pruebas
python test_scraper.py

# Ejecutar prueba específica
python test_scraper.py config      # Prueba de configuración
python test_scraper.py dates       # Prueba de parsing de fechas
python test_scraper.py extraction  # Prueba de simulación de extracción
```

## 📁 Estructura de archivos

```
D:\Work Work\Upwork\DataPM\scrapper\
├── linkedin_applied_scraper.py    # Script principal del scraper
├── config.py                      # Configuración y constantes
├── test_scraper.py               # Script de pruebas
├── requirements.txt              # Dependencias Python
├── README.md                     # Este archivo
└── workflow-results-container.txt # Estructura HTML de referencia
```

## 📂 Salida

Los archivos CSV se generan en:
```
D:\Work Work\Upwork\DataPM\csv\src\scrapped\Applied\
```

Con nombres como:
- `linkedin_applied_jobs_20240115_143022.csv`
- `linkedin_applied_jobs_20240116_092315.csv`

## ⚠️ Consideraciones importantes

### 1. Login manual requerido
- Debes iniciar sesión manualmente en LinkedIn
- El scraper no almacena ni usa tus credenciales
- Soporta autenticación de dos factores (2FA)

### 2. Campos no disponibles
Los siguientes campos no están disponibles en la página de LinkedIn y se dejarán vacíos:
- `SOURCE`
- `REFERRED BY`
- `SALARY`
- `BENEFITS`

### 3. Manejo de fechas
- Las fechas se extraen de textos como "Applied 4m ago"
- Si no se puede determinar la fecha exacta, se calcula automáticamente
- Las fechas se guardan en formato `YYYY-MM-DD HH:MM:SS`

### 4. Límites de paginación
- LinkedIn puede tener límites en el número de páginas
- Se recomienda empezar con pocas páginas (5-10) y aumentar gradualmente

## 🔧 Solución de problemas

### Error: "ChromeDriver not found"
```bash
pip install webdriver-manager
# O reinstala selenium
pip uninstall selenium
pip install selenium
```

### Error: "Output folder is not writable"
- Verifica que tienes permisos de escritura en la carpeta de salida
- Cambia la carpeta de salida en `config.py` si es necesario

### Error: "No jobs found"
- Verifica que estás en la página correcta de trabajos aplicados
- Asegúrate de que tienes trabajos aplicados en LinkedIn
- Intenta recargar la página manualmente antes de continuar

### El scraper se queda atascado
- Presiona `Ctrl+C` para detener el proceso
- Verifica tu conexión a internet
- Intenta con menos páginas inicialmente

## 📞 Soporte

Si encuentras problemas:

1. Ejecuta las pruebas: `python test_scraper.py`
2. Revisa los mensajes de error en la consola
3. Verifica que todas las dependencias están instaladas
4. Asegúrate de que Chrome esté actualizado

## 🔄 Actualizaciones

Para futuras actualizaciones, verifica si LinkedIn ha cambiado su estructura HTML y actualiza los selectores CSS en `config.py` si es necesario.

## 📜 Licencia

Este proyecto es para uso personal. Respeta los términos de servicio de LinkedIn y no uses este scraper para fines comerciales sin autorización.
