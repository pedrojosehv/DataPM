# Revisión de almacenamiento de outputs del scrapper
_Exported on 8/18/2025 at 14:10:45 GMT+2 from Cursor (1.4.5)_

---

**User**

vamos a procesar un nuevo lote de trabajos, quisiera hacer una revisión previa del código de los programas verificando dónde se están almacenando los outputs que genera cada programa, empezando con el scrapper 
D:\Work Work\Upwork\DataPM\scrapper\linkedin_selenium.py

1) Verifica que carpeta de almacenamiento sea:

D:\Work Work\Upwork\DataPM\csv\src\scrapped

2) Que el almacenamiento de los trabajos extraídos sea en un sólo archivo csv y no se esté haciendo la separación en batches

---

**Cursor**

Voy a revisar el archivo del scrapper para identificar la ruta de guardado y cómo se escribe el CSV (único archivo vs batches).

Voy a revisar y ajustar el bloque de guardado del archivo para que use la carpeta `csv/src/scrapped` y escriba un único CSV por ejecución. Luego te confirmo el resultado.

```python
# --- FUNCIÓN REUTILIZABLE PARA NAVEGAR ENTRE PÁGINAS ---
def go_to_page(driver, target_page, current_page=None):
    """Navega a la página target_page desde la página actual o desde current_page si se indica."""
    print(f"Navegando hasta la página: {target_page}")
    for p in range((current_page or 1) + 1, target_page + 1):
        next_selectors = [
            f"button[aria-label='Page {p}']",
            "button[aria-label='Next']",
            "button[aria-label='Siguiente']",
            "li.artdeco-pagination__indicator--active + li button",
            "button.artdeco-pagination__button--next"
        ]
        next_button = None
        for selector in next_selectors:
            try:
                next_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except TimeoutException:
                continue
        if next_button:
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            random_delay(1, 2)
            next_button.click()
            print(f"✅ Navegado a página {p}")
            random_delay(3, 5)
        else:
            print(f"🚫 No se encontró botón para la página {p}. Abortando navegación.")
            break
from selenium import webdriver
from datetime import datetime
import time
import csv
import random
import re
import os

# --- CONFIGURACIÓN DE USUARIO ---
import argparse
EMAIL = "11-10466@usb.ve"  
PASSWORD = "SanJudas.2011"  
KEYWORDS = "Producto Manager Junior"
LOCATION = "Spain"
REMOTE_FILTER = "2"   # 2 = Remote

# Argumentos para rango de páginas
parser = argparse.ArgumentParser(description="LinkedIn Scraper con rango de páginas")
parser.add_argument('--page-start', type=int, default=1, help='Página inicial a scrapear')
parser.add_argument('--page-end', type=int, default=3, help='Página final a scrapear')
args = parser.parse_args()
PAGE_START = args.page_start
PAGE_END = args.page_end

# --- CONFIGURACIÓN ANTI-DETECCIÓN ---
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ANTI-DETECCIÓN ---
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")

# Agregar User-Agent personalizado
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

# Deshabilitar WebGL para evitar fingerprinting
options.add_argument("--disable-webgl")
options.add_argument("--disable-3d-apis")

# Agregar preferencias adicionales
options.add_experimental_option("prefs", {
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False,
    "profile.default_content_setting_values.notifications": 2
})

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options)

# Ocultar que es automatizado
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def random_delay(min_seconds=1, max_seconds=3):
    """Pausa aleatoria para evitar detección"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def safe_find_element(driver, by, selector, timeout=10):
    """Busca elemento de forma segura con múltiples intentos"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    except TimeoutException:
        return None

def safe_find_elements(driver, by, selector, timeout=10):
    """Busca elementos de forma segura"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by, selector))
        )
    except TimeoutException:
        return []

def verify_login_success(driver):
    """Verifica si el login fue exitoso"""
    try:
        # Esperar a que aparezca el feed o el perfil
        WebDriverWait(driver, 15).until(
            EC.any_of(
                EC.url_contains("/feed/"),
                EC.url_contains("/mynetwork/"),
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.global-nav"))
            )
        )
        return True
    except TimeoutException:
        return False

def extract_text_safe(element, default=""):
    """Extrae texto de forma segura"""
    try:
        return element.text.strip() if element else default
    except:
        return default

def clean_text_for_csv(text):
    """Limpia texto para CSV"""
    if not text:
        return ""
    # Remover caracteres problemáticos y normalizar
    cleaned = re.sub(r'[\r\n\t]', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

# --- 1. LOGIN LINKEDIN CON VERIFICACIÓN ---
print("Iniciando login en LinkedIn...")
driver.get("https://www.linkedin.com/login")
random_delay(2, 4)

# Buscar campos de login
email_field = safe_find_element(driver, By.ID, "username")
password_field = safe_find_element(driver, By.ID, "password")

if not email_field or not password_field:
    print("❌ Error: No se encontraron los campos de login")
    driver.quit()
    exit(1)

# Llenar formulario de manera más humana
for char in EMAIL:
    email_field.send_keys(char)
    random_delay(0.1, 0.3)  # Pequeña pausa entre caracteres

random_delay(1, 2)  # Pausa antes de pasar a la contraseña

for char in PASSWORD:
    password_field.send_keys(char)
    random_delay(0.1, 0.3)  # Pequeña pausa entre caracteres

random_delay(1.5, 2.5)  # Pausa antes de dar enter
password_field.send_keys(Keys.RETURN)

# Verificar login exitoso con más tiempo de espera
print("Verificando login...")
if not verify_login_success(driver):
    print("❌ Error: Login fallido. Verifica credenciales o captcha")
    # Guardar screenshot para debug
    try:
        driver.save_screenshot("login_error.png")
        print("Se ha guardado una captura de pantalla en 'login_error.png'")
    except:
        pass
    driver.quit()
    exit(1)

print("✅ Login exitoso")

# --- 2. NAVEGAR A BÚSQUEDA CON VERIFICACIÓN ---
print("Navegando a resultados de búsqueda...")
search_url = (
    f"https://www.linkedin.com/jobs/search/"
    f"?keywords={KEYWORDS}"
    f"&location={LOCATION}"
    f"&f_WT={REMOTE_FILTER}"
    f"&distance=25"
)

driver.get(search_url)
random_delay(3, 5)

# Verificar que llegamos a la página de empleos
WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
)
job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")

if not job_cards:
    print("❌ Error: No se encontraron resultados de empleos")
    driver.quit()
    exit(1)

print(f"✅ Encontrados {len(job_cards)} empleos para procesar")

results = []
processed_count = 0


# --- NAVEGAR HASTA LA PÁGINA DE INICIO SI ES NECESARIO ---
if PAGE_START > 1:
    go_to_page(driver, PAGE_START, current_page=1)

for page in range(PAGE_START, PAGE_END + 1):
    print(f"\n📄 Procesando página {page}/{PAGE_END}...")
    
    # Esperar y localizar las tarjetas en la página actual
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
    )
    job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")
    
    if not job_cards:
        print(f"⚠️  No se encontraron ofertas en la página {page}. Saltando...")
        continue
    
    print(f"✅ Encontrados {len(job_cards)} empleos en página {page}")
    
    for idx, card in enumerate(job_cards, start=1):
        try:
            print(f"Procesando empleo {idx}/{len(job_cards)} (página {page})...")
            
            # Re-find el elemento para evitar StaleElementReferenceException
            card = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")[idx-1]
            
            # Scroll y click seguro
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            random_delay(1, 2)
            
            # Intentar click con múltiples estrategias
            try:
                card.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", card)
            except StaleElementReferenceException:
                # Re-find y reintentar
                card = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")[idx-1]
                card.click()

            # Esperar carga del panel de detalles con múltiples selectores
            detail_selectors = [
                "div.jobs-search__job-details--wrapper",
                "div.job-details-jobs-unified-top-card__container--two-pane",
                "div.jobs-unified-top-card__content"
            ]
            
            detail_loaded = False
            for selector in detail_selectors:
                if safe_find_element(driver, By.CSS_SELECTOR, selector, timeout=5):
                    detail_loaded = True
                    break
            
            if not detail_loaded:
                print(f"⚠️  Saltando empleo {page}-{idx}: No se cargaron los detalles")
                continue

            random_delay(1, 2)

            # Extraer datos con múltiples selectores de fallback
            title = ""
            title_selectors = [
                "div.job-details-jobs-unified-top-card__container--two-pane h1.t-24",
                "h1.t-24",
                "h1.job-details-jobs-unified-top-card__job-title",
                "h1"
            ]
            
            for selector in title_selectors:
                title_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if title_elem:
                    title = extract_text_safe(title_elem)
                    break
            
            company = ""
            company_selectors = [
                "div.job-details-jobs-unified-top-card__company-name a",
                "div.job-details-jobs-unified-top-card__company-name",
                "a[data-control-name='job_details_company_name']",
                "span.job-details-jobs-unified-top-card__company-name"
            ]
            
            for selector in company_selectors:
                company_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if company_elem:
                    company = extract_text_safe(company_elem)
                    break
            
            location = ""
            location_selectors = [
                "div.job-details-jobs-unified-top-card__primary-description-container span.tvm__text",
                "span.job-details-jobs-unified-top-card__bullet",
                "span[aria-label*='location']",
                "div.job-details-jobs-unified-top-card__primary-description-container"
            ]
            
            for selector in location_selectors:
                location_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if location_elem:
                    location = extract_text_safe(location_elem)
                    break
            
            description = ""
            description_selectors = [
                "article.jobs-description__container div.jobs-description-content__text--stretch",
                "div.jobs-description-content__text",
                "div.jobs-box__html-content",
                "div[data-job-description]"
            ]
            
            for selector in description_selectors:
                desc_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if desc_elem:
                    description = extract_text_safe(desc_elem)
                    break

            # Validar que tenemos al menos título y empresa
            if not title or not company:
                print(f"⚠️  Saltando empleo {page}-{idx}: Datos insuficientes")
                continue
        
            # Limpiar datos para CSV
            title = clean_text_for_csv(title)
            company = clean_text_for_csv(company)
            location = clean_text_for_csv(location)
            description = clean_text_for_csv(description)

            print(f"✅ [{page}-{idx}] {title[:50]}... | {company} | {location}")
            
            results.append({
                "title": title,
                "company": company,
                "location": location,
                "description": description
            })
            
            processed_count += 1
            random_delay(1, 3)  # Pausa entre empleos

        except Exception as e:
            print(f"❌ Error procesando empleo #{page}-{idx}: {str(e)}")
            continue
    
    # Buscar y hacer clic en "Siguiente" para la siguiente página
    if page < PAGE_END:  # No intentar navegar después de la última página configurada
        try:
            go_to_page(driver, page + 1, current_page=page)
        except Exception as e:
            print(f"❌ Error navegando a página {page + 1}: {str(e)}")
            break

# --- 4. GUARDAR EN CSV CON VALIDACIÓN ---
if results:
    # Crear directorio de salida absoluto: <repo_root>/csv/src/scrapped
    scrapped_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "csv",
        "src",
        "scrapped",
    )
    os.makedirs(scrapped_dir, exist_ok=True)

    # Guardar TODO en un único archivo CSV por ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scrape_filename = os.path.join(scrapped_dir, f"{timestamp}_linkedin_jobs.csv")

    try:
        with open(scrape_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "company", "location", "description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ {len(results)} ofertas guardadas en {scrape_filename}")
        print(f"✅ Proceso completado: {processed_count} ofertas totales procesadas")
    except Exception as e:
        print(f"❌ Error guardando CSV: {str(e)}")
else:
    print("❌ No se extrajo ningún empleo válido")

driver.quit()
```

Estoy validando que no haya errores de lint tras los cambios y voy a citar el bloque de guardado actualizado para que veas la ruta y formato del archivo.

- He ajustado el scrapper para guardar en la carpeta correcta y en un único archivo por ejecución.

Código relevante del bloque de guardado:
```378:406:scrapper/linkedin_selenium.py
# --- 4. GUARDAR EN CSV CON VALIDACIÓN ---
if results:
    # Crear directorio de salida absoluto: <repo_root>/csv/src/scrapped
    scrapped_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "csv",
        "src",
        "scrapped",
    )
    os.makedirs(scrapped_dir, exist_ok=True)

    # Guardar TODO en un único archivo CSV por ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scrape_filename = os.path.join(scrapped_dir, f"{timestamp}_linkedin_jobs.csv")

    try:
        with open(scrape_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "company", "location", "description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ {len(results)} ofertas guardadas en {scrape_filename}")
        print(f"✅ Proceso completado: {processed_count} ofertas totales procesadas")
    except Exception as e:
        print(f"❌ Error guardando CSV: {str(e)}")
else:
    print("❌ No se extrajo ningún empleo válido")
```

- Ruta de almacenamiento ahora: `D:\Work Work\Upwork\DataPM\csv\src\scrapped`
- Se elimina la separación en batches: ahora se escribe un solo CSV por corrida con nombre `<timestamp>_linkedin_jobs.csv`.

¿Seguimos con la verificación de los otros programas de procesamiento?

```python
# --- 4. GUARDAR EN CSV CON VALIDACIÓN ---
if results:
    # Crear directorio de salida absoluto: <repo_root>/csv/src/scrapped
    scrapped_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "csv",
        "src",
        "scrapped",
    )
    os.makedirs(scrapped_dir, exist_ok=True)

    # Guardar TODO en un único archivo CSV por ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scrape_filename = os.path.join(scrapped_dir, f"{timestamp}_linkedin_jobs.csv")

    try:
        with open(scrape_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "company", "location", "description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ {len(results)} ofertas guardadas en {scrape_filename}")
        print(f"✅ Proceso completado: {processed_count} ofertas totales procesadas")
    except Exception as e:
        print(f"❌ Error guardando CSV: {str(e)}")
else:
    print("❌ No se extrajo ningún empleo válido")
```

---

**User**

ahora verifica que el motor de procesamiento:

D:\Work Work\Upwork\DataPM\csv_engine\engines\datapm_processor.py

1) Tenga como almacenamiento de output: 
D:\Work Work\Upwork\DataPM\csv\src\csv_processed

2) Tenga como fuente de input el archivo más reciente en:
D:\Work Work\Upwork\DataPM\csv\src\scrapped
(puede modificarse o personalizarse según el prompt que te indique) 

3) Verifica que por cada 10 filas procesadas se genera un nuevo csv con la identificación de número de batch al final (ese código ya existe, es verificar que esté funcionando sin volver a escribir la función)

---

**Cursor**

Voy a revisar el motor `csv_engine/engines/datapm_processor.py` para confirmar carpeta de salida, selección del input más reciente y la lógica de batches de 10 filas.

Voy a buscar en el motor y utilidades si ya existe la lógica de dividir en lotes de 10 y escribir múltiples CSV, y confirmar la ruta de salida/inferencia del último archivo del directorio de scrapped.

Voy a actualizar el motor para: 1) seleccionar automáticamente el CSV más reciente en `csv/src/scrapped` cuando se indique, y 2) reutilizar la función existente de división en lotes para generar un CSV por cada 10 filas en `csv/src/csv_processed`. Luego validaré lints y te cito los bloques relevantes.

```python
#!/usr/bin/env python3
"""
DataPM Processor - Replica la automatización de Make.com para análisis de trabajos
Procesa descripciones de trabajo con LLM (Gemini/Ollama) y genera CSV estructurado
"""

import csv
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse

# Configuración de LLM
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Google Gemini no disponible. Instala con: pip install google-generativeai")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Requests no disponible. Instala con: pip install requests")


# Extensiones y utilidades de import para reutilizar funciones existentes
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_ENGINE_ROOT = os.path.dirname(CURRENT_DIR)
REPO_ROOT = os.path.dirname(CSV_ENGINE_ROOT)

# Permitir importar módulos hermanos como `normalization.split_batches`
if CSV_ENGINE_ROOT not in sys.path:
    sys.path.append(CSV_ENGINE_ROOT)

try:
    from normalization.split_batches import split_csv_batches  # type: ignore
except Exception:
    split_csv_batches = None


class DataPMProcessor:
    """Procesador principal para análisis de descripciones de trabajo"""
    
    def __init__(self, llm_type: str = "gemini", api_key: Optional[str] = None, 
                 ollama_url: str = "http://localhost:11434"):
        """
        Inicializa el procesador
        
        Args:
            llm_type: "gemini" o "ollama"
            api_key: API key para Gemini (requerido si llm_type="gemini")
            ollama_url: URL del servidor Ollama
        """
        self.llm_type = llm_type
        self.api_key = api_key
        self.ollama_url = ollama_url
        
        # Configurar Gemini si está disponible
        if llm_type == "gemini" and GEMINI_AVAILABLE:
            if not api_key:
                raise ValueError("API key requerida para Gemini")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Schema de normalización (igual que en Make.com)
        self.schema = {
            "job_title_original": "string",
            "job_title_short": "string",  # Normalizado a valores específicos
            "experience_years": "string",  # "0-3", "3-5", "5+"
            "job_schedule_type": "string",  # "Full-time", "Part-time", "Contract", "Internship", "Unknown"
            "seniority": "string",  # "Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"
            "city": "string",
            "state": "string",  # Abreviación de 2 letras para US/CA
            "country": "string",
            "degrees": "array",  # Array de strings
            "skills": "array",   # Array de strings
            "software": "array", # Array de strings
            "company_name": "string"
        }
        
        # Valores normalizados permitidos
        self.normalized_values = {
            "job_title_short": [
                "Product Manager", "Data Analyst", "Data Scientist", "Data Engineer", 
                "UX/UI Designer", "Software Engineer", "Marketing Specialist", 
                "Project Manager", "Business Analyst", "Process Designer", 
                "Product Designer", "IT Analyst", "DevOps Engineer",
                "Quality Assurance Engineer", "Documentation Specialist",
                "Financial Analyst", "Compliance Analyst", "Operations Manager", 
                "Other"
            ],
            "experience_years": ["0-3", "3-5", "5+"],
            "job_schedule_type": ["Full-time", "Part-time", "Contract", "Internship", "Unknown"],
            "seniority": ["Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"],
            "degrees": [
                "Bachelor's Degree", "Master's Degree", "PhD", "Associate's Degree", 
                "Higher Education", "Engineering", "Automotive Engineering", 
                "Vocational Training", "Other"
            ],
            "skills": [
                "Project Management", "Agile", "Scrum", "API", "Cloud Computing", 
                "Machine Learning", "Data Analysis", "Data Visualization", 
                "User Research", "UI/UX Design", "Product Design", "Product Management", 
                "Marketing", "Sales", "Communication", "Problem Solving", 
                "Process Optimization", "Regulatory Compliance", "Document Management", 
                "Quality Control", "Auditing", "Technical Writing", "Statistical Reporting", 
                "Business Acumen", "Cross-functional Collaboration", "Team Leadership", 
                "Healthcare Knowledge", "Supply Chain", "SDLC", "User-Centered Design",
                "Quality Assurance", "Test Automation", "Clinical Documentation",
                "Investment Banking", "Supply Chain Management", "Operations Management",
                "KYC/AML Compliance", "Financial Analysis"
            ],
            "software": [
                "SQL", "Python", "R", "C", "C++", "Java", "JavaScript", "Microsoft Excel", 
                "Figma", "Sketch", "Adobe XD", "Adobe Creative Suite", "Tableau", 
                "Power BI", "Jira", "Confluence", "Atlassian", "SAP", "Salesforce", 
                "HubSpot", "Google Analytics", "Looker", "MicroStrategy", "GitHub", 
                "GitLab", "DevOps Tools", "Vercel", "Next.js", "Prisma", "PlanetScale", 
                "Rhino", "Keyshot", "SolidWorks", "C4D", "OneDrive", "Word", "IMDS", 
                "Pytorch", "Flow", "AWS", "Azure", "GCP", "SQL Server", "Oracle", 
                "MongoDB", "PostgreSQL", "Apache Spark", "Veeva Vault", "Jenkins",
                "JUnit", "Cypress", "Selenium", "TestRail", "Bloomberg Terminal"
            ]
        }
    
    def create_system_prompt(self) -> str:
        """Crea el prompt del sistema igual que en Make.com"""
        return f"""You are a strict data extractor and standardizer. You MUST return ONLY a valid JSON object and nothing else.
The JSON must follow this schema:

job_title_original (string)

job_title_short (string, normalized to one of these values: {self.normalized_values['job_title_short']})

experience_years (string, normalized to one of these formats: "0-3" for less than 3 years, "3-5" for ranges, "5+" for 5 or more years)

job_schedule_type (string, normalized to one of these values: {self.normalized_values['job_schedule_type']})

seniority (string, normalized to one of these values: {self.normalized_values['seniority']})

city (string, normalized to proper case, e.g., "New York", "Madrid". If not found, use "Unknown".)

state (string, normalized to two-letter abbreviation if in the US/CA, e.g., "NY", "CA". If not in the US/CA or not found, use "Unknown".)

country (string, normalized to proper case, e.g., "United States", "Spain", "Mexico", "United Kingdom", "Germany", "France", "Panamá", "Venezuela", "European Union", "Unknown")

degrees (array of strings, normalized to one of these values: {self.normalized_values['degrees']})

skills (array of strings, normalized to a fixed set of values like: {self.normalized_values['skills']})

software (array of strings, normalized to a fixed set of values like: {self.normalized_values['software']})

company_name (string)

If you cannot determine a value, use "Unknown" for strings and blank space for arrays, data slot must be empty. No extra text, no markdown, no explanation."""

    def create_user_prompt(self, description: str) -> str:
        """Crea el prompt del usuario"""
        return f"""INPUT: {{"text":"{description}"}}
TASK: Analyze INPUT.text and return the JSON according to the schema in the system instructions."""

    def call_gemini(self, description: str) -> Dict[str, Any]:
        """Llama a Google Gemini para procesar la descripción"""
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Google Gemini no está disponible")
        
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                system_prompt = self.create_system_prompt()
                user_prompt = self.create_user_prompt(description)
                
                response = self.model.generate_content([
                    {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}
                ])
                
                # Extraer JSON de la respuesta
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                return json.loads(response_text.strip())
                
            except Exception as e:
                error_str = str(e)
                
                # Verificar si es un error de rate limiting
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    retry_count += 1
                    
                    # Extraer el tiempo de espera del error si está disponible
                    wait_time = 60  # Tiempo por defecto
                    if "retry_delay" in error_str:
                        try:
                            # Buscar el tiempo de espera en el mensaje de error
                            import re
                            match = re.search(r'seconds":\s*(\d+)', error_str)
                            if match:
                                wait_time = int(match.group(1))
                        except:
                            pass
                    
                    print(f"⏳ Rate limit alcanzado. Esperando {wait_time} segundos... (intento {retry_count}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    # Si no es rate limiting, es un error real
                    print(f"❌ Error con Gemini: {e}")
                    return self.get_default_response()
        
        # Si se agotaron los reintentos
        print(f"❌ Se agotaron los reintentos por rate limiting")
        return self.get_default_response()

    def call_ollama(self, description: str) -> Dict[str, Any]:
        """Llama a Ollama para procesar la descripción"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("Requests no está disponible")
        
        try:
            system_prompt = self.create_system_prompt()
            user_prompt = self.create_user_prompt(description)
            
            payload = {
                "model": "llama3.2:3b",  # Puedes cambiar el modelo
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False
            }
            
            response = requests.post(f"{self.ollama_url}/api/chat", json=payload)
            response.raise_for_status()
            
            response_text = response.json()["message"]["content"].strip()
            
            # Extraer JSON de la respuesta
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            return json.loads(response_text.strip())
            
        except Exception as e:
            print(f"❌ Error con Ollama: {e}")
            return self.get_default_response()

    def get_default_response(self) -> Dict[str, Any]:
        """Retorna una respuesta por defecto en caso de error"""
        return {
            "job_title_original": "Unknown",
            "job_title_short": "Unknown",
            "experience_years": "Unknown",
            "job_schedule_type": "Unknown",
            "seniority": "Unknown",
            "city": "Unknown",
            "state": "Unknown",
            "country": "Unknown",
            "degrees": [],
            "skills": [],
            "software": [],
            "company_name": "Unknown"
        }

    def process_description(self, description: str) -> Dict[str, Any]:
        """Procesa una descripción usando el LLM configurado"""
        print(f"🤖 Procesando descripción con {self.llm_type.upper()}...")
        
        if self.llm_type == "gemini":
            return self.call_gemini(description)
        elif self.llm_type == "ollama":
            return self.call_ollama(description)
        else:
            raise ValueError(f"LLM tipo '{self.llm_type}' no soportado")

    def read_csv(self, file_path: str) -> List[Dict[str, str]]:
        """Lee el CSV de entrada"""
        print(f"📖 Leyendo CSV: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        data = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        
        print(f"✅ Leídos {len(data)} registros")
        return data

    def process_data(self, input_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Procesa todos los datos de entrada"""
        print(f"🔄 Procesando {len(input_data)} registros...")
        
        processed_data = []
        
        for i, row in enumerate(input_data, 1):
            print(f"📝 Procesando registro {i}/{len(input_data)}")
            
            # Extraer datos del CSV
            title = row.get('title', '')
            company = row.get('company', '')
            location = row.get('location', '')
            description = row.get('description', '')
            
            # Procesar con LLM con manejo de errores mejorado
            try:
                llm_result = self.process_description(description)
                
                # Verificar si el resultado es válido (no todo Unknown)
                if llm_result.get('job_title_short') == 'Unknown' and all(
                    v == 'Unknown' or v == [] for k, v in llm_result.items() 
                    if k not in ['job_title_original', 'degrees', 'skills', 'software']
                ):
                    print(f"⚠️  Resultado sospechoso para registro {i}, reintentando...")
                    # Reintentar una vez más
                    time.sleep(2)
                    llm_result = self.process_description(description)
                
                # Combinar datos originales con resultados del LLM
                processed_row = {
                    'Job title (original)': title,
                    'Job title (short)': llm_result.get('job_title_short', 'Unknown'),
                    'Company': llm_result.get('company_name', company),
                    'Country': llm_result.get('country', 'Unknown'),
                    'State': llm_result.get('state', 'Unknown'),
                    'City': llm_result.get('city', 'Unknown'),
                    'Schedule type': llm_result.get('job_schedule_type', 'Unknown'),
                    'Experience years': llm_result.get('experience_years', 'Unknown'),
                    'Seniority': llm_result.get('seniority', 'Unknown'),
                    'Skills': '; '.join(llm_result.get('skills', [])),
                    'Degrees': '; '.join(llm_result.get('degrees', [])),
                    'Software': '; '.join(llm_result.get('software', []))
                }
                
                processed_data.append(processed_row)
                
            except Exception as e:
                print(f"❌ Error procesando registro {i}: {e}")
                # Agregar una fila con datos mínimos en lugar de todo Unknown
                processed_row = {
                    'Job title (original)': title,
                    'Job title (short)': 'Error',
                    'Company': company,
                    'Country': 'Unknown',
                    'State': 'Unknown',
                    'City': 'Unknown',
                    'Schedule type': 'Unknown',
                    'Experience years': 'Unknown',
                    'Seniority': 'Unknown',
                    'Skills': '',
                    'Degrees': '',
                    'Software': ''
                }
                processed_data.append(processed_row)
            
            # Pausa para evitar rate limiting (ajustado a 5 segundos)
            if i < len(input_data):
                time.sleep(5)
        
        print(f"✅ Procesamiento completado")
        return processed_data

    def write_csv(self, data: List[Dict[str, Any]], output_path: str):
        """Escribe el CSV de salida"""
        print(f"💾 Guardando CSV: {output_path}")
        
        if not data:
            print("⚠️  No hay datos para guardar")
            return
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        print(f"✅ CSV guardado exitosamente")

    def run(self, input_file: str, output_file: Optional[str] = None):
        """Ejecuta el procesamiento completo"""
        print("🚀 Iniciando DataPM Processor")
        print(f"📊 LLM: {self.llm_type.upper()}")
        
        # Generar nombre de archivo de salida si no se proporciona
        if not output_file:
            # Determinar número de batch si está en el nombre del archivo de entrada
            input_filename = os.path.basename(input_file)
            batch_num = None
            import re
            match = re.search(r'_batch_(\d+)', input_filename)
            if match:
                batch_num = match.group(1)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if batch_num:
                output_file = f"csv/src/csv_processed/{timestamp}_DataPM_result_batch_{batch_num}.csv"
            else:
                output_file = f"csv/src/csv_processed/{timestamp}_DataPM_result.csv"
        
        try:
            # Leer datos de entrada
            input_data = self.read_csv(input_file)
            
            # Procesar datos
            processed_data = self.process_data(input_data)
            
            # Guardar resultados
            self.write_csv(processed_data, output_file)
            
            # Reutilizar función existente para dividir en lotes de 10 filas
            if split_csv_batches is not None:
                try:
                    # output_file -> archivo recién generado; dividirlo en batches de 10
                    output_dir = os.path.dirname(output_file)
                    split_csv_batches(output_file, output_dir, batch_size=10)
                except Exception as e:
                    print(f"⚠️  No se pudo dividir en lotes: {e}")
            else:
                print("⚠️  split_csv_batches no disponible; omitiendo división en lotes")
            
            print(f"🎉 Procesamiento completado exitosamente!")
            print(f"📁 Archivo de salida: {output_file}")
            
        except Exception as e:
            print(f"❌ Error durante el procesamiento: {e}")
            sys.exit(1)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="DataPM Processor - Análisis de descripciones de trabajo")
    parser.add_argument("input_file", help="Archivo CSV o carpeta de entrada (si se pasa carpeta, se usa el CSV más reciente). Use 'latest' para tomar el más reciente de csv/src/scrapped")
    parser.add_argument("--output", "-o", help="Archivo CSV de salida (opcional)")
    parser.add_argument("--llm", choices=["gemini", "ollama"], default="gemini", 
                       help="Tipo de LLM a usar (default: gemini)")
    parser.add_argument("--api-key", help="API key para Gemini (requerido si --llm=gemini)")
    parser.add_argument("--ollama-url", default="http://localhost:11434", 
                       help="URL del servidor Ollama (default: http://localhost:11434)")
    
    args = parser.parse_args()
    
    # Validaciones
    if args.llm == "gemini" and not args.api_key:
        print("❌ Error: --api-key es requerido para Gemini")
        print("💡 Obtén tu API key en: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    # Resolver input: permitir directorio o palabra clave 'latest'
    def resolve_input_path(input_arg: str) -> str:
        # Si es directorio, tomar el CSV más reciente
        if os.path.isdir(input_arg):
            candidates = [
                os.path.join(input_arg, f) for f in os.listdir(input_arg)
                if f.lower().endswith('.csv')
            ]
            if not candidates:
                raise FileNotFoundError(f"No se encontraron CSV en la carpeta: {input_arg}")
            return max(candidates, key=os.path.getmtime)
        
        # Si es 'latest', usar carpeta por defecto csv/src/scrapped
        if input_arg.strip().lower() in {"latest", "auto"}:
            default_scrapped = os.path.join(REPO_ROOT, "csv", "src", "scrapped")
            candidates = [
                os.path.join(default_scrapped, f) for f in os.listdir(default_scrapped)
                if f.lower().endswith('.csv')
            ]
            if not candidates:
                raise FileNotFoundError(f"No se encontraron CSV en: {default_scrapped}")
            return max(candidates, key=os.path.getmtime)
        
        # En otro caso, tratar como archivo
        return input_arg

    resolved_input = resolve_input_path(args.input_file)

    # Crear y ejecutar procesador
    processor = DataPMProcessor(
        llm_type=args.llm,
        api_key=args.api_key,
        ollama_url=args.ollama_url
    )
    
    processor.run(resolved_input, args.output)


if __name__ == "__main__":
    main()

```

- Verifiqué el motor y ajusté para cumplir tus 3 puntos.

### 1) Carpeta de output
- Ahora guarda en `csv/src/csv_processed` por defecto.
- Confirmado en `run()`:
```403:416:csv_engine/engines/datapm_processor.py
# Generar nombre de archivo de salida si no se proporciona
if not output_file:
    ...
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if batch_num:
        output_file = f"csv/src/csv_processed/{timestamp}_DataPM_result_batch_{batch_num}.csv"
    else:
        output_file = f"csv/src/csv_processed/{timestamp}_DataPM_result.csv"
```

### 2) Input: archivo más reciente en `csv/src/scrapped`
- Añadí resolución automática: puedes pasar un directorio o la palabra clave `latest`/`auto`, y toma el CSV más reciente de `csv/src/scrapped`.
```449:477:csv_engine/engines/datapm_processor.py
parser.add_argument("input_file", help="Archivo CSV o carpeta de entrada ... Use 'latest' para tomar el más reciente de csv/src/scrapped")
...
def resolve_input_path(input_arg: str) -> str:
    if os.path.isdir(input_arg):
        ...
        return max(candidates, key=os.path.getmtime)
    if input_arg.strip().lower() in {"latest", "auto"}:
        default_scrapped = os.path.join(REPO_ROOT, "csv", "src", "scrapped")
        ...
        return max(candidates, key=os.path.getmtime)
    return input_arg

resolved_input = resolve_input_path(args.input_file)
...
processor.run(resolved_input, args.output)
```

Uso rápido:
- Más reciente automático: `python csv_engine/engines/datapm_processor.py latest --llm ollama`
- O pasando la carpeta: `python csv_engine/engines/datapm_processor.py csv/src/scrapped`

### 3) Batches de 10 filas
- No reescribí la función; reutilizo `normalization.split_batches.split_csv_batches` si está disponible.
- Después de escribir el CSV único, se divide en lotes de 10, generando archivos con sufijo `_batch_N` en la misma carpeta de salida.
```428:437:csv_engine/engines/datapm_processor.py
# Reutilizar función existente para dividir en lotes de 10 filas
if split_csv_batches is not None:
    try:
        output_dir = os.path.dirname(output_file)
        split_csv_batches(output_file, output_dir, batch_size=10)
    except Exception as e:
        print(f"⚠️  No se pudo dividir en lotes: {e}")
else:
    print("⚠️  split_csv_batches no disponible; omitiendo división en lotes")
```

- Confirmé que `normalization/split_batches.py` existe y divide en lotes de 10. Esto mantendrá el comportamiento que querías verificar.

¿Quieres que deje fijo por defecto `--llm ollama` o algún modelo en particular, o lo dejamos configurable como está?

```python
# Generar nombre de archivo de salida si no se proporciona
if not output_file:
    ...
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if batch_num:
        output_file = f"csv/src/csv_processed/{timestamp}_DataPM_result_batch_{batch_num}.csv"
    else:
        output_file = f"csv/src/csv_processed/{timestamp}_DataPM_result.csv"
```

```python
parser.add_argument("input_file", help="Archivo CSV o carpeta de entrada ... Use 'latest' para tomar el más reciente de csv/src/scrapped")
...
def resolve_input_path(input_arg: str) -> str:
    if os.path.isdir(input_arg):
        ...
        return max(candidates, key=os.path.getmtime)
    if input_arg.strip().lower() in {"latest", "auto"}:
        default_scrapped = os.path.join(REPO_ROOT, "csv", "src", "scrapped")
        ...
        return max(candidates, key=os.path.getmtime)
    return input_arg

resolved_input = resolve_input_path(args.input_file)
...
processor.run(resolved_input, args.output)
```

```python
# Reutilizar función existente para dividir en lotes de 10 filas
if split_csv_batches is not None:
    try:
        output_dir = os.path.dirname(output_file)
        split_csv_batches(output_file, output_dir, batch_size=10)
    except Exception as e:
        print(f"⚠️  No se pudo dividir en lotes: {e}")
else:
    print("⚠️  split_csv_batches no disponible; omitiendo división en lotes")
```

---

**User**

1) El split en batches debería ir ocurriendo a medida que se están procesando las filas con el modelo de lenguaje, es decir:

El programa procesa 10 filas del CSV inicial con el LLM > Genera CSV > Continúa con las siguientes 10 filas

2) El procesador D:\Work Work\Upwork\DataPM\csv_engine\engines\datapm_processor.py debería usar es el LLM de Gemini AI, que ya debería tener escrito en el código este u otro de los motores de procesamiento de la carpeta D:\Work Work\Upwork\DataPM\csv_engine\engines


---

**Cursor**

Voy a actualizar el flujo para escribir un CSV por cada 10 filas durante el procesamiento, y ajustar la salida para usar `csv/src/csv_processed` como directorio. Luego revisaré lints y te cito los fragmentos relevantes.

```python
#!/usr/bin/env python3
"""
DataPM Processor - Replica la automatización de Make.com para análisis de trabajos
Procesa descripciones de trabajo con LLM (Gemini/Ollama) y genera CSV estructurado
"""

import csv
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse

# Configuración de LLM
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Google Gemini no disponible. Instala con: pip install google-generativeai")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Requests no disponible. Instala con: pip install requests")


# Extensiones y utilidades de import para reutilizar funciones existentes
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_ENGINE_ROOT = os.path.dirname(CURRENT_DIR)
REPO_ROOT = os.path.dirname(CSV_ENGINE_ROOT)

# Permitir importar módulos hermanos como `normalization.split_batches`
if CSV_ENGINE_ROOT not in sys.path:
    sys.path.append(CSV_ENGINE_ROOT)

try:
    from normalization.split_batches import split_csv_batches  # type: ignore
except Exception:
    split_csv_batches = None


class DataPMProcessor:
    """Procesador principal para análisis de descripciones de trabajo"""
    
    def __init__(self, llm_type: str = "gemini", api_key: Optional[str] = None, 
                 ollama_url: str = "http://localhost:11434"):
        """
        Inicializa el procesador
        
        Args:
            llm_type: "gemini" o "ollama"
            api_key: API key para Gemini (requerido si llm_type="gemini")
            ollama_url: URL del servidor Ollama
        """
        self.llm_type = llm_type
        self.api_key = api_key
        self.ollama_url = ollama_url
        
        # Configurar Gemini si está disponible
        if llm_type == "gemini" and GEMINI_AVAILABLE:
            if not api_key:
                raise ValueError("API key requerida para Gemini")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Schema de normalización (igual que en Make.com)
        self.schema = {
            "job_title_original": "string",
            "job_title_short": "string",  # Normalizado a valores específicos
            "experience_years": "string",  # "0-3", "3-5", "5+"
            "job_schedule_type": "string",  # "Full-time", "Part-time", "Contract", "Internship", "Unknown"
            "seniority": "string",  # "Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"
            "city": "string",
            "state": "string",  # Abreviación de 2 letras para US/CA
            "country": "string",
            "degrees": "array",  # Array de strings
            "skills": "array",   # Array de strings
            "software": "array", # Array de strings
            "company_name": "string"
        }
        
        # Valores normalizados permitidos
        self.normalized_values = {
            "job_title_short": [
                "Product Manager", "Data Analyst", "Data Scientist", "Data Engineer", 
                "UX/UI Designer", "Software Engineer", "Marketing Specialist", 
                "Project Manager", "Business Analyst", "Process Designer", 
                "Product Designer", "IT Analyst", "DevOps Engineer",
                "Quality Assurance Engineer", "Documentation Specialist",
                "Financial Analyst", "Compliance Analyst", "Operations Manager", 
                "Other"
            ],
            "experience_years": ["0-3", "3-5", "5+"],
            "job_schedule_type": ["Full-time", "Part-time", "Contract", "Internship", "Unknown"],
            "seniority": ["Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"],
            "degrees": [
                "Bachelor's Degree", "Master's Degree", "PhD", "Associate's Degree", 
                "Higher Education", "Engineering", "Automotive Engineering", 
                "Vocational Training", "Other"
            ],
            "skills": [
                "Project Management", "Agile", "Scrum", "API", "Cloud Computing", 
                "Machine Learning", "Data Analysis", "Data Visualization", 
                "User Research", "UI/UX Design", "Product Design", "Product Management", 
                "Marketing", "Sales", "Communication", "Problem Solving", 
                "Process Optimization", "Regulatory Compliance", "Document Management", 
                "Quality Control", "Auditing", "Technical Writing", "Statistical Reporting", 
                "Business Acumen", "Cross-functional Collaboration", "Team Leadership", 
                "Healthcare Knowledge", "Supply Chain", "SDLC", "User-Centered Design",
                "Quality Assurance", "Test Automation", "Clinical Documentation",
                "Investment Banking", "Supply Chain Management", "Operations Management",
                "KYC/AML Compliance", "Financial Analysis"
            ],
            "software": [
                "SQL", "Python", "R", "C", "C++", "Java", "JavaScript", "Microsoft Excel", 
                "Figma", "Sketch", "Adobe XD", "Adobe Creative Suite", "Tableau", 
                "Power BI", "Jira", "Confluence", "Atlassian", "SAP", "Salesforce", 
                "HubSpot", "Google Analytics", "Looker", "MicroStrategy", "GitHub", 
                "GitLab", "DevOps Tools", "Vercel", "Next.js", "Prisma", "PlanetScale", 
                "Rhino", "Keyshot", "SolidWorks", "C4D", "OneDrive", "Word", "IMDS", 
                "Pytorch", "Flow", "AWS", "Azure", "GCP", "SQL Server", "Oracle", 
                "MongoDB", "PostgreSQL", "Apache Spark", "Veeva Vault", "Jenkins",
                "JUnit", "Cypress", "Selenium", "TestRail", "Bloomberg Terminal"
            ]
        }
    
    def create_system_prompt(self) -> str:
        """Crea el prompt del sistema igual que en Make.com"""
        return f"""You are a strict data extractor and standardizer. You MUST return ONLY a valid JSON object and nothing else.
The JSON must follow this schema:

job_title_original (string)

job_title_short (string, normalized to one of these values: {self.normalized_values['job_title_short']})

experience_years (string, normalized to one of these formats: "0-3" for less than 3 years, "3-5" for ranges, "5+" for 5 or more years)

job_schedule_type (string, normalized to one of these values: {self.normalized_values['job_schedule_type']})

seniority (string, normalized to one of these values: {self.normalized_values['seniority']})

city (string, normalized to proper case, e.g., "New York", "Madrid". If not found, use "Unknown".)

state (string, normalized to two-letter abbreviation if in the US/CA, e.g., "NY", "CA". If not in the US/CA or not found, use "Unknown".)

country (string, normalized to proper case, e.g., "United States", "Spain", "Mexico", "United Kingdom", "Germany", "France", "Panamá", "Venezuela", "European Union", "Unknown")

degrees (array of strings, normalized to one of these values: {self.normalized_values['degrees']})

skills (array of strings, normalized to a fixed set of values like: {self.normalized_values['skills']})

software (array of strings, normalized to a fixed set of values like: {self.normalized_values['software']})

company_name (string)

If you cannot determine a value, use "Unknown" for strings and blank space for arrays, data slot must be empty. No extra text, no markdown, no explanation."""

    def create_user_prompt(self, description: str) -> str:
        """Crea el prompt del usuario"""
        return f"""INPUT: {{"text":"{description}"}}
TASK: Analyze INPUT.text and return the JSON according to the schema in the system instructions."""

    def call_gemini(self, description: str) -> Dict[str, Any]:
        """Llama a Google Gemini para procesar la descripción"""
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Google Gemini no está disponible")
        
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                system_prompt = self.create_system_prompt()
                user_prompt = self.create_user_prompt(description)
                
                response = self.model.generate_content([
                    {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}
                ])
                
                # Extraer JSON de la respuesta
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                return json.loads(response_text.strip())
                
            except Exception as e:
                error_str = str(e)
                
                # Verificar si es un error de rate limiting
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    retry_count += 1
                    
                    # Extraer el tiempo de espera del error si está disponible
                    wait_time = 60  # Tiempo por defecto
                    if "retry_delay" in error_str:
                        try:
                            # Buscar el tiempo de espera en el mensaje de error
                            import re
                            match = re.search(r'seconds":\s*(\d+)', error_str)
                            if match:
                                wait_time = int(match.group(1))
                        except:
                            pass
                    
                    print(f"⏳ Rate limit alcanzado. Esperando {wait_time} segundos... (intento {retry_count}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    # Si no es rate limiting, es un error real
                    print(f"❌ Error con Gemini: {e}")
                    return self.get_default_response()
        
        # Si se agotaron los reintentos
        print(f"❌ Se agotaron los reintentos por rate limiting")
        return self.get_default_response()

    def call_ollama(self, description: str) -> Dict[str, Any]:
        """Llama a Ollama para procesar la descripción"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("Requests no está disponible")
        
        try:
            system_prompt = self.create_system_prompt()
            user_prompt = self.create_user_prompt(description)
            
            payload = {
                "model": "llama3.2:3b",  # Puedes cambiar el modelo
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False
            }
            
            response = requests.post(f"{self.ollama_url}/api/chat", json=payload)
            response.raise_for_status()
            
            response_text = response.json()["message"]["content"].strip()
            
            # Extraer JSON de la respuesta
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            return json.loads(response_text.strip())
            
        except Exception as e:
            print(f"❌ Error con Ollama: {e}")
            return self.get_default_response()

    def get_default_response(self) -> Dict[str, Any]:
        """Retorna una respuesta por defecto en caso de error"""
        return {
            "job_title_original": "Unknown",
            "job_title_short": "Unknown",
            "experience_years": "Unknown",
            "job_schedule_type": "Unknown",
            "seniority": "Unknown",
            "city": "Unknown",
            "state": "Unknown",
            "country": "Unknown",
            "degrees": [],
            "skills": [],
            "software": [],
            "company_name": "Unknown"
        }

    def process_description(self, description: str) -> Dict[str, Any]:
        """Procesa una descripción usando el LLM configurado"""
        print(f"🤖 Procesando descripción con {self.llm_type.upper()}...")
        
        if self.llm_type == "gemini":
            return self.call_gemini(description)
        elif self.llm_type == "ollama":
            return self.call_ollama(description)
        else:
            raise ValueError(f"LLM tipo '{self.llm_type}' no soportado")

    def read_csv(self, file_path: str) -> List[Dict[str, str]]:
        """Lee el CSV de entrada"""
        print(f"📖 Leyendo CSV: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        data = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        
        print(f"✅ Leídos {len(data)} registros")
        return data

    def process_data(self, input_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Procesa todos los datos de entrada"""
        print(f"🔄 Procesando {len(input_data)} registros...")
        
        processed_data = []
        
        for i, row in enumerate(input_data, 1):
            print(f"📝 Procesando registro {i}/{len(input_data)}")
            
            # Extraer datos del CSV
            title = row.get('title', '')
            company = row.get('company', '')
            location = row.get('location', '')
            description = row.get('description', '')
            
            # Procesar con LLM con manejo de errores mejorado
            try:
                llm_result = self.process_description(description)
                
                # Verificar si el resultado es válido (no todo Unknown)
                if llm_result.get('job_title_short') == 'Unknown' and all(
                    v == 'Unknown' or v == [] for k, v in llm_result.items() 
                    if k not in ['job_title_original', 'degrees', 'skills', 'software']
                ):
                    print(f"⚠️  Resultado sospechoso para registro {i}, reintentando...")
                    # Reintentar una vez más
                    time.sleep(2)
                    llm_result = self.process_description(description)
                
                # Combinar datos originales con resultados del LLM
                processed_row = {
                    'Job title (original)': title,
                    'Job title (short)': llm_result.get('job_title_short', 'Unknown'),
                    'Company': llm_result.get('company_name', company),
                    'Country': llm_result.get('country', 'Unknown'),
                    'State': llm_result.get('state', 'Unknown'),
                    'City': llm_result.get('city', 'Unknown'),
                    'Schedule type': llm_result.get('job_schedule_type', 'Unknown'),
                    'Experience years': llm_result.get('experience_years', 'Unknown'),
                    'Seniority': llm_result.get('seniority', 'Unknown'),
                    'Skills': '; '.join(llm_result.get('skills', [])),
                    'Degrees': '; '.join(llm_result.get('degrees', [])),
                    'Software': '; '.join(llm_result.get('software', []))
                }
                
                processed_data.append(processed_row)
                
            except Exception as e:
                print(f"❌ Error procesando registro {i}: {e}")
                # Agregar una fila con datos mínimos en lugar de todo Unknown
                processed_row = {
                    'Job title (original)': title,
                    'Job title (short)': 'Error',
                    'Company': company,
                    'Country': 'Unknown',
                    'State': 'Unknown',
                    'City': 'Unknown',
                    'Schedule type': 'Unknown',
                    'Experience years': 'Unknown',
                    'Seniority': 'Unknown',
                    'Skills': '',
                    'Degrees': '',
                    'Software': ''
                }
                processed_data.append(processed_row)
            
            # Pausa para evitar rate limiting (ajustado a 5 segundos)
            if i < len(input_data):
                time.sleep(5)
        
        print(f"✅ Procesamiento completado")
        return processed_data

    def write_csv(self, data: List[Dict[str, Any]], output_path: str):
        """Escribe el CSV de salida"""
        print(f"💾 Guardando CSV: {output_path}")
        
        if not data:
            print("⚠️  No hay datos para guardar")
            return
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        print(f"✅ CSV guardado exitosamente")

    def run(self, input_file: str, output_file: Optional[str] = None):
        """Ejecuta el procesamiento completo generando un CSV por cada 10 filas procesadas"""
        print("🚀 Iniciando DataPM Processor")
        print(f"📊 LLM: {self.llm_type.upper()}")
        
        # Determinar directorio de salida
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_file:
            # Si se proporcionó una ruta, usar su directorio; si es un directorio, usarlo tal cual
            output_dir = output_file if os.path.isdir(output_file) else os.path.dirname(output_file) or os.path.join(REPO_ROOT, "csv", "src", "csv_processed")
        else:
            output_dir = os.path.join(REPO_ROOT, "csv", "src", "csv_processed")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Leer datos de entrada
            input_data = self.read_csv(input_file)
            
            # Procesar y guardar en batches de 10 filas
            batch_size = 10
            total_rows = len(input_data)
            batch_count = 0
            for i in range(0, total_rows, batch_size):
                batch_count += 1
                batch_slice = input_data[i:i+batch_size]
                print(f"🔄 Procesando batch {batch_count} con {len(batch_slice)} filas...")
                processed_batch = self.process_data(batch_slice)
                batch_filename = f"{timestamp}_DataPM_result_batch_{batch_count}.csv"
                batch_output_path = os.path.join(output_dir, batch_filename)
                self.write_csv(processed_batch, batch_output_path)
            
            print(f"🎉 Procesamiento completado exitosamente!")
            print(f"📁 Archivos de salida en: {output_dir}")
            
        except Exception as e:
            print(f"❌ Error durante el procesamiento: {e}")
            sys.exit(1)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="DataPM Processor - Análisis de descripciones de trabajo")
    parser.add_argument("input_file", help="Archivo CSV o carpeta de entrada (si se pasa carpeta, se usa el CSV más reciente). Use 'latest' para tomar el más reciente de csv/src/scrapped")
    parser.add_argument("--output", "-o", help="Archivo CSV de salida (opcional)")
    parser.add_argument("--llm", choices=["gemini", "ollama"], default="gemini", 
                       help="Tipo de LLM a usar (default: gemini)")
    parser.add_argument("--api-key", help="API key para Gemini (requerido si --llm=gemini)")
    parser.add_argument("--ollama-url", default="http://localhost:11434", 
                       help="URL del servidor Ollama (default: http://localhost:11434)")
    
    args = parser.parse_args()
    
    # Validaciones
    if args.llm == "gemini" and not args.api_key:
        print("❌ Error: --api-key es requerido para Gemini")
        print("💡 Obtén tu API key en: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    # Resolver input: permitir directorio o palabra clave 'latest'
    def resolve_input_path(input_arg: str) -> str:
        # Si es directorio, tomar el CSV más reciente
        if os.path.isdir(input_arg):
            candidates = [
                os.path.join(input_arg, f) for f in os.listdir(input_arg)
                if f.lower().endswith('.csv')
            ]
            if not candidates:
                raise FileNotFoundError(f"No se encontraron CSV en la carpeta: {input_arg}")
            return max(candidates, key=os.path.getmtime)
        
        # Si es 'latest', usar carpeta por defecto csv/src/scrapped
        if input_arg.strip().lower() in {"latest", "auto"}:
            default_scrapped = os.path.join(REPO_ROOT, "csv", "src", "scrapped")
            candidates = [
                os.path.join(default_scrapped, f) for f in os.listdir(default_scrapped)
                if f.lower().endswith('.csv')
            ]
            if not candidates:
                raise FileNotFoundError(f"No se encontraron CSV en: {default_scrapped}")
            return max(candidates, key=os.path.getmtime)
        
        # En otro caso, tratar como archivo
        return input_arg

    resolved_input = resolve_input_path(args.input_file)

    # Crear y ejecutar procesador
    processor = DataPMProcessor(
        llm_type=args.llm,
        api_key=args.api_key,
        ollama_url=args.ollama_url
    )
    
    processor.run(resolved_input, args.output)


if __name__ == "__main__":
    main()

```

Voy a citar los fragmentos exactos del archivo para demostrar: 1) batching durante el procesamiento, 2) selección del input más reciente, y 3) que el LLM por defecto es Gemini.

- He ajustado el procesador para que:
  - Procese en batches de 10 y vaya generando un CSV por batch mientras avanza.
  - Use `csv/src/csv_processed` como carpeta de salida.
  - Permita usar el input más reciente de `csv/src/scrapped` con `latest` o pasando la carpeta.
  - Use por defecto Gemini como LLM (ya estaba), configurable por flag.

Bloques relevantes:
```398:431:csv_engine/engines/datapm_processor.py
def run(...):
    ...
    # Determinar directorio de salida
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ...
    output_dir = os.path.join(REPO_ROOT, "csv", "src", "csv_processed")
    ...
    # Procesar y guardar en batches de 10 filas
    batch_size = 10
    for i in range(0, total_rows, batch_size):
        batch_count += 1
        batch_slice = input_data[i:i+batch_size]
        processed_batch = self.process_data(batch_slice)
        batch_filename = f"{timestamp}_DataPM_result_batch_{batch_count}.csv"
        self.write_csv(processed_batch, os.path.join(output_dir, batch_filename))
```

```440:483:csv_engine/engines/datapm_processor.py
parser.add_argument("input_file", help="... Use 'latest' para ... csv/src/scrapped")
...
def resolve_input_path(input_arg: str) -> str:
    if os.path.isdir(input_arg): return max(..., key=os.path.getmtime)
    if input_arg in {"latest","auto"}:
        default_scrapped = os.path.join(REPO_ROOT, "csv", "src", "scrapped")
        return max(..., key=os.path.getmtime)
```

```442:444:csv_engine/engines/datapm_processor.py
parser.add_argument("--llm", choices=["gemini","ollama"], default="gemini", ...)
```

Ejemplos de ejecución:
- Tomar el último scrappeado y procesar con Gemini:
  - `python csv_engine/engines/datapm_processor.py latest --llm gemini --api-key TU_API_KEY`
- O desde la carpeta:
  - `python csv_engine/engines/datapm_processor.py csv/src/scrapped --llm gemini --api-key TU_API_KEY`

¿Quieres que fuerce Gemini siempre y elimine el flag `--llm`, o lo dejamos configurable?

```python
def run(...):
    ...
    # Determinar directorio de salida
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ...
    output_dir = os.path.join(REPO_ROOT, "csv", "src", "csv_processed")
    ...
    # Procesar y guardar en batches de 10 filas
    batch_size = 10
    for i in range(0, total_rows, batch_size):
        batch_count += 1
        batch_slice = input_data[i:i+batch_size]
        processed_batch = self.process_data(batch_slice)
        batch_filename = f"{timestamp}_DataPM_result_batch_{batch_count}.csv"
        self.write_csv(processed_batch, os.path.join(output_dir, batch_filename))
```

```python
parser.add_argument("input_file", help="... Use 'latest' para ... csv/src/scrapped")
...
def resolve_input_path(input_arg: str) -> str:
    if os.path.isdir(input_arg): return max(..., key=os.path.getmtime)
    if input_arg in {"latest","auto"}:
        default_scrapped = os.path.join(REPO_ROOT, "csv", "src", "scrapped")
        return max(..., key=os.path.getmtime)
```

```python
parser.add_argument("--llm", choices=["gemini","ollama"], default="gemini", ...)
```

---

**User**

Quiero ingresar en el campo KEYWORDS del grupo  --- CONFIGURACIÓN DE USUARIO --- en el programa:

D:\Work Work\Upwork\DataPM\scrapper\linkedin_selenium.py 

el input de búsqueda:

("Business Analyst" OR "Product Analyst" OR "Data Analyst" OR "BI Analyst") AND (analyst OR "product") NOT (senior OR lead OR director)

para aprovechar la búsqueda booleana de LinkedIn y que el código lea todo este input como un String y no dañen el código las comillas

---

**Cursor**

Voy a actualizar `KEYWORDS` con tu consulta booleana y a asegurar que se codifica correctamente en la URL para que las comillas no rompan la búsqueda. Luego valido lints y te muestro los fragmentos exactos modificados.

```python
# --- FUNCIÓN REUTILIZABLE PARA NAVEGAR ENTRE PÁGINAS ---
def go_to_page(driver, target_page, current_page=None):
    """Navega a la página target_page desde la página actual o desde current_page si se indica."""
    print(f"Navegando hasta la página: {target_page}")
    for p in range((current_page or 1) + 1, target_page + 1):
        next_selectors = [
            f"button[aria-label='Page {p}']",
            "button[aria-label='Next']",
            "button[aria-label='Siguiente']",
            "li.artdeco-pagination__indicator--active + li button",
            "button.artdeco-pagination__button--next"
        ]
        next_button = None
        for selector in next_selectors:
            try:
                next_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except TimeoutException:
                continue
        if next_button:
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            random_delay(1, 2)
            next_button.click()
            print(f"✅ Navegado a página {p}")
            random_delay(3, 5)
        else:
            print(f"🚫 No se encontró botón para la página {p}. Abortando navegación.")
            break
from selenium import webdriver
from datetime import datetime
import time
import csv
import random
import re
import os
from urllib.parse import quote_plus

# --- CONFIGURACIÓN DE USUARIO ---
import argparse
EMAIL = "11-10466@usb.ve"  
PASSWORD = "SanJudas.2011"  
KEYWORDS = '("Business Analyst" OR "Product Analyst" OR "Data Analyst" OR "BI Analyst") AND (analyst OR "product") NOT (senior OR lead OR director)'
LOCATION = "Spain"
REMOTE_FILTER = "2"   # 2 = Remote

# Argumentos para rango de páginas
parser = argparse.ArgumentParser(description="LinkedIn Scraper con rango de páginas")
parser.add_argument('--page-start', type=int, default=1, help='Página inicial a scrapear')
parser.add_argument('--page-end', type=int, default=3, help='Página final a scrapear')
args = parser.parse_args()
PAGE_START = args.page_start
PAGE_END = args.page_end

# --- CONFIGURACIÓN ANTI-DETECCIÓN ---
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ANTI-DETECCIÓN ---
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")

# Agregar User-Agent personalizado
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

# Deshabilitar WebGL para evitar fingerprinting
options.add_argument("--disable-webgl")
options.add_argument("--disable-3d-apis")

# Agregar preferencias adicionales
options.add_experimental_option("prefs", {
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False,
    "profile.default_content_setting_values.notifications": 2
})

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options)

# Ocultar que es automatizado
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def random_delay(min_seconds=1, max_seconds=3):
    """Pausa aleatoria para evitar detección"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def safe_find_element(driver, by, selector, timeout=10):
    """Busca elemento de forma segura con múltiples intentos"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    except TimeoutException:
        return None

def safe_find_elements(driver, by, selector, timeout=10):
    """Busca elementos de forma segura"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by, selector))
        )
    except TimeoutException:
        return []

def verify_login_success(driver):
    """Verifica si el login fue exitoso"""
    try:
        # Esperar a que aparezca el feed o el perfil
        WebDriverWait(driver, 15).until(
            EC.any_of(
                EC.url_contains("/feed/"),
                EC.url_contains("/mynetwork/"),
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.global-nav"))
            )
        )
        return True
    except TimeoutException:
        return False

def extract_text_safe(element, default=""):
    """Extrae texto de forma segura"""
    try:
        return element.text.strip() if element else default
    except:
        return default

def clean_text_for_csv(text):
    """Limpia texto para CSV"""
    if not text:
        return ""
    # Remover caracteres problemáticos y normalizar
    cleaned = re.sub(r'[\r\n\t]', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

# --- 1. LOGIN LINKEDIN CON VERIFICACIÓN ---
print("Iniciando login en LinkedIn...")
driver.get("https://www.linkedin.com/login")
random_delay(2, 4)

# Buscar campos de login
email_field = safe_find_element(driver, By.ID, "username")
password_field = safe_find_element(driver, By.ID, "password")

if not email_field or not password_field:
    print("❌ Error: No se encontraron los campos de login")
    driver.quit()
    exit(1)

# Llenar formulario de manera más humana
for char in EMAIL:
    email_field.send_keys(char)
    random_delay(0.1, 0.3)  # Pequeña pausa entre caracteres

random_delay(1, 2)  # Pausa antes de pasar a la contraseña

for char in PASSWORD:
    password_field.send_keys(char)
    random_delay(0.1, 0.3)  # Pequeña pausa entre caracteres

random_delay(1.5, 2.5)  # Pausa antes de dar enter
password_field.send_keys(Keys.RETURN)

# Verificar login exitoso con más tiempo de espera
print("Verificando login...")
if not verify_login_success(driver):
    print("❌ Error: Login fallido. Verifica credenciales o captcha")
    # Guardar screenshot para debug
    try:
        driver.save_screenshot("login_error.png")
        print("Se ha guardado una captura de pantalla en 'login_error.png'")
    except:
        pass
    driver.quit()
    exit(1)

print("✅ Login exitoso")

# --- 2. NAVEGAR A BÚSQUEDA CON VERIFICACIÓN ---
print("Navegando a resultados de búsqueda...")
encoded_keywords = quote_plus(KEYWORDS)
encoded_location = quote_plus(LOCATION)
search_url = (
    f"https://www.linkedin.com/jobs/search/"
    f"?keywords={encoded_keywords}"
    f"&location={encoded_location}"
    f"&f_WT={REMOTE_FILTER}"
    f"&distance=25"
)

driver.get(search_url)
random_delay(3, 5)

# Verificar que llegamos a la página de empleos
WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
)
job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")

if not job_cards:
    print("❌ Error: No se encontraron resultados de empleos")
    driver.quit()
    exit(1)

print(f"✅ Encontrados {len(job_cards)} empleos para procesar")

results = []
processed_count = 0


# --- NAVEGAR HASTA LA PÁGINA DE INICIO SI ES NECESARIO ---
if PAGE_START > 1:
    go_to_page(driver, PAGE_START, current_page=1)

for page in range(PAGE_START, PAGE_END + 1):
    print(f"\n📄 Procesando página {page}/{PAGE_END}...")
    
    # Esperar y localizar las tarjetas en la página actual
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
    )
    job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")
    
    if not job_cards:
        print(f"⚠️  No se encontraron ofertas en la página {page}. Saltando...")
        continue
    
    print(f"✅ Encontrados {len(job_cards)} empleos en página {page}")
    
    for idx, card in enumerate(job_cards, start=1):
        try:
            print(f"Procesando empleo {idx}/{len(job_cards)} (página {page})...")
            
            # Re-find el elemento para evitar StaleElementReferenceException
            card = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")[idx-1]
            
            # Scroll y click seguro
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            random_delay(1, 2)
            
            # Intentar click con múltiples estrategias
            try:
                card.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", card)
            except StaleElementReferenceException:
                # Re-find y reintentar
                card = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")[idx-1]
                card.click()

            # Esperar carga del panel de detalles con múltiples selectores
            detail_selectors = [
                "div.jobs-search__job-details--wrapper",
                "div.job-details-jobs-unified-top-card__container--two-pane",
                "div.jobs-unified-top-card__content"
            ]
            
            detail_loaded = False
            for selector in detail_selectors:
                if safe_find_element(driver, By.CSS_SELECTOR, selector, timeout=5):
                    detail_loaded = True
                    break
            
            if not detail_loaded:
                print(f"⚠️  Saltando empleo {page}-{idx}: No se cargaron los detalles")
                continue

            random_delay(1, 2)

            # Extraer datos con múltiples selectores de fallback
            title = ""
            title_selectors = [
                "div.job-details-jobs-unified-top-card__container--two-pane h1.t-24",
                "h1.t-24",
                "h1.job-details-jobs-unified-top-card__job-title",
                "h1"
            ]
            
            for selector in title_selectors:
                title_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if title_elem:
                    title = extract_text_safe(title_elem)
                    break
            
            company = ""
            company_selectors = [
                "div.job-details-jobs-unified-top-card__company-name a",
                "div.job-details-jobs-unified-top-card__company-name",
                "a[data-control-name='job_details_company_name']",
                "span.job-details-jobs-unified-top-card__company-name"
            ]
            
            for selector in company_selectors:
                company_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if company_elem:
                    company = extract_text_safe(company_elem)
                    break
            
            location = ""
            location_selectors = [
                "div.job-details-jobs-unified-top-card__primary-description-container span.tvm__text",
                "span.job-details-jobs-unified-top-card__bullet",
                "span[aria-label*='location']",
                "div.job-details-jobs-unified-top-card__primary-description-container"
            ]
            
            for selector in location_selectors:
                location_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if location_elem:
                    location = extract_text_safe(location_elem)
                    break
            
            description = ""
            description_selectors = [
                "article.jobs-description__container div.jobs-description-content__text--stretch",
                "div.jobs-description-content__text",
                "div.jobs-box__html-content",
                "div[data-job-description]"
            ]
            
            for selector in description_selectors:
                desc_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if desc_elem:
                    description = extract_text_safe(desc_elem)
                    break

            # Validar que tenemos al menos título y empresa
            if not title or not company:
                print(f"⚠️  Saltando empleo {page}-{idx}: Datos insuficientes")
                continue
        
            # Limpiar datos para CSV
            title = clean_text_for_csv(title)
            company = clean_text_for_csv(company)
            location = clean_text_for_csv(location)
            description = clean_text_for_csv(description)

            print(f"✅ [{page}-{idx}] {title[:50]}... | {company} | {location}")
            
            results.append({
                "title": title,
                "company": company,
                "location": location,
                "description": description
            })
            
            processed_count += 1
            random_delay(1, 3)  # Pausa entre empleos

        except Exception as e:
            print(f"❌ Error procesando empleo #{page}-{idx}: {str(e)}")
            continue
    
    # Buscar y hacer clic en "Siguiente" para la siguiente página
    if page < PAGE_END:  # No intentar navegar después de la última página configurada
        try:
            go_to_page(driver, page + 1, current_page=page)
        except Exception as e:
            print(f"❌ Error navegando a página {page + 1}: {str(e)}")
            break

# --- 4. GUARDAR EN CSV CON VALIDACIÓN ---
if results:
    # Crear directorio de salida absoluto: <repo_root>/csv/src/scrapped
    scrapped_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "csv",
        "src",
        "scrapped",
    )
    os.makedirs(scrapped_dir, exist_ok=True)

    # Guardar TODO en un único archivo CSV por ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scrape_filename = os.path.join(scrapped_dir, f"{timestamp}_linkedin_jobs.csv")

    try:
        with open(scrape_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "company", "location", "description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ {len(results)} ofertas guardadas en {scrape_filename}")
        print(f"✅ Proceso completado: {processed_count} ofertas totales procesadas")
    except Exception as e:
        print(f"❌ Error guardando CSV: {str(e)}")
else:
    print("❌ No se extrajo ningún empleo válido")

driver.quit()
```

- Actualicé `KEYWORDS` con tu búsqueda booleana y codifiqué la URL para evitar problemas con comillas.

Bloques relevantes:
```39:46:scrapper/linkedin_selenium.py
from urllib.parse import quote_plus
...
EMAIL = "11-10466@usb.ve"  
PASSWORD = "SanJudas.2011"  
KEYWORDS = '("Business Analyst" OR "Product Analyst" OR "Data Analyst" OR "BI Analyst") AND (analyst OR "product") NOT (senior OR lead OR director)'
LOCATION = "Spain"
REMOTE_FILTER = "2"   # 2 = Remote
```

```197:205:scrapper/linkedin_selenium.py
print("Navegando a resultados de búsqueda...")
encoded_keywords = quote_plus(KEYWORDS)
encoded_location = quote_plus(LOCATION)
search_url = (
    f"https://www.linkedin.com/jobs/search/"
    f"?keywords={encoded_keywords}"
    f"&location={encoded_location}"
    f"&f_WT={REMOTE_FILTER}"
    f"&distance=25"
)
```

- Así LinkedIn recibirá el string completo correctamente. ¿Quieres que haga lo mismo con `LOCATION` si deseas una búsqueda con booleanos allí también?

```python
from urllib.parse import quote_plus
...
EMAIL = "11-10466@usb.ve"  
PASSWORD = "SanJudas.2011"  
KEYWORDS = '("Business Analyst" OR "Product Analyst" OR "Data Analyst" OR "BI Analyst") AND (analyst OR "product") NOT (senior OR lead OR director)'
LOCATION = "Spain"
REMOTE_FILTER = "2"   # 2 = Remote
```

```python
print("Navegando a resultados de búsqueda...")
encoded_keywords = quote_plus(KEYWORDS)
encoded_location = quote_plus(LOCATION)
search_url = (
    f"https://www.linkedin.com/jobs/search/"
    f"?keywords={encoded_keywords}"
    f"&location={encoded_location}"
    f"&f_WT={REMOTE_FILTER}"
    f"&distance=25"
)
```

---

**User**

Quisiera que hagas un análisis preliminar del nuevo scrap generado:

D:\Work Work\Upwork\DataPM\csv\src\scrapped\20250818_113052_linkedin_jobs.csv

y con tu propio LLM hagas una ampliación del schema:

D:\Work Work\Upwork\DataPM\csv_engine\utils\config.py

para la normalización, especialmente de job titles, skills y software que genera el motor de procesamiento, procurando:

1) Evitar redundancias como el acompañamiento de adjetivos que describan una rama de industria específica o nivel de seniority, sólo específicamente ítems que no hayan sido considerados previamente para el schema actual. 

---

**Cursor**

Voy a revisar el CSV nuevo y el archivo `csv_engine/utils/config.py` en paralelo para identificar brechas y proponer ampliaciones seguras del schema evitando redundancias. Luego haré los edits necesarios.

Voy a abrir una muestra del CSV scrappeado y el archivo de configuración para identificar huecos en listas y aplicar las ampliaciones necesarias en `csv_engine/utils/config.py`. Luego haré los edits.

Voy a escanear el CSV para detectar menciones de herramientas y roles clave que falten en el schema, y luego actualizaré `csv_engine/utils/config.py` con adiciones no redundantes.

```python
*** Begin Patch
*** Update File: csv_engine/utils/config.py
@@
 NORMALIZATION_SCHEMA = {
     "job_title_short": [
@@
-        # Data Roles
-        "Data Analyst", "Data Scientist", "Data Engineer", "Data Architect", 
-        "Data Manager", "Data Lead", "Data Specialist", "Business Intelligence Analyst", 
-        "BI Analyst", "Analytics Manager", "Machine Learning Engineer", "ML Engineer", 
-        "AI Engineer", "AI Specialist",
+        # Data Roles
+        "Data Analyst", "Data Scientist", "Data Engineer", "Data Architect", 
+        "Data Manager", "Data Lead", "Data Specialist", "Business Intelligence Analyst", 
+        "BI Analyst", "Analytics Manager", "Machine Learning Engineer", "ML Engineer", 
+        "AI Engineer", "AI Specialist", "Analytics Engineer", "Growth Analyst", 
+        "Insights Analyst", "Experimentation Analyst", "BI Engineer", "Data Product Manager",
@@
-        # Project & Business Roles
-        "Project Manager", "Program Manager", "Project Coordinator", "Project Lead",
-        "Business Analyst", "Process Designer", "Process Manager", "Process Analyst",
-        "Business Intelligence Manager", "Strategy Manager", "Operations Manager",
+        # Project & Business Roles
+        "Project Manager", "Program Manager", "Project Coordinator", "Project Lead",
+        "Business Analyst", "Process Designer", "Process Manager", "Process Analyst",
+        "Business Intelligence Manager", "Strategy Manager", "Operations Manager",
+        "Product Operations",
@@
     "skills": [
@@
-        # Data & Analytics
-        "Data Analysis", "Data Visualization", "Statistical Analysis", "Predictive Analytics",
-        "Machine Learning", "Deep Learning", "AI", "Natural Language Processing", "NLP",
-        "Business Intelligence", "Data Mining", "Data Modeling", "Data Governance",
-        "A/B Testing", "Hypothesis Testing", "Quantitative Research", "Qualitative Research",
+        # Data & Analytics
+        "Data Analysis", "Data Visualization", "Statistical Analysis", "Predictive Analytics",
+        "Machine Learning", "Deep Learning", "AI", "Natural Language Processing", "NLP",
+        "Business Intelligence", "Data Mining", "Data Modeling", "Data Governance",
+        "A/B Testing", "Hypothesis Testing", "Quantitative Research", "Qualitative Research",
+        "Experimentation", "Experiment Design", "Causal Inference", "Cohort Analysis",
+        "Funnel Analysis", "Retention Analysis", "Attribution Modeling",
@@
-        # Product Management
-        "Product Management", "Product Strategy", "Product Development", "Product Launch",
-        "Product Roadmapping", "Feature Prioritization", "User Stories", "Requirements Gathering",
-        "Market Research", "Competitive Analysis", "Product Analytics", "Growth Hacking",
+        # Product Management
+        "Product Management", "Product Strategy", "Product Development", "Product Launch",
+        "Product Roadmapping", "Feature Prioritization", "User Stories", "Requirements Gathering",
+        "Market Research", "Competitive Analysis", "Product Analytics", "Growth Hacking",
+        "Tracking Plan", "Event Taxonomy", "Event Tracking", "Instrumentation", "Feature Flagging",
@@
     "software": [
@@
-        # Data & Analytics Tools
-        "Tableau", "Power BI", "Looker", "QlikView", "Qlik Sense", "MicroStrategy",
-        "Google Analytics", "Google Data Studio", "Mixpanel", "Amplitude",
-        "Segment", "Snowflake", "Databricks", "Apache Spark", "Hadoop",
-        "Apache Kafka", "Apache Airflow", "dbt", "Fivetran", "Stitch",
+        # Data & Analytics Tools
+        "Tableau", "Power BI", "Looker", "QlikView", "Qlik Sense", "MicroStrategy",
+        "Google Analytics", "Google Data Studio", "Looker Studio", "Mixpanel", "Amplitude",
+        "PostHog", "Heap", "FullStory", "Hotjar", "Pendo",
+        "Segment", "RudderStack", "Snowflake", "Databricks", "Apache Spark", "Hadoop",
+        "Apache Kafka", "Apache Airflow", "Airbyte", "dbt", "Fivetran", "Stitch",
+        "Apache Superset", "Metabase", "Mode Analytics",
@@
-        # Cloud Platforms
-        "AWS", "Azure", "GCP", "DigitalOcean", "Heroku", "Vercel", "Netlify",
-        "Cloudflare", "Linode", "Vultr", "IBM Cloud", "Oracle Cloud",
+        # Cloud Platforms
+        "AWS", "Azure", "GCP", "DigitalOcean", "Heroku", "Vercel", "Netlify",
+        "Cloudflare", "Linode", "Vultr", "IBM Cloud", "Oracle Cloud",
+        
+        # Data Warehouses
+        "BigQuery", "Redshift",
@@
-        # Project Management & Collaboration
-        "Jira", "Confluence", "Atlassian", "Asana", "Trello", "Monday.com",
-        "ClickUp", "Notion", "Slack", "Microsoft Teams", "Discord", "Zoom",
-        "Google Meet", "WebEx", "Loom", "Miro", "Figma", "Lucidchart",
+        # Project Management & Collaboration
+        "Jira", "Confluence", "Atlassian", "Asana", "Trello", "Monday.com",
+        "ClickUp", "Notion", "Slack", "Microsoft Teams", "Discord", "Zoom",
+        "Google Meet", "WebEx", "Loom", "Miro", "Figma", "Lucidchart",
+        
+        # Experimentation & Feature Flags
+        "Optimizely", "VWO", "LaunchDarkly",
*** End Patch
```

```python
*** Begin Patch
*** Update File: csv_engine/utils/config.py
@@
-        "AI Engineer", "AI Specialist",
+        "AI Engineer", "AI Specialist", "Analytics Engineer", "Growth Analyst", 
+        "Insights Analyst", "Experimentation Analyst", "BI Engineer", "Data Product Manager",
@@
-        "Business Intelligence Manager", "Strategy Manager", "Operations Manager",
+        "Business Intelligence Manager", "Strategy Manager", "Operations Manager",
+        "Product Operations",
@@
-        "A/B Testing", "Hypothesis Testing", "Quantitative Research", "Qualitative Research",
+        "A/B Testing", "Hypothesis Testing", "Quantitative Research", "Qualitative Research",
+        "Experimentation", "Experiment Design", "Causal Inference", "Cohort Analysis",
+        "Funnel Analysis", "Retention Analysis", "Attribution Modeling",
@@
-        "Market Research", "Competitive Analysis", "Product Analytics", "Growth Hacking",
+        "Market Research", "Competitive Analysis", "Product Analytics", "Growth Hacking",
+        "Tracking Plan", "Event Taxonomy", "Event Tracking", "Instrumentation", "Feature Flagging",
@@
-        "Google Analytics", "Google Data Studio", "Mixpanel", "Amplitude",
-        "Segment", "Snowflake", "Databricks", "Apache Spark", "Hadoop",
-        "Apache Kafka", "Apache Airflow", "dbt", "Fivetran", "Stitch",
+        "Google Analytics", "Google Data Studio", "Looker Studio", "Mixpanel", "Amplitude",
+        "PostHog", "Heap", "FullStory", "Hotjar", "Pendo",
+        "Segment", "RudderStack", "Snowflake", "Databricks", "Apache Spark", "Hadoop",
+        "Apache Kafka", "Apache Airflow", "Airbyte", "dbt", "Fivetran", "Stitch",
+        "Apache Superset", "Metabase", "Mode Analytics",
@@
-        "Cloudflare", "Linode", "Vultr", "IBM Cloud", "Oracle Cloud",
+        "Cloudflare", "Linode", "Vultr", "IBM Cloud", "Oracle Cloud",
+
+        # Data Warehouses
+        "BigQuery", "Redshift",
@@
-        "Google Meet", "WebEx", "Loom", "Miro", "Figma", "Lucidchart",
+        "Google Meet", "WebEx", "Loom", "Miro", "Figma", "Lucidchart",
+
+        # Experimentation & Feature Flags
+        "Optimizely", "VWO", "LaunchDarkly",
*** End Patch
```

```python
#!/usr/bin/env python3
"""
Configuración centralizada para DataPM Processor
"""

import os
from typing import Dict, List

# Configuración de LLMs
LLM_CONFIG = {
    "gemini": {
        "model": "gemini-2.0-flash-exp",
        "max_tokens": 100000,
        "temperature": 0.1,  # Baja temperatura para respuestas más consistentes
    },
    "ollama": {
        "model": "llama3.2:3b",  # Modelo por defecto
        "url": "http://localhost:11434",
        "timeout": 30,
    }
}

# Schema de normalización expandido para mayor cobertura
NORMALIZATION_SCHEMA = {
    "job_title_short": [
        # Product Management
        "Product Manager", "Product Owner", "Product Lead", "Product Director", 
        "VP of Product", "Head of Product", "Product Specialist", "Product Coordinator", 
        "Product Analyst", "Product Associate",
        
        # Data Roles
        "Data Analyst", "Data Scientist", "Data Engineer", "Data Architect", 
        "Data Manager", "Data Lead", "Data Specialist", "Business Intelligence Analyst", 
        "BI Analyst", "Analytics Manager", "Machine Learning Engineer", "ML Engineer", 
        "AI Engineer", "AI Specialist", "Analytics Engineer", "Growth Analyst", 
        "Insights Analyst", "Experimentation Analyst", "BI Engineer", "Data Product Manager",
        
        # Design Roles
        "UX/UI Designer", "UX Designer", "UI Designer", "Product Designer", 
        "Design Lead", "Design Manager", "Creative Designer", "Visual Designer", 
        "Graphic Designer", "Digital Designer", "Web Designer", "Interaction Designer", 
        "Service Designer", "Design Director", "Head of Design", "VP of Design",
        
        # Engineering Roles
        "Software Engineer", "Full Stack Developer", "Frontend Developer", "Backend Developer",
        "DevOps Engineer", "Site Reliability Engineer", "Cloud Engineer", "Systems Engineer", 
        "QA Engineer", "Test Engineer", "Automation Engineer", "Mobile Developer", 
        "iOS Developer", "Android Developer", "Web Developer",
        
        # Marketing Roles
        "Marketing Specialist", "Marketing Manager", "Marketing Analyst",
        "Digital Marketing Specialist", "Content Marketing Specialist",
        "Product Marketing Manager", "Product Marketing Specialist",
        "Growth Marketing Manager", "Brand Manager", "Marketing Coordinator",
        "Marketing Assistant", "Marketing Director", "VP of Marketing",
        
        # Project & Business Roles
        "Project Manager", "Program Manager", "Project Coordinator", "Project Lead",
        "Business Analyst", "Process Designer", "Process Manager", "Process Analyst",
        "Business Intelligence Manager", "Strategy Manager", "Operations Manager",
        "Product Operations",
        
        # IT & Technical Roles
        "IT Analyst", "IT Manager", "IT Specialist", "IT Coordinator",
        "System Administrator", "Network Engineer", "Security Engineer",
        "Information Security Analyst", "Technical Support Specialist",
        "Technical Writer", "Technical Project Manager",
        
        # Compliance & Quality
        "Product Compliance Specialist", "Compliance Manager", "Compliance Analyst",
        "Quality Assurance Specialist", "Quality Manager", "Quality Analyst",
        "Regulatory Affairs Specialist", "Auditor", "Risk Analyst",
        
        # Sales & Customer Success
        "Sales Manager", "Sales Specialist", "Sales Representative",
        "Account Manager", "Customer Success Manager", "Customer Success Specialist",
        "Business Development Manager", "Partnership Manager",
        
        # Research & Analytics
        "Research Analyst", "Market Research Analyst", "User Researcher",
        "Research Manager", "Analytics Specialist", "Performance Analyst",
        
        # Other Common Roles
        "Consultant", "Advisor", "Specialist", "Coordinator", "Assistant", "Associate",
        "Manager", "Director", "VP", "Head of", "Lead", "Principal", "Staff", "Other"
    ],
    "experience_years": ["0-3", "3-5", "5+"],
    "job_schedule_type": ["Full-time", "Part-time", "Contract", "Internship", "Unknown"],
    "seniority": ["Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"],
    "degrees": [
        "Bachelor's Degree", "Master's Degree", "PhD", "Associate's Degree", 
        "Higher Education", "Engineering", "Automotive Engineering", 
        "Vocational Training", "Other"
    ],
    "skills": [
        # Project Management & Methodology
        "Project Management", "Agile", "Scrum", "Kanban", "Lean", "Six Sigma",
        "Waterfall", "SAFe", "DevOps", "CI/CD", "SDLC", "Product Lifecycle Management",
        
        # Data & Analytics
        "Data Analysis", "Data Visualization", "Statistical Analysis", "Predictive Analytics",
        "Machine Learning", "Deep Learning", "AI", "Natural Language Processing", "NLP",
        "Business Intelligence", "Data Mining", "Data Modeling", "Data Governance",
        "A/B Testing", "Hypothesis Testing", "Quantitative Research", "Qualitative Research",
        
        # Design & UX
        "UI/UX Design", "User Research", "User-Centered Design", "Design Thinking",
        "Wireframing", "Prototyping", "Visual Design", "Interaction Design",
        "Information Architecture", "Usability Testing", "Accessibility Design",
        "Design Systems", "Brand Design", "Graphic Design", "Digital Design",
        
        # Product Management
        "Product Management", "Product Strategy", "Product Development", "Product Launch",
        "Product Roadmapping", "Feature Prioritization", "User Stories", "Requirements Gathering",
        "Market Research", "Competitive Analysis", "Product Analytics", "Growth Hacking",
        
        # Marketing & Sales
        "Marketing", "Digital Marketing", "Content Marketing", "Social Media Marketing",
        "Email Marketing", "SEO", "SEM", "PPC", "Brand Management", "Marketing Analytics",
        "Sales", "Sales Strategy", "Customer Relationship Management", "CRM",
        "Lead Generation", "Account Management", "Business Development",
        
        # Technical Skills
        "API", "REST APIs", "GraphQL", "Microservices", "Cloud Computing", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "Infrastructure as Code", "System Design", "Architecture",
        "Database Design", "SQL", "NoSQL", "Data Warehousing", "ETL", "Data Pipeline",
        
        # Programming & Development
        "Programming", "Software Development", "Web Development", "Mobile Development",
        "Frontend Development", "Backend Development", "Full Stack Development",
        "Object-Oriented Programming", "Functional Programming", "Test-Driven Development",
        "Code Review", "Version Control", "Git", "Debugging", "Performance Optimization",
        
        # Business & Soft Skills
        "Communication", "Problem Solving", "Critical Thinking", "Analytical Thinking",
        "Business Acumen", "Strategic Thinking", "Leadership", "Team Management",
        "Cross-functional Collaboration", "Stakeholder Management", "Presentation Skills",
        "Negotiation", "Conflict Resolution", "Time Management", "Organization",
        
        # Industry-Specific
        "Regulatory Compliance", "Quality Assurance", "Quality Control", "Process Optimization",
        "Supply Chain Management", "Logistics", "Healthcare Knowledge", "Financial Analysis",
        "Risk Management", "Auditing", "Document Management", "Technical Writing",
        "Training", "Mentoring", "Coaching",
        
        # Tools & Platforms
        "Microsoft Office", "Google Workspace", "Slack", "Teams", "Zoom", "WebEx",
        "Customer Support", "Help Desk", "Troubleshooting", "System Administration",
        "Network Administration", "Security", "Cybersecurity", "Information Security"
    ],
    "software": [
        # Programming Languages
        "Python", "R", "SQL", "JavaScript", "TypeScript", "Java", "C#", "C++", "C",
        "Go", "Rust", "Scala", "PHP", "Ruby", "Swift", "Kotlin", "Dart", "Perl",
        "MATLAB", "Julia", "VBA", "PowerShell", "Bash", "Shell Scripting",
        
        # Web Technologies
        "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Express.js",
        "Django", "Flask", "FastAPI", "Spring Boot", "Laravel", "Ruby on Rails",
        "Next.js", "Nuxt.js", "Gatsby", "Vercel", "Netlify", "WordPress",
        
        # Databases
        "MySQL", "PostgreSQL", "SQL Server", "Oracle", "MongoDB", "Redis",
        "Cassandra", "DynamoDB", "Firebase", "Supabase", "PlanetScale",
        "Elasticsearch", "InfluxDB", "Neo4j", "SQLite",
        
        # Cloud Platforms
        "AWS", "Azure", "GCP", "DigitalOcean", "Heroku", "Vercel", "Netlify",
        "Cloudflare", "Linode", "Vultr", "IBM Cloud", "Oracle Cloud",
        
        # Data & Analytics Tools
        "Tableau", "Power BI", "Looker", "QlikView", "Qlik Sense", "MicroStrategy",
        "Google Analytics", "Google Data Studio", "Mixpanel", "Amplitude",
        "Segment", "Snowflake", "Databricks", "Apache Spark", "Hadoop",
        "Apache Kafka", "Apache Airflow", "dbt", "Fivetran", "Stitch",
        
        # Machine Learning & AI
        "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "XGBoost", "LightGBM",
        "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly", "Bokeh",
        "Jupyter", "Google Colab", "Databricks", "Hugging Face", "OpenAI API",
        "Anthropic API", "LangChain", "Streamlit", "Gradio",
        
        # Design & Creative Tools
        "Figma", "Sketch", "Adobe XD", "Adobe Creative Suite", "Photoshop",
        "Illustrator", "InDesign", "Premiere Pro", "After Effects", "Framer",
        "InVision", "Marvel", "Principle", "Lottie", "Canva", "Miro", "Whimsical",
        
        # Project Management & Collaboration
        "Jira", "Confluence", "Atlassian", "Asana", "Trello", "Monday.com",
        "ClickUp", "Notion", "Slack", "Microsoft Teams", "Discord", "Zoom",
        "Google Meet", "WebEx", "Loom", "Miro", "Figma", "Lucidchart",
        
        # Development Tools
        "Git", "GitHub", "GitLab", "Bitbucket", "VS Code", "IntelliJ IDEA",
        "PyCharm", "WebStorm", "Sublime Text", "Atom", "Vim", "Emacs",
        "Docker", "Kubernetes", "Jenkins", "CircleCI", "GitHub Actions",
        "GitLab CI", "Travis CI", "SonarQube", "Postman", "Insomnia",
        
        # Business Software
        "Microsoft Office", "Excel", "Word", "PowerPoint", "Outlook",
        "Google Workspace", "Google Sheets", "Google Docs", "Google Slides",
        "Salesforce", "HubSpot", "Pipedrive", "Zoho", "SAP", "Oracle",
        "QuickBooks", "Xero", "Stripe", "PayPal", "Shopify", "WooCommerce",
        
        # CRM & Marketing
        "Salesforce", "HubSpot", "Pipedrive", "Zoho CRM", "Freshsales",
        "Mailchimp", "Constant Contact", "SendGrid", "Klaviyo", "ConvertKit",
        "Hootsuite", "Buffer", "Sprout Social", "Later", "Canva",
        
        # Engineering & CAD
        "SolidWorks", "AutoCAD", "Fusion 360", "Rhino", "Keyshot", "C4D",
        "Blender", "Maya", "3ds Max", "Revit", "SketchUp", "TinkerCAD",
        
        # Other Tools
        "OneDrive", "Google Drive", "Dropbox", "Box", "SharePoint",
        "IMDS", "Flow", "Zapier", "IFTTT", "Make.com", "Airtable",
        "Notion", "Obsidian", "Roam Research", "Logseq"
    ]
}

# Configuración de archivos
FILE_CONFIG = {
    "input_dir": "csv",
    "output_dir": "csv/archive",
    "default_input": "linkedin_jobs_make.csv",
    "output_prefix": "DataPM_result",
    "encoding": "utf-8",
    "delimiter": ",",
}

# Configuración de procesamiento
PROCESSING_CONFIG = {
    "batch_size": 1,  # Procesar uno por uno para evitar rate limiting
    "delay_between_requests": 1,  # Segundos entre requests
    "max_retries": 3,  # Máximo de reintentos por request
    "timeout": 30,  # Timeout por request
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "file": "datapm.log",
}

# Configuración de países y estados
LOCATION_CONFIG = {
    "countries": [
        "United States", "Spain", "Mexico", "United Kingdom", "Germany", 
        "France", "Panamá", "Venezuela", "European Union", "Unknown"
    ],
    "us_states": {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming"
    },
    "ca_provinces": {
        "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba", "NB": "New Brunswick",
        "NL": "Newfoundland and Labrador", "NS": "Nova Scotia", "NT": "Northwest Territories",
        "NU": "Nunavut", "ON": "Ontario", "PE": "Prince Edward Island", "QC": "Quebec",
        "SK": "Saskatchewan", "YT": "Yukon"
    }
}

def get_api_key(llm_type: str) -> str:
    """Obtiene la API key desde variables de entorno"""
    if llm_type == "gemini":
        return os.getenv('GEMINI_API_KEY', '')
    return ''

def get_ollama_url() -> str:
    """Obtiene la URL de Ollama desde variables de entorno"""
    return os.getenv('OLLAMA_URL', 'http://localhost:11434')

def get_output_filename(prefix: str = None) -> str:
    """Genera un nombre de archivo de salida con timestamp"""
    from datetime import datetime
    
    if not prefix:
        prefix = FILE_CONFIG["output_prefix"]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{prefix}.csv"

def get_full_output_path(filename: str = None) -> str:
    """Obtiene la ruta completa del archivo de salida"""
    if not filename:
        filename = get_output_filename()
    
    output_dir = FILE_CONFIG["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    return os.path.join(output_dir, filename)

def get_full_input_path(filename: str = None) -> str:
    """Obtiene la ruta completa del archivo de entrada"""
    if not filename:
        filename = FILE_CONFIG["default_input"]
    
    input_dir = FILE_CONFIG["input_dir"]
    return os.path.join(input_dir, filename)

# Configuración de prompts
PROMPT_TEMPLATES = {
    "system": """You are a strict data extractor and standardizer. You MUST return ONLY a valid JSON object and nothing else.
The JSON must follow this schema:

job_title_original (string)

job_title_short (string, normalized to one of these values: {job_titles})

experience_years (string, normalized to one of these formats: "0-3" for less than 3 years, "3-5" for ranges, "5+" for 5 or more years)

job_schedule_type (string, normalized to one of these values: {schedule_types})

seniority (string, normalized to one of these values: {seniority_levels})

city (string, normalized to proper case, e.g., "New York", "Madrid". If not found, use "Unknown".)

state (string, normalized to two-letter abbreviation if in the US/CA, e.g., "NY", "CA". If not in the US/CA or not found, use "Unknown".)

country (string, normalized to proper case, e.g., "United States", "Spain", "Mexico", "United Kingdom", "Germany", "France", "Panamá", "Venezuela", "European Union", "Unknown")

degrees (array of strings, normalized to one of these values: {degrees})

skills (array of strings, normalized to a fixed set of values like: {skills})

software (array of strings, normalized to a fixed set of values like: {software})

company_name (string)

If you cannot determine a value, use "Unknown" for strings and blank space for arrays, data slot must be empty. No extra text, no markdown, no explanation.""",
    
    "user": """INPUT: {{"text":"{description}"}}
TASK: Analyze INPUT.text and return the JSON according to the schema in the system instructions."""
}

def get_system_prompt() -> str:
    """Obtiene el prompt del sistema con valores normalizados"""
    return PROMPT_TEMPLATES["system"].format(
        job_titles=NORMALIZATION_SCHEMA["job_title_short"],
        schedule_types=NORMALIZATION_SCHEMA["job_schedule_type"],
        seniority_levels=NORMALIZATION_SCHEMA["seniority"],
        degrees=NORMALIZATION_SCHEMA["degrees"],
        skills=NORMALIZATION_SCHEMA["skills"],
        software=NORMALIZATION_SCHEMA["software"]
    )

def get_user_prompt(description: str) -> str:
    """Obtiene el prompt del usuario"""
    return PROMPT_TEMPLATES["user"].format(description=description)

```

```python
#!/usr/bin/env python3
"""
Configuración centralizada para DataPM Processor
"""

import os
from typing import Dict, List

# Configuración de LLMs
LLM_CONFIG = {
    "gemini": {
        "model": "gemini-2.0-flash-exp",
        "max_tokens": 100000,
        "temperature": 0.1,  # Baja temperatura para respuestas más consistentes
    },
    "ollama": {
        "model": "llama3.2:3b",  # Modelo por defecto
        "url": "http://localhost:11434",
        "timeout": 30,
    }
}

# Schema de normalización expandido para mayor cobertura
NORMALIZATION_SCHEMA = {
    "job_title_short": [
        # Product Management
        "Product Manager", "Product Owner", "Product Lead", "Product Director", 
        "VP of Product", "Head of Product", "Product Specialist", "Product Coordinator", 
        "Product Analyst", "Product Associate",
        
        # Data Roles
        "Data Analyst", "Data Scientist", "Data Engineer", "Data Architect", 
        "Data Manager", "Data Lead", "Data Specialist", "Business Intelligence Analyst", 
        "BI Analyst", "Analytics Manager", "Machine Learning Engineer", "ML Engineer", 
        "AI Engineer", "AI Specialist", "Analytics Engineer", "Growth Analyst", 
        "Insights Analyst", "Experimentation Analyst", "BI Engineer", "Data Product Manager",
        
        # Design Roles
        "UX/UI Designer", "UX Designer", "UI Designer", "Product Designer", 
        "Design Lead", "Design Manager", "Creative Designer", "Visual Designer", 
        "Graphic Designer", "Digital Designer", "Web Designer", "Interaction Designer", 
        "Service Designer", "Design Director", "Head of Design", "VP of Design",
        
        # Engineering Roles
        "Software Engineer", "Full Stack Developer", "Frontend Developer", "Backend Developer",
        "DevOps Engineer", "Site Reliability Engineer", "Cloud Engineer", "Systems Engineer", 
        "QA Engineer", "Test Engineer", "Automation Engineer", "Mobile Developer", 
        "iOS Developer", "Android Developer", "Web Developer",
        
        # Marketing Roles
        "Marketing Specialist", "Marketing Manager", "Marketing Analyst",
        "Digital Marketing Specialist", "Content Marketing Specialist",
        "Product Marketing Manager", "Product Marketing Specialist",
        "Growth Marketing Manager", "Brand Manager", "Marketing Coordinator",
        "Marketing Assistant", "Marketing Director", "VP of Marketing",
        
        # Project & Business Roles
        "Project Manager", "Program Manager", "Project Coordinator", "Project Lead",
        "Business Analyst", "Process Designer", "Process Manager", "Process Analyst",
        "Business Intelligence Manager", "Strategy Manager", "Operations Manager",
        "Product Operations",
        
        # IT & Technical Roles
        "IT Analyst", "IT Manager", "IT Specialist", "IT Coordinator",
        "System Administrator", "Network Engineer", "Security Engineer",
        "Information Security Analyst", "Technical Support Specialist",
        "Technical Writer", "Technical Project Manager",
        
        # Compliance & Quality
        "Product Compliance Specialist", "Compliance Manager", "Compliance Analyst",
        "Quality Assurance Specialist", "Quality Manager", "Quality Analyst",
        "Regulatory Affairs Specialist", "Auditor", "Risk Analyst",
        
        # Sales & Customer Success
        "Sales Manager", "Sales Specialist", "Sales Representative",
        "Account Manager", "Customer Success Manager", "Customer Success Specialist",
        "Business Development Manager", "Partnership Manager",
        
        # Research & Analytics
        "Research Analyst", "Market Research Analyst", "User Researcher",
        "Research Manager", "Analytics Specialist", "Performance Analyst",
        
        # Other Common Roles
        "Consultant", "Advisor", "Specialist", "Coordinator", "Assistant", "Associate",
        "Manager", "Director", "VP", "Head of", "Lead", "Principal", "Staff", "Other"
    ],
    "experience_years": ["0-3", "3-5", "5+"],
    "job_schedule_type": ["Full-time", "Part-time", "Contract", "Internship", "Unknown"],
    "seniority": ["Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"],
    "degrees": [
        "Bachelor's Degree", "Master's Degree", "PhD", "Associate's Degree", 
        "Higher Education", "Engineering", "Automotive Engineering", 
        "Vocational Training", "Other"
    ],
    "skills": [
        # Project Management & Methodology
        "Project Management", "Agile", "Scrum", "Kanban", "Lean", "Six Sigma",
        "Waterfall", "SAFe", "DevOps", "CI/CD", "SDLC", "Product Lifecycle Management",
        
        # Data & Analytics
        "Data Analysis", "Data Visualization", "Statistical Analysis", "Predictive Analytics",
        "Machine Learning", "Deep Learning", "AI", "Natural Language Processing", "NLP",
        "Business Intelligence", "Data Mining", "Data Modeling", "Data Governance",
        "A/B Testing", "Hypothesis Testing", "Quantitative Research", "Qualitative Research",
        "Experimentation", "Experiment Design", "Causal Inference", "Cohort Analysis",
        "Funnel Analysis", "Retention Analysis", "Attribution Modeling",
        
        # Design & UX
        "UI/UX Design", "User Research", "User-Centered Design", "Design Thinking",
        "Wireframing", "Prototyping", "Visual Design", "Interaction Design",
        "Information Architecture", "Usability Testing", "Accessibility Design",
        "Design Systems", "Brand Design", "Graphic Design", "Digital Design",
        
        # Product Management
        "Product Management", "Product Strategy", "Product Development", "Product Launch",
        "Product Roadmapping", "Feature Prioritization", "User Stories", "Requirements Gathering",
        "Market Research", "Competitive Analysis", "Product Analytics", "Growth Hacking",
        "Tracking Plan", "Event Taxonomy", "Event Tracking", "Instrumentation", "Feature Flagging",
        
        # Marketing & Sales
        "Marketing", "Digital Marketing", "Content Marketing", "Social Media Marketing",
        "Email Marketing", "SEO", "SEM", "PPC", "Brand Management", "Marketing Analytics",
        "Sales", "Sales Strategy", "Customer Relationship Management", "CRM",
        "Lead Generation", "Account Management", "Business Development",
        
        # Technical Skills
        "API", "REST APIs", "GraphQL", "Microservices", "Cloud Computing", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "Infrastructure as Code", "System Design", "Architecture",
        "Database Design", "SQL", "NoSQL", "Data Warehousing", "ETL", "Data Pipeline",
        
        # Programming & Development
        "Programming", "Software Development", "Web Development", "Mobile Development",
        "Frontend Development", "Backend Development", "Full Stack Development",
        "Object-Oriented Programming", "Functional Programming", "Test-Driven Development",
        "Code Review", "Version Control", "Git", "Debugging", "Performance Optimization",
        
        # Business & Soft Skills
        "Communication", "Problem Solving", "Critical Thinking", "Analytical Thinking",
        "Business Acumen", "Strategic Thinking", "Leadership", "Team Management",
        "Cross-functional Collaboration", "Stakeholder Management", "Presentation Skills",
        "Negotiation", "Conflict Resolution", "Time Management", "Organization",
        
        # Industry-Specific
        "Regulatory Compliance", "Quality Assurance", "Quality Control", "Process Optimization",
        "Supply Chain Management", "Logistics", "Healthcare Knowledge", "Financial Analysis",
        "Risk Management", "Auditing", "Document Management", "Technical Writing",
        "Training", "Mentoring", "Coaching",
        
        # Tools & Platforms
        "Microsoft Office", "Google Workspace", "Slack", "Teams", "Zoom", "WebEx",
        "Customer Support", "Help Desk", "Troubleshooting", "System Administration",
        "Network Administration", "Security", "Cybersecurity", "Information Security"
    ],
    "software": [
        # Programming Languages
        "Python", "R", "SQL", "JavaScript", "TypeScript", "Java", "C#", "C++", "C",
        "Go", "Rust", "Scala", "PHP", "Ruby", "Swift", "Kotlin", "Dart", "Perl",
        "MATLAB", "Julia", "VBA", "PowerShell", "Bash", "Shell Scripting",
        
        # Web Technologies
        "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Express.js",
        "Django", "Flask", "FastAPI", "Spring Boot", "Laravel", "Ruby on Rails",
        "Next.js", "Nuxt.js", "Gatsby", "Vercel", "Netlify", "WordPress",
        
        # Databases
        "MySQL", "PostgreSQL", "SQL Server", "Oracle", "MongoDB", "Redis",
        "Cassandra", "DynamoDB", "Firebase", "Supabase", "PlanetScale",
        "Elasticsearch", "InfluxDB", "Neo4j", "SQLite",
        
        # Cloud Platforms
        "AWS", "Azure", "GCP", "DigitalOcean", "Heroku", "Vercel", "Netlify",
        "Cloudflare", "Linode", "Vultr", "IBM Cloud", "Oracle Cloud",
        
        # Data & Analytics Tools
        "Tableau", "Power BI", "Looker", "QlikView", "Qlik Sense", "MicroStrategy",
        "Google Analytics", "Google Data Studio", "Mixpanel", "Amplitude",
        "Segment", "Snowflake", "Databricks", "Apache Spark", "Hadoop",
        "Apache Kafka", "Apache Airflow", "dbt", "Fivetran", "Stitch",
        
        # Machine Learning & AI
        "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "XGBoost", "LightGBM",
        "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly", "Bokeh",
        "Jupyter", "Google Colab", "Databricks", "Hugging Face", "OpenAI API",
        "Anthropic API", "LangChain", "Streamlit", "Gradio",
        
        # Design & Creative Tools
        "Figma", "Sketch", "Adobe XD", "Adobe Creative Suite", "Photoshop",
        "Illustrator", "InDesign", "Premiere Pro", "After Effects", "Framer",
        "InVision", "Marvel", "Principle", "Lottie", "Canva", "Miro", "Whimsical",
        
        # Project Management & Collaboration
        "Jira", "Confluence", "Atlassian", "Asana", "Trello", "Monday.com",
        "ClickUp", "Notion", "Slack", "Microsoft Teams", "Discord", "Zoom",
        "Google Meet", "WebEx", "Loom", "Miro", "Figma", "Lucidchart",
        
        # Development Tools
        "Git", "GitHub", "GitLab", "Bitbucket", "VS Code", "IntelliJ IDEA",
        "PyCharm", "WebStorm", "Sublime Text", "Atom", "Vim", "Emacs",
        "Docker", "Kubernetes", "Jenkins", "CircleCI", "GitHub Actions",
        "GitLab CI", "Travis CI", "SonarQube", "Postman", "Insomnia",
        
        # Business Software
        "Microsoft Office", "Excel", "Word", "PowerPoint", "Outlook",
        "Google Workspace", "Google Sheets", "Google Docs", "Google Slides",
        "Salesforce", "HubSpot", "Pipedrive", "Zoho", "SAP", "Oracle",
        "QuickBooks", "Xero", "Stripe", "PayPal", "Shopify", "WooCommerce",
        
        # CRM & Marketing
        "Salesforce", "HubSpot", "Pipedrive", "Zoho CRM", "Freshsales",
        "Mailchimp", "Constant Contact", "SendGrid", "Klaviyo", "ConvertKit",
        "Hootsuite", "Buffer", "Sprout Social", "Later", "Canva",
        
        # Engineering & CAD
        "SolidWorks", "AutoCAD", "Fusion 360", "Rhino", "Keyshot", "C4D",
        "Blender", "Maya", "3ds Max", "Revit", "SketchUp", "TinkerCAD",
        
        # Other Tools
        "OneDrive", "Google Drive", "Dropbox", "Box", "SharePoint",
        "IMDS", "Flow", "Zapier", "IFTTT", "Make.com", "Airtable",
        "Notion", "Obsidian", "Roam Research", "Logseq"
    ]
}

# Configuración de archivos
FILE_CONFIG = {
    "input_dir": "csv",
    "output_dir": "csv/archive",
    "default_input": "linkedin_jobs_make.csv",
    "output_prefix": "DataPM_result",
    "encoding": "utf-8",
    "delimiter": ",",
}

# Configuración de procesamiento
PROCESSING_CONFIG = {
    "batch_size": 1,  # Procesar uno por uno para evitar rate limiting
    "delay_between_requests": 1,  # Segundos entre requests
    "max_retries": 3,  # Máximo de reintentos por request
    "timeout": 30,  # Timeout por request
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "file": "datapm.log",
}

# Configuración de países y estados
LOCATION_CONFIG = {
    "countries": [
        "United States", "Spain", "Mexico", "United Kingdom", "Germany", 
        "France", "Panamá", "Venezuela", "European Union", "Unknown"
    ],
    "us_states": {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming"
    },
    "ca_provinces": {
        "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba", "NB": "New Brunswick",
        "NL": "Newfoundland and Labrador", "NS": "Nova Scotia", "NT": "Northwest Territories",
        "NU": "Nunavut", "ON": "Ontario", "PE": "Prince Edward Island", "QC": "Quebec",
        "SK": "Saskatchewan", "YT": "Yukon"
    }
}

def get_api_key(llm_type: str) -> str:
    """Obtiene la API key desde variables de entorno"""
    if llm_type == "gemini":
        return os.getenv('GEMINI_API_KEY', '')
    return ''

def get_ollama_url() -> str:
    """Obtiene la URL de Ollama desde variables de entorno"""
    return os.getenv('OLLAMA_URL', 'http://localhost:11434')

def get_output_filename(prefix: str = None) -> str:
    """Genera un nombre de archivo de salida con timestamp"""
    from datetime import datetime
    
    if not prefix:
        prefix = FILE_CONFIG["output_prefix"]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{prefix}.csv"

def get_full_output_path(filename: str = None) -> str:
    """Obtiene la ruta completa del archivo de salida"""
    if not filename:
        filename = get_output_filename()
    
    output_dir = FILE_CONFIG["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    return os.path.join(output_dir, filename)

def get_full_input_path(filename: str = None) -> str:
    """Obtiene la ruta completa del archivo de entrada"""
    if not filename:
        filename = FILE_CONFIG["default_input"]
    
    input_dir = FILE_CONFIG["input_dir"]
    return os.path.join(input_dir, filename)

# Configuración de prompts
PROMPT_TEMPLATES = {
    "system": """You are a strict data extractor and standardizer. You MUST return ONLY a valid JSON object and nothing else.
The JSON must follow this schema:

job_title_original (string)

job_title_short (string, normalized to one of these values: {job_titles})

experience_years (string, normalized to one of these formats: "0-3" for less than 3 years, "3-5" for ranges, "5+" for 5 or more years)

job_schedule_type (string, normalized to one of these values: {schedule_types})

seniority (string, normalized to one of these values: {seniority_levels})

city (string, normalized to proper case, e.g., "New York", "Madrid". If not found, use "Unknown".)

state (string, normalized to two-letter abbreviation if in the US/CA, e.g., "NY", "CA". If not in the US/CA or not found, use "Unknown".)

country (string, normalized to proper case, e.g., "United States", "Spain", "Mexico", "United Kingdom", "Germany", "France", "Panamá", "Venezuela", "European Union", "Unknown")

degrees (array of strings, normalized to one of these values: {degrees})

skills (array of strings, normalized to a fixed set of values like: {skills})

software (array of strings, normalized to a fixed set of values like: {software})

company_name (string)

If you cannot determine a value, use "Unknown" for strings and blank space for arrays, data slot must be empty. No extra text, no markdown, no explanation.""",
    
    "user": """INPUT: {{"text":"{description}"}}
TASK: Analyze INPUT.text and return the JSON according to the schema in the system instructions."""
}

def get_system_prompt() -> str:
    """Obtiene el prompt del sistema con valores normalizados"""
    return PROMPT_TEMPLATES["system"].format(
        job_titles=NORMALIZATION_SCHEMA["job_title_short"],
        schedule_types=NORMALIZATION_SCHEMA["job_schedule_type"],
        seniority_levels=NORMALIZATION_SCHEMA["seniority"],
        degrees=NORMALIZATION_SCHEMA["degrees"],
        skills=NORMALIZATION_SCHEMA["skills"],
        software=NORMALIZATION_SCHEMA["software"]
    )

def get_user_prompt(description: str) -> str:
    """Obtiene el prompt del usuario"""
    return PROMPT_TEMPLATES["user"].format(description=description)

```

```python
#!/usr/bin/env python3
"""
Configuración centralizada para DataPM Processor
"""

import os
from typing import Dict, List

# Configuración de LLMs
LLM_CONFIG = {
    "gemini": {
        "model": "gemini-2.0-flash-exp",
        "max_tokens": 100000,
        "temperature": 0.1,  # Baja temperatura para respuestas más consistentes
    },
    "ollama": {
        "model": "llama3.2:3b",  # Modelo por defecto
        "url": "http://localhost:11434",
        "timeout": 30,
    }
}

# Schema de normalización expandido para mayor cobertura
NORMALIZATION_SCHEMA = {
    "job_title_short": [
        # Product Management
        "Product Manager", "Product Owner", "Product Lead", "Product Director", 
        "VP of Product", "Head of Product", "Product Specialist", "Product Coordinator", 
        "Product Analyst", "Product Associate",
        
        # Data Roles
        "Data Analyst", "Data Scientist", "Data Engineer", "Data Architect", 
        "Data Manager", "Data Lead", "Data Specialist", "Business Intelligence Analyst", 
        "BI Analyst", "Analytics Manager", "Machine Learning Engineer", "ML Engineer", 
        "AI Engineer", "AI Specialist", "Analytics Engineer", "Growth Analyst", 
        "Insights Analyst", "Experimentation Analyst", "BI Engineer", "Data Product Manager",
        
        # Design Roles
        "UX/UI Designer", "UX Designer", "UI Designer", "Product Designer", 
        "Design Lead", "Design Manager", "Creative Designer", "Visual Designer", 
        "Graphic Designer", "Digital Designer", "Web Designer", "Interaction Designer", 
        "Service Designer", "Design Director", "Head of Design", "VP of Design",
        
        # Engineering Roles
        "Software Engineer", "Full Stack Developer", "Frontend Developer", "Backend Developer",
        "DevOps Engineer", "Site Reliability Engineer", "Cloud Engineer", "Systems Engineer", 
        "QA Engineer", "Test Engineer", "Automation Engineer", "Mobile Developer", 
        "iOS Developer", "Android Developer", "Web Developer",
        
        # Marketing Roles
        "Marketing Specialist", "Marketing Manager", "Marketing Analyst",
        "Digital Marketing Specialist", "Content Marketing Specialist",
        "Product Marketing Manager", "Product Marketing Specialist",
        "Growth Marketing Manager", "Brand Manager", "Marketing Coordinator",
        "Marketing Assistant", "Marketing Director", "VP of Marketing",
        
        # Project & Business Roles
        "Project Manager", "Program Manager", "Project Coordinator", "Project Lead",
        "Business Analyst", "Process Designer", "Process Manager", "Process Analyst",
        "Business Intelligence Manager", "Strategy Manager", "Operations Manager",
        "Product Operations",
        
        # IT & Technical Roles
        "IT Analyst", "IT Manager", "IT Specialist", "IT Coordinator",
        "System Administrator", "Network Engineer", "Security Engineer",
        "Information Security Analyst", "Technical Support Specialist",
        "Technical Writer", "Technical Project Manager",
        
        # Compliance & Quality
        "Product Compliance Specialist", "Compliance Manager", "Compliance Analyst",
        "Quality Assurance Specialist", "Quality Manager", "Quality Analyst",
        "Regulatory Affairs Specialist", "Auditor", "Risk Analyst",
        
        # Sales & Customer Success
        "Sales Manager", "Sales Specialist", "Sales Representative",
        "Account Manager", "Customer Success Manager", "Customer Success Specialist",
        "Business Development Manager", "Partnership Manager",
        
        # Research & Analytics
        "Research Analyst", "Market Research Analyst", "User Researcher",
        "Research Manager", "Analytics Specialist", "Performance Analyst",
        
        # Other Common Roles
        "Consultant", "Advisor", "Specialist", "Coordinator", "Assistant", "Associate",
        "Manager", "Director", "VP", "Head of", "Lead", "Principal", "Staff", "Other"
    ],
    "experience_years": ["0-3", "3-5", "5+"],
    "job_schedule_type": ["Full-time", "Part-time", "Contract", "Internship", "Unknown"],
    "seniority": ["Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"],
    "degrees": [
        "Bachelor's Degree", "Master's Degree", "PhD", "Associate's Degree", 
        "Higher Education", "Engineering", "Automotive Engineering", 
        "Vocational Training", "Other"
    ],
    "skills": [
        # Project Management & Methodology
        "Project Management", "Agile", "Scrum", "Kanban", "Lean", "Six Sigma",
        "Waterfall", "SAFe", "DevOps", "CI/CD", "SDLC", "Product Lifecycle Management",
        
        # Data & Analytics
        "Data Analysis", "Data Visualization", "Statistical Analysis", "Predictive Analytics",
        "Machine Learning", "Deep Learning", "AI", "Natural Language Processing", "NLP",
        "Business Intelligence", "Data Mining", "Data Modeling", "Data Governance",
        "A/B Testing", "Hypothesis Testing", "Quantitative Research", "Qualitative Research",
        "Experimentation", "Experiment Design", "Causal Inference", "Cohort Analysis",
        "Funnel Analysis", "Retention Analysis", "Attribution Modeling",
        
        # Design & UX
        "UI/UX Design", "User Research", "User-Centered Design", "Design Thinking",
        "Wireframing", "Prototyping", "Visual Design", "Interaction Design",
        "Information Architecture", "Usability Testing", "Accessibility Design",
        "Design Systems", "Brand Design", "Graphic Design", "Digital Design",
        
        # Product Management
        "Product Management", "Product Strategy", "Product Development", "Product Launch",
        "Product Roadmapping", "Feature Prioritization", "User Stories", "Requirements Gathering",
        "Market Research", "Competitive Analysis", "Product Analytics", "Growth Hacking",
        "Tracking Plan", "Event Taxonomy", "Event Tracking", "Instrumentation", "Feature Flagging",
        
        # Marketing & Sales
        "Marketing", "Digital Marketing", "Content Marketing", "Social Media Marketing",
        "Email Marketing", "SEO", "SEM", "PPC", "Brand Management", "Marketing Analytics",
        "Sales", "Sales Strategy", "Customer Relationship Management", "CRM",
        "Lead Generation", "Account Management", "Business Development",
        
        # Technical Skills
        "API", "REST APIs", "GraphQL", "Microservices", "Cloud Computing", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "Infrastructure as Code", "System Design", "Architecture",
        "Database Design", "SQL", "NoSQL", "Data Warehousing", "ETL", "Data Pipeline",
        
        # Programming & Development
        "Programming", "Software Development", "Web Development", "Mobile Development",
        "Frontend Development", "Backend Development", "Full Stack Development",
        "Object-Oriented Programming", "Functional Programming", "Test-Driven Development",
        "Code Review", "Version Control", "Git", "Debugging", "Performance Optimization",
        
        # Business & Soft Skills
        "Communication", "Problem Solving", "Critical Thinking", "Analytical Thinking",
        "Business Acumen", "Strategic Thinking", "Leadership", "Team Management",
        "Cross-functional Collaboration", "Stakeholder Management", "Presentation Skills",
        "Negotiation", "Conflict Resolution", "Time Management", "Organization",
        
        # Industry-Specific
        "Regulatory Compliance", "Quality Assurance", "Quality Control", "Process Optimization",
        "Supply Chain Management", "Logistics", "Healthcare Knowledge", "Financial Analysis",
        "Risk Management", "Auditing", "Document Management", "Technical Writing",
        "Training", "Mentoring", "Coaching",
        
        # Tools & Platforms
        "Microsoft Office", "Google Workspace", "Slack", "Teams", "Zoom", "WebEx",
        "Customer Support", "Help Desk", "Troubleshooting", "System Administration",
        "Network Administration", "Security", "Cybersecurity", "Information Security"
    ],
    "software": [
        # Programming Languages
        "Python", "R", "SQL", "JavaScript", "TypeScript", "Java", "C#", "C++", "C",
        "Go", "Rust", "Scala", "PHP", "Ruby", "Swift", "Kotlin", "Dart", "Perl",
        "MATLAB", "Julia", "VBA", "PowerShell", "Bash", "Shell Scripting",
        
        # Web Technologies
        "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Express.js",
        "Django", "Flask", "FastAPI", "Spring Boot", "Laravel", "Ruby on Rails",
        "Next.js", "Nuxt.js", "Gatsby", "Vercel", "Netlify", "WordPress",
        
        # Databases
        "MySQL", "PostgreSQL", "SQL Server", "Oracle", "MongoDB", "Redis",
        "Cassandra", "DynamoDB", "Firebase", "Supabase", "PlanetScale",
        "Elasticsearch", "InfluxDB", "Neo4j", "SQLite",
        
        # Cloud Platforms
        "AWS", "Azure", "GCP", "DigitalOcean", "Heroku", "Vercel", "Netlify",
        "Cloudflare", "Linode", "Vultr", "IBM Cloud", "Oracle Cloud",
        
        # Data & Analytics Tools
        "Tableau", "Power BI", "Looker", "QlikView", "Qlik Sense", "MicroStrategy",
        "Google Analytics", "Google Data Studio", "Looker Studio", "Mixpanel", "Amplitude",
        "PostHog", "Heap", "FullStory", "Hotjar", "Pendo",
        "Segment", "RudderStack", "Snowflake", "Databricks", "Apache Spark", "Hadoop",
        "Apache Kafka", "Apache Airflow", "Airbyte", "dbt", "Fivetran", "Stitch",
        "Apache Superset", "Metabase", "Mode Analytics",
        
        # Machine Learning & AI
        "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "XGBoost", "LightGBM",
        "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly", "Bokeh",
        "Jupyter", "Google Colab", "Databricks", "Hugging Face", "OpenAI API",
        "Anthropic API", "LangChain", "Streamlit", "Gradio",
        
        # Design & Creative Tools
        "Figma", "Sketch", "Adobe XD", "Adobe Creative Suite", "Photoshop",
        "Illustrator", "InDesign", "Premiere Pro", "After Effects", "Framer",
        "InVision", "Marvel", "Principle", "Lottie", "Canva", "Miro", "Whimsical",
        
        # Project Management & Collaboration
        "Jira", "Confluence", "Atlassian", "Asana", "Trello", "Monday.com",
        "ClickUp", "Notion", "Slack", "Microsoft Teams", "Discord", "Zoom",
        "Google Meet", "WebEx", "Loom", "Miro", "Figma", "Lucidchart",
        
        # Development Tools
        "Git", "GitHub", "GitLab", "Bitbucket", "VS Code", "IntelliJ IDEA",
        "PyCharm", "WebStorm", "Sublime Text", "Atom", "Vim", "Emacs",
        "Docker", "Kubernetes", "Jenkins", "CircleCI", "GitHub Actions",
        "GitLab CI", "Travis CI", "SonarQube", "Postman", "Insomnia",
        
        # Business Software
        "Microsoft Office", "Excel", "Word", "PowerPoint", "Outlook",
        "Google Workspace", "Google Sheets", "Google Docs", "Google Slides",
        "Salesforce", "HubSpot", "Pipedrive", "Zoho", "SAP", "Oracle",
        "QuickBooks", "Xero", "Stripe", "PayPal", "Shopify", "WooCommerce",
        
        # CRM & Marketing
        "Salesforce", "HubSpot", "Pipedrive", "Zoho CRM", "Freshsales",
        "Mailchimp", "Constant Contact", "SendGrid", "Klaviyo", "ConvertKit",
        "Hootsuite", "Buffer", "Sprout Social", "Later", "Canva",
        
        # Engineering & CAD
        "SolidWorks", "AutoCAD", "Fusion 360", "Rhino", "Keyshot", "C4D",
        "Blender", "Maya", "3ds Max", "Revit", "SketchUp", "TinkerCAD",
        
        # Other Tools
        "OneDrive", "Google Drive", "Dropbox", "Box", "SharePoint",
        "IMDS", "Flow", "Zapier", "IFTTT", "Make.com", "Airtable",
        "Notion", "Obsidian", "Roam Research", "Logseq"
    ]
}

# Configuración de archivos
FILE_CONFIG = {
    "input_dir": "csv",
    "output_dir": "csv/archive",
    "default_input": "linkedin_jobs_make.csv",
    "output_prefix": "DataPM_result",
    "encoding": "utf-8",
    "delimiter": ",",
}

# Configuración de procesamiento
PROCESSING_CONFIG = {
    "batch_size": 1,  # Procesar uno por uno para evitar rate limiting
    "delay_between_requests": 1,  # Segundos entre requests
    "max_retries": 3,  # Máximo de reintentos por request
    "timeout": 30,  # Timeout por request
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "file": "datapm.log",
}

# Configuración de países y estados
LOCATION_CONFIG = {
    "countries": [
        "United States", "Spain", "Mexico", "United Kingdom", "Germany", 
        "France", "Panamá", "Venezuela", "European Union", "Unknown"
    ],
    "us_states": {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming"
    },
    "ca_provinces": {
        "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba", "NB": "New Brunswick",
        "NL": "Newfoundland and Labrador", "NS": "Nova Scotia", "NT": "Northwest Territories",
        "NU": "Nunavut", "ON": "Ontario", "PE": "Prince Edward Island", "QC": "Quebec",
        "SK": "Saskatchewan", "YT": "Yukon"
    }
}

def get_api_key(llm_type: str) -> str:
    """Obtiene la API key desde variables de entorno"""
    if llm_type == "gemini":
        return os.getenv('GEMINI_API_KEY', '')
    return ''

def get_ollama_url() -> str:
    """Obtiene la URL de Ollama desde variables de entorno"""
    return os.getenv('OLLAMA_URL', 'http://localhost:11434')

def get_output_filename(prefix: str = None) -> str:
    """Genera un nombre de archivo de salida con timestamp"""
    from datetime import datetime
    
    if not prefix:
        prefix = FILE_CONFIG["output_prefix"]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{prefix}.csv"

def get_full_output_path(filename: str = None) -> str:
    """Obtiene la ruta completa del archivo de salida"""
    if not filename:
        filename = get_output_filename()
    
    output_dir = FILE_CONFIG["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    return os.path.join(output_dir, filename)

def get_full_input_path(filename: str = None) -> str:
    """Obtiene la ruta completa del archivo de entrada"""
    if not filename:
        filename = FILE_CONFIG["default_input"]
    
    input_dir = FILE_CONFIG["input_dir"]
    return os.path.join(input_dir, filename)

# Configuración de prompts
PROMPT_TEMPLATES = {
    "system": """You are a strict data extractor and standardizer. You MUST return ONLY a valid JSON object and nothing else.
The JSON must follow this schema:

job_title_original (string)

job_title_short (string, normalized to one of these values: {job_titles})

experience_years (string, normalized to one of these formats: "0-3" for less than 3 years, "3-5" for ranges, "5+" for 5 or more years)

job_schedule_type (string, normalized to one of these values: {schedule_types})

seniority (string, normalized to one of these values: {seniority_levels})

city (string, normalized to proper case, e.g., "New York", "Madrid". If not found, use "Unknown".)

state (string, normalized to two-letter abbreviation if in the US/CA, e.g., "NY", "CA". If not in the US/CA or not found, use "Unknown".)

country (string, normalized to proper case, e.g., "United States", "Spain", "Mexico", "United Kingdom", "Germany", "France", "Panamá", "Venezuela", "European Union", "Unknown")

degrees (array of strings, normalized to one of these values: {degrees})

skills (array of strings, normalized to a fixed set of values like: {skills})

software (array of strings, normalized to a fixed set of values like: {software})

company_name (string)

If you cannot determine a value, use "Unknown" for strings and blank space for arrays, data slot must be empty. No extra text, no markdown, no explanation.""",
    
    "user": """INPUT: {{"text":"{description}"}}
TASK: Analyze INPUT.text and return the JSON according to the schema in the system instructions."""
}

def get_system_prompt() -> str:
    """Obtiene el prompt del sistema con valores normalizados"""
    return PROMPT_TEMPLATES["system"].format(
        job_titles=NORMALIZATION_SCHEMA["job_title_short"],
        schedule_types=NORMALIZATION_SCHEMA["job_schedule_type"],
        seniority_levels=NORMALIZATION_SCHEMA["seniority"],
        degrees=NORMALIZATION_SCHEMA["degrees"],
        skills=NORMALIZATION_SCHEMA["skills"],
        software=NORMALIZATION_SCHEMA["software"]
    )

def get_user_prompt(description: str) -> str:
    """Obtiene el prompt del usuario"""
    return PROMPT_TEMPLATES["user"].format(description=description)

```

```python
#!/usr/bin/env python3
"""
Configuración centralizada para DataPM Processor
"""

import os
from typing import Dict, List

# Configuración de LLMs
LLM_CONFIG = {
    "gemini": {
        "model": "gemini-2.0-flash-exp",
        "max_tokens": 100000,
        "temperature": 0.1,  # Baja temperatura para respuestas más consistentes
    },
    "ollama": {
        "model": "llama3.2:3b",  # Modelo por defecto
        "url": "http://localhost:11434",
        "timeout": 30,
    }
}

# Schema de normalización expandido para mayor cobertura
NORMALIZATION_SCHEMA = {
    "job_title_short": [
        # Product Management
        "Product Manager", "Product Owner", "Product Lead", "Product Director", 
        "VP of Product", "Head of Product", "Product Specialist", "Product Coordinator", 
        "Product Analyst", "Product Associate",
        
        # Data Roles
        "Data Analyst", "Data Scientist", "Data Engineer", "Data Architect", 
        "Data Manager", "Data Lead", "Data Specialist", "Business Intelligence Analyst", 
        "BI Analyst", "Analytics Manager", "Machine Learning Engineer", "ML Engineer", 
        "AI Engineer", "AI Specialist", "Analytics Engineer", "Growth Analyst", 
        "Insights Analyst", "Experimentation Analyst", "BI Engineer", "Data Product Manager",
        
        # Design Roles
        "UX/UI Designer", "UX Designer", "UI Designer", "Product Designer", 
        "Design Lead", "Design Manager", "Creative Designer", "Visual Designer", 
        "Graphic Designer", "Digital Designer", "Web Designer", "Interaction Designer", 
        "Service Designer", "Design Director", "Head of Design", "VP of Design",
        
        # Engineering Roles
        "Software Engineer", "Full Stack Developer", "Frontend Developer", "Backend Developer",
        "DevOps Engineer", "Site Reliability Engineer", "Cloud Engineer", "Systems Engineer", 
        "QA Engineer", "Test Engineer", "Automation Engineer", "Mobile Developer", 
        "iOS Developer", "Android Developer", "Web Developer",
        
        # Marketing Roles
        "Marketing Specialist", "Marketing Manager", "Marketing Analyst",
        "Digital Marketing Specialist", "Content Marketing Specialist",
        "Product Marketing Manager", "Product Marketing Specialist",
        "Growth Marketing Manager", "Brand Manager", "Marketing Coordinator",
        "Marketing Assistant", "Marketing Director", "VP of Marketing",
        
        # Project & Business Roles
        "Project Manager", "Program Manager", "Project Coordinator", "Project Lead",
        "Business Analyst", "Process Designer", "Process Manager", "Process Analyst",
        "Business Intelligence Manager", "Strategy Manager", "Operations Manager",
        "Product Operations",
        
        # IT & Technical Roles
        "IT Analyst", "IT Manager", "IT Specialist", "IT Coordinator",
        "System Administrator", "Network Engineer", "Security Engineer",
        "Information Security Analyst", "Technical Support Specialist",
        "Technical Writer", "Technical Project Manager",
        
        # Compliance & Quality
        "Product Compliance Specialist", "Compliance Manager", "Compliance Analyst",
        "Quality Assurance Specialist", "Quality Manager", "Quality Analyst",
        "Regulatory Affairs Specialist", "Auditor", "Risk Analyst",
        
        # Sales & Customer Success
        "Sales Manager", "Sales Specialist", "Sales Representative",
        "Account Manager", "Customer Success Manager", "Customer Success Specialist",
        "Business Development Manager", "Partnership Manager",
        
        # Research & Analytics
        "Research Analyst", "Market Research Analyst", "User Researcher",
        "Research Manager", "Analytics Specialist", "Performance Analyst",
        
        # Other Common Roles
        "Consultant", "Advisor", "Specialist", "Coordinator", "Assistant", "Associate",
        "Manager", "Director", "VP", "Head of", "Lead", "Principal", "Staff", "Other"
    ],
    "experience_years": ["0-3", "3-5", "5+"],
    "job_schedule_type": ["Full-time", "Part-time", "Contract", "Internship", "Unknown"],
    "seniority": ["Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"],
    "degrees": [
        "Bachelor's Degree", "Master's Degree", "PhD", "Associate's Degree", 
        "Higher Education", "Engineering", "Automotive Engineering", 
        "Vocational Training", "Other"
    ],
    "skills": [
        # Project Management & Methodology
        "Project Management", "Agile", "Scrum", "Kanban", "Lean", "Six Sigma",
        "Waterfall", "SAFe", "DevOps", "CI/CD", "SDLC", "Product Lifecycle Management",
        
        # Data & Analytics
        "Data Analysis", "Data Visualization", "Statistical Analysis", "Predictive Analytics",
        "Machine Learning", "Deep Learning", "AI", "Natural Language Processing", "NLP",
        "Business Intelligence", "Data Mining", "Data Modeling", "Data Governance",
        "A/B Testing", "Hypothesis Testing", "Quantitative Research", "Qualitative Research",
        "Experimentation", "Experiment Design", "Causal Inference", "Cohort Analysis",
        "Funnel Analysis", "Retention Analysis", "Attribution Modeling",
        
        # Design & UX
        "UI/UX Design", "User Research", "User-Centered Design", "Design Thinking",
        "Wireframing", "Prototyping", "Visual Design", "Interaction Design",
        "Information Architecture", "Usability Testing", "Accessibility Design",
        "Design Systems", "Brand Design", "Graphic Design", "Digital Design",
        
        # Product Management
        "Product Management", "Product Strategy", "Product Development", "Product Launch",
        "Product Roadmapping", "Feature Prioritization", "User Stories", "Requirements Gathering",
        "Market Research", "Competitive Analysis", "Product Analytics", "Growth Hacking",
        "Tracking Plan", "Event Taxonomy", "Event Tracking", "Instrumentation", "Feature Flagging",
        
        # Marketing & Sales
        "Marketing", "Digital Marketing", "Content Marketing", "Social Media Marketing",
        "Email Marketing", "SEO", "SEM", "PPC", "Brand Management", "Marketing Analytics",
        "Sales", "Sales Strategy", "Customer Relationship Management", "CRM",
        "Lead Generation", "Account Management", "Business Development",
        
        # Technical Skills
        "API", "REST APIs", "GraphQL", "Microservices", "Cloud Computing", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "Infrastructure as Code", "System Design", "Architecture",
        "Database Design", "SQL", "NoSQL", "Data Warehousing", "ETL", "Data Pipeline",
        
        # Programming & Development
        "Programming", "Software Development", "Web Development", "Mobile Development",
        "Frontend Development", "Backend Development", "Full Stack Development",
        "Object-Oriented Programming", "Functional Programming", "Test-Driven Development",
        "Code Review", "Version Control", "Git", "Debugging", "Performance Optimization",
        
        # Business & Soft Skills
        "Communication", "Problem Solving", "Critical Thinking", "Analytical Thinking",
        "Business Acumen", "Strategic Thinking", "Leadership", "Team Management",
        "Cross-functional Collaboration", "Stakeholder Management", "Presentation Skills",
        "Negotiation", "Conflict Resolution", "Time Management", "Organization",
        
        # Industry-Specific
        "Regulatory Compliance", "Quality Assurance", "Quality Control", "Process Optimization",
        "Supply Chain Management", "Logistics", "Healthcare Knowledge", "Financial Analysis",
        "Risk Management", "Auditing", "Document Management", "Technical Writing",
        "Training", "Mentoring", "Coaching",
        
        # Tools & Platforms
        "Microsoft Office", "Google Workspace", "Slack", "Teams", "Zoom", "WebEx",
        "Customer Support", "Help Desk", "Troubleshooting", "System Administration",
        "Network Administration", "Security", "Cybersecurity", "Information Security"
    ],
    "software": [
        # Programming Languages
        "Python", "R", "SQL", "JavaScript", "TypeScript", "Java", "C#", "C++", "C",
        "Go", "Rust", "Scala", "PHP", "Ruby", "Swift", "Kotlin", "Dart", "Perl",
        "MATLAB", "Julia", "VBA", "PowerShell", "Bash", "Shell Scripting",
        
        # Web Technologies
        "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Express.js",
        "Django", "Flask", "FastAPI", "Spring Boot", "Laravel", "Ruby on Rails",
        "Next.js", "Nuxt.js", "Gatsby", "Vercel", "Netlify", "WordPress",
        
        # Databases
        "MySQL", "PostgreSQL", "SQL Server", "Oracle", "MongoDB", "Redis",
        "Cassandra", "DynamoDB", "Firebase", "Supabase", "PlanetScale",
        "Elasticsearch", "InfluxDB", "Neo4j", "SQLite",
        
        # Cloud Platforms
        "AWS", "Azure", "GCP", "DigitalOcean", "Heroku", "Vercel", "Netlify",
        "Cloudflare", "Linode", "Vultr", "IBM Cloud", "Oracle Cloud",

        # Data Warehouses
        "BigQuery", "Redshift",
        
        # Data & Analytics Tools
        "Tableau", "Power BI", "Looker", "QlikView", "Qlik Sense", "MicroStrategy",
        "Google Analytics", "Google Data Studio", "Looker Studio", "Mixpanel", "Amplitude",
        "PostHog", "Heap", "FullStory", "Hotjar", "Pendo",
        "Segment", "RudderStack", "Snowflake", "Databricks", "Apache Spark", "Hadoop",
        "Apache Kafka", "Apache Airflow", "Airbyte", "dbt", "Fivetran", "Stitch",
        "Apache Superset", "Metabase", "Mode Analytics",
        
        # Machine Learning & AI
        "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "XGBoost", "LightGBM",
        "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly", "Bokeh",
        "Jupyter", "Google Colab", "Databricks", "Hugging Face", "OpenAI API",
        "Anthropic API", "LangChain", "Streamlit", "Gradio",
        
        # Design & Creative Tools
        "Figma", "Sketch", "Adobe XD", "Adobe Creative Suite", "Photoshop",
        "Illustrator", "InDesign", "Premiere Pro", "After Effects", "Framer",
        "InVision", "Marvel", "Principle", "Lottie", "Canva", "Miro", "Whimsical",
        
        # Project Management & Collaboration
        "Jira", "Confluence", "Atlassian", "Asana", "Trello", "Monday.com",
        "ClickUp", "Notion", "Slack", "Microsoft Teams", "Discord", "Zoom",
        "Google Meet", "WebEx", "Loom", "Miro", "Figma", "Lucidchart",

        # Experimentation & Feature Flags
        "Optimizely", "VWO", "LaunchDarkly",
        
        # Development Tools
        "Git", "GitHub", "GitLab", "Bitbucket", "VS Code", "IntelliJ IDEA",
        "PyCharm", "WebStorm", "Sublime Text", "Atom", "Vim", "Emacs",
        "Docker", "Kubernetes", "Jenkins", "CircleCI", "GitHub Actions",
        "GitLab CI", "Travis CI", "SonarQube", "Postman", "Insomnia",
        
        # Business Software
        "Microsoft Office", "Excel", "Word", "PowerPoint", "Outlook",
        "Google Workspace", "Google Sheets", "Google Docs", "Google Slides",
        "Salesforce", "HubSpot", "Pipedrive", "Zoho", "SAP", "Oracle",
        "QuickBooks", "Xero", "Stripe", "PayPal", "Shopify", "WooCommerce",
        
        # CRM & Marketing
        "Salesforce", "HubSpot", "Pipedrive", "Zoho CRM", "Freshsales",
        "Mailchimp", "Constant Contact", "SendGrid", "Klaviyo", "ConvertKit",
        "Hootsuite", "Buffer", "Sprout Social", "Later", "Canva",
        
        # Engineering & CAD
        "SolidWorks", "AutoCAD", "Fusion 360", "Rhino", "Keyshot", "C4D",
        "Blender", "Maya", "3ds Max", "Revit", "SketchUp", "TinkerCAD",
        
        # Other Tools
        "OneDrive", "Google Drive", "Dropbox", "Box", "SharePoint",
        "IMDS", "Flow", "Zapier", "IFTTT", "Make.com", "Airtable",
        "Notion", "Obsidian", "Roam Research", "Logseq"
    ]
}

# Configuración de archivos
FILE_CONFIG = {
    "input_dir": "csv",
    "output_dir": "csv/archive",
    "default_input": "linkedin_jobs_make.csv",
    "output_prefix": "DataPM_result",
    "encoding": "utf-8",
    "delimiter": ",",
}

# Configuración de procesamiento
PROCESSING_CONFIG = {
    "batch_size": 1,  # Procesar uno por uno para evitar rate limiting
    "delay_between_requests": 1,  # Segundos entre requests
    "max_retries": 3,  # Máximo de reintentos por request
    "timeout": 30,  # Timeout por request
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "file": "datapm.log",
}

# Configuración de países y estados
LOCATION_CONFIG = {
    "countries": [
        "United States", "Spain", "Mexico", "United Kingdom", "Germany", 
        "France", "Panamá", "Venezuela", "European Union", "Unknown"
    ],
    "us_states": {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming"
    },
    "ca_provinces": {
        "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba", "NB": "New Brunswick",
        "NL": "Newfoundland and Labrador", "NS": "Nova Scotia", "NT": "Northwest Territories",
        "NU": "Nunavut", "ON": "Ontario", "PE": "Prince Edward Island", "QC": "Quebec",
        "SK": "Saskatchewan", "YT": "Yukon"
    }
}

def get_api_key(llm_type: str) -> str:
    """Obtiene la API key desde variables de entorno"""
    if llm_type == "gemini":
        return os.getenv('GEMINI_API_KEY', '')
    return ''

def get_ollama_url() -> str:
    """Obtiene la URL de Ollama desde variables de entorno"""
    return os.getenv('OLLAMA_URL', 'http://localhost:11434')

def get_output_filename(prefix: str = None) -> str:
    """Genera un nombre de archivo de salida con timestamp"""
    from datetime import datetime
    
    if not prefix:
        prefix = FILE_CONFIG["output_prefix"]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{prefix}.csv"

def get_full_output_path(filename: str = None) -> str:
    """Obtiene la ruta completa del archivo de salida"""
    if not filename:
        filename = get_output_filename()
    
    output_dir = FILE_CONFIG["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    return os.path.join(output_dir, filename)

def get_full_input_path(filename: str = None) -> str:
    """Obtiene la ruta completa del archivo de entrada"""
    if not filename:
        filename = FILE_CONFIG["default_input"]
    
    input_dir = FILE_CONFIG["input_dir"]
    return os.path.join(input_dir, filename)

# Configuración de prompts
PROMPT_TEMPLATES = {
    "system": """You are a strict data extractor and standardizer. You MUST return ONLY a valid JSON object and nothing else.
The JSON must follow this schema:

job_title_original (string)

job_title_short (string, normalized to one of these values: {job_titles})

experience_years (string, normalized to one of these formats: "0-3" for less than 3 years, "3-5" for ranges, "5+" for 5 or more years)

job_schedule_type (string, normalized to one of these values: {schedule_types})

seniority (string, normalized to one of these values: {seniority_levels})

city (string, normalized to proper case, e.g., "New York", "Madrid". If not found, use "Unknown".)

state (string, normalized to two-letter abbreviation if in the US/CA, e.g., "NY", "CA". If not in the US/CA or not found, use "Unknown".)

country (string, normalized to proper case, e.g., "United States", "Spain", "Mexico", "United Kingdom", "Germany", "France", "Panamá", "Venezuela", "European Union", "Unknown")

degrees (array of strings, normalized to one of these values: {degrees})

skills (array of strings, normalized to a fixed set of values like: {skills})

software (array of strings, normalized to a fixed set of values like: {software})

company_name (string)

If you cannot determine a value, use "Unknown" for strings and blank space for arrays, data slot must be empty. No extra text, no markdown, no explanation.""",
    
    "user": """INPUT: {{"text":"{description}"}}
TASK: Analyze INPUT.text and return the JSON according to the schema in the system instructions."""
}

def get_system_prompt() -> str:
    """Obtiene el prompt del sistema con valores normalizados"""
    return PROMPT_TEMPLATES["system"].format(
        job_titles=NORMALIZATION_SCHEMA["job_title_short"],
        schedule_types=NORMALIZATION_SCHEMA["job_schedule_type"],
        seniority_levels=NORMALIZATION_SCHEMA["seniority"],
        degrees=NORMALIZATION_SCHEMA["degrees"],
        skills=NORMALIZATION_SCHEMA["skills"],
        software=NORMALIZATION_SCHEMA["software"]
    )

def get_user_prompt(description: str) -> str:
    """Obtiene el prompt del usuario"""
    return PROMPT_TEMPLATES["user"].format(description=description)

```

He analizado el CSV nuevo y amplié el schema de normalización en `csv_engine/utils/config.py` agregando solo categorías útiles sin redundancias de seniority o industria.

- job_title_short: añadidos específicos y no redundantes
  - Analytics Engineer, Growth Analyst, Insights Analyst, Experimentation Analyst, BI Engineer, Data Product Manager, Product Operations

- skills: añadí conceptos analíticos/product growth sin adjetivos de industria/seniority
  - Experimentation, Experiment Design, Causal Inference, Cohort Analysis, Funnel Analysis, Retention Analysis, Attribution Modeling
  - Tracking Plan, Event Taxonomy, Event Tracking, Instrumentation, Feature Flagging

- software: añadidos de analítica de producto, warehouses, ETL, orquestación y feature flags
  - Looker Studio, PostHog, Heap, FullStory, Hotjar, Pendo
  - RudderStack, Airbyte, Apache Superset, Metabase, Mode Analytics
  - BigQuery, Redshift
  - Optimizely, VWO, LaunchDarkly

Fragmentos relevantes:
```31:36:csv_engine/utils/config.py
# Data Roles
"Data Analyst", ..., "AI Engineer", "AI Specialist", "Analytics Engineer", "Growth Analyst", 
"Insights Analyst", "Experimentation Analyst", "BI Engineer", "Data Product Manager",
```
```56:60:csv_engine/utils/config.py
"Business Intelligence Manager", "Strategy Manager", "Operations Manager",
"Product Operations",
```
```98:106:csv_engine/utils/config.py
"A/B Testing", "Hypothesis Testing", ..., 
"Experimentation", "Experiment Design", "Causal Inference", "Cohort Analysis",
"Funnel Analysis", "Retention Analysis", "Attribution Modeling",
```
```110:114:csv_engine/utils/config.py
"Product Analytics", "Growth Hacking",
"Tracking Plan", "Event Taxonomy", "Event Tracking", "Instrumentation", "Feature Flagging",
```
```169:176:csv_engine/utils/config.py
"Google Analytics", "Google Data Studio", "Looker Studio", "Mixpanel", "Amplitude",
"PostHog", "Heap", "FullStory", "Hotjar", "Pendo",
"Segment", "RudderStack", ..., "Airbyte", "dbt", ..., 
"Apache Superset", "Metabase", "Mode Analytics",
```
```165:168:csv_engine/utils/config.py
"AWS", "Azure", "GCP", ..., "Oracle Cloud",

# Data Warehouses
"BigQuery", "Redshift",
```
```186:190:csv_engine/utils/config.py
"Google Meet", ..., "Lucidchart",

# Experimentation & Feature Flags
"Optimizely", "VWO", "LaunchDarkly",
```

¿Quieres que agregue alguna herramienta adicional concreta (p.ej., Snowplow, mParticle, Tealium) o roles específicos de producto/analítica que suelas ver en tus fuentes?

```python
# Data Roles
"Data Analyst", ..., "AI Engineer", "AI Specialist", "Analytics Engineer", "Growth Analyst", 
"Insights Analyst", "Experimentation Analyst", "BI Engineer", "Data Product Manager",
```

```python
"Business Intelligence Manager", "Strategy Manager", "Operations Manager",
"Product Operations",
```

```python
"A/B Testing", "Hypothesis Testing", ..., 
"Experimentation", "Experiment Design", "Causal Inference", "Cohort Analysis",
"Funnel Analysis", "Retention Analysis", "Attribution Modeling",
```

```python
"Product Analytics", "Growth Hacking",
"Tracking Plan", "Event Taxonomy", "Event Tracking", "Instrumentation", "Feature Flagging",
```

```python
"Google Analytics", "Google Data Studio", "Looker Studio", "Mixpanel", "Amplitude",
"PostHog", "Heap", "FullStory", "Hotjar", "Pendo",
"Segment", "RudderStack", ..., "Airbyte", "dbt", ..., 
"Apache Superset", "Metabase", "Mode Analytics",
```

```python
"AWS", "Azure", "GCP", ..., "Oracle Cloud",

# Data Warehouses
"BigQuery", "Redshift",
```

```python
"Google Meet", ..., "Lucidchart",

# Experimentation & Feature Flags
"Optimizely", "VWO", "LaunchDarkly",
```

---

**User**

¿se puede integrar el programa:

D:\Work Work\Upwork\DataPM\csv_engine\utils\title_normalizer.py

a la escritura del csv de:

D:\Work Work\Upwork\DataPM\csv_engine\engines\datapm_processor.py

para que el job title (short) de cada fila ya haya sido previamente revisado por segunda vez y normalizado?

Plantea si sería posible o mejor opción:

a) Ejecutar el programa de forma externa desde su archivo python separado del motor principal

o

b) Reescribir el código del normalizador dentro del programa del motor de procesamiento

---

**Cursor**

Voy a revisar `csv_engine/utils/title_normalizer.py` para ver su API y proponer la mejor forma de integrarlo (idealmente importándolo y llamándolo desde `process_data`). Luego te propongo la integración concreta.

- Sí, se puede integrar. La mejor opción es no ejecutar el script como proceso aparte ni reescribir su lógica, sino importarlo y aplicarlo en memoria antes de escribir cada CSV de batch. Esto evita doble I/O, mantiene una sola fuente de verdad del mapeo y asegura que el “Job title (short)” salga ya normalizado en cada archivo.

Recomendación:
- Opción b (integrar en el motor) pero sin “copiar/pegar” código: importar la función `normalize_titles` y aplicarla a cada batch justo antes de escribir el CSV.
- Evitar la opción a (ejecutar externamente) porque escribe, vuelve a leer y reescribe, con más I/O y mayor tiempo.

Integración sugerida dentro de `csv_engine/engines/datapm_processor.py` (en el loop de batches):
```python
import pandas as pd
from csv_engine.utils.title_normalizer import normalize_titles

# ... dentro del for de batches, después de obtener processed_batch:
df = pd.DataFrame(processed_batch)
df = normalize_titles(df)  # aplica el mapeo TITLE_MAPPING y mantiene las columnas
processed_batch = df.to_dict(orient="records")
self.write_csv(processed_batch, batch_output_path)
```

- Esto ejecuta la “segunda pasada” de normalización de títulos antes de escribir cada archivo en `csv/src/csv_processed`.
- No hay redundancias: el mapeo central se mantiene en `csv_engine/utils/title_normalizer.py`, y el motor sólo lo usa.

```python
import pandas as pd
from csv_engine.utils.title_normalizer import normalize_titles

# ... dentro del for de batches, después de obtener processed_batch:
df = pd.DataFrame(processed_batch)
df = normalize_titles(df)  # aplica el mapeo TITLE_MAPPING y mantiene las columnas
processed_batch = df.to_dict(orient="records")
self.write_csv(processed_batch, batch_output_path)
```

---

**User**

¿ya has hecho las modificaciones correspondientes en los programas para funcionar con tu sistema sugerido? de no haberlas hecho, ejecuta

---

**Cursor**

Voy a integrar la normalización de títulos en el motor, importando la función desde `utils/title_normalizer.py` y aplicándola a cada batch antes de escribir el CSV. Luego reviso lints.

```python
#!/usr/bin/env python3
"""
DataPM Processor - Replica la automatización de Make.com para análisis de trabajos
Procesa descripciones de trabajo con LLM (Gemini/Ollama) y genera CSV estructurado
"""

import csv
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse
import pandas as pd

# Configuración de LLM
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Google Gemini no disponible. Instala con: pip install google-generativeai")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Requests no disponible. Instala con: pip install requests")


# Extensiones y utilidades de import para reutilizar funciones existentes
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_ENGINE_ROOT = os.path.dirname(CURRENT_DIR)
REPO_ROOT = os.path.dirname(CSV_ENGINE_ROOT)

# Permitir importar módulos hermanos como `normalization.split_batches`
if CSV_ENGINE_ROOT not in sys.path:
    sys.path.append(CSV_ENGINE_ROOT)

try:
    from normalization.split_batches import split_csv_batches  # type: ignore
except Exception:
    split_csv_batches = None

try:
    from utils.title_normalizer import normalize_titles  # type: ignore
except Exception:
    normalize_titles = None


class DataPMProcessor:
    """Procesador principal para análisis de descripciones de trabajo"""
    
    def __init__(self, llm_type: str = "gemini", api_key: Optional[str] = None, 
                 ollama_url: str = "http://localhost:11434"):
        """
        Inicializa el procesador
        
        Args:
            llm_type: "gemini" o "ollama"
            api_key: API key para Gemini (requerido si llm_type="gemini")
            ollama_url: URL del servidor Ollama
        """
        self.llm_type = llm_type
        self.api_key = api_key
        self.ollama_url = ollama_url
        
        # Configurar Gemini si está disponible
        if llm_type == "gemini" and GEMINI_AVAILABLE:
            if not api_key:
                raise ValueError("API key requerida para Gemini")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Schema de normalización (igual que en Make.com)
        self.schema = {
            "job_title_original": "string",
            "job_title_short": "string",  # Normalizado a valores específicos
            "experience_years": "string",  # "0-3", "3-5", "5+"
            "job_schedule_type": "string",  # "Full-time", "Part-time", "Contract", "Internship", "Unknown"
            "seniority": "string",  # "Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"
            "city": "string",
            "state": "string",  # Abreviación de 2 letras para US/CA
            "country": "string",
            "degrees": "array",  # Array de strings
            "skills": "array",   # Array de strings
            "software": "array", # Array de strings
            "company_name": "string"
        }
        
        # Valores normalizados permitidos
        self.normalized_values = {
            "job_title_short": [
                "Product Manager", "Data Analyst", "Data Scientist", "Data Engineer", 
                "UX/UI Designer", "Software Engineer", "Marketing Specialist", 
                "Project Manager", "Business Analyst", "Process Designer", 
                "Product Designer", "IT Analyst", "DevOps Engineer",
                "Quality Assurance Engineer", "Documentation Specialist",
                "Financial Analyst", "Compliance Analyst", "Operations Manager", 
                "Other"
            ],
            "experience_years": ["0-3", "3-5", "5+"],
            "job_schedule_type": ["Full-time", "Part-time", "Contract", "Internship", "Unknown"],
            "seniority": ["Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"],
            "degrees": [
                "Bachelor's Degree", "Master's Degree", "PhD", "Associate's Degree", 
                "Higher Education", "Engineering", "Automotive Engineering", 
                "Vocational Training", "Other"
            ],
            "skills": [
                "Project Management", "Agile", "Scrum", "API", "Cloud Computing", 
                "Machine Learning", "Data Analysis", "Data Visualization", 
                "User Research", "UI/UX Design", "Product Design", "Product Management", 
                "Marketing", "Sales", "Communication", "Problem Solving", 
                "Process Optimization", "Regulatory Compliance", "Document Management", 
                "Quality Control", "Auditing", "Technical Writing", "Statistical Reporting", 
                "Business Acumen", "Cross-functional Collaboration", "Team Leadership", 
                "Healthcare Knowledge", "Supply Chain", "SDLC", "User-Centered Design",
                "Quality Assurance", "Test Automation", "Clinical Documentation",
                "Investment Banking", "Supply Chain Management", "Operations Management",
                "KYC/AML Compliance", "Financial Analysis"
            ],
            "software": [
                "SQL", "Python", "R", "C", "C++", "Java", "JavaScript", "Microsoft Excel", 
                "Figma", "Sketch", "Adobe XD", "Adobe Creative Suite", "Tableau", 
                "Power BI", "Jira", "Confluence", "Atlassian", "SAP", "Salesforce", 
                "HubSpot", "Google Analytics", "Looker", "MicroStrategy", "GitHub", 
                "GitLab", "DevOps Tools", "Vercel", "Next.js", "Prisma", "PlanetScale", 
                "Rhino", "Keyshot", "SolidWorks", "C4D", "OneDrive", "Word", "IMDS", 
                "Pytorch", "Flow", "AWS", "Azure", "GCP", "SQL Server", "Oracle", 
                "MongoDB", "PostgreSQL", "Apache Spark", "Veeva Vault", "Jenkins",
                "JUnit", "Cypress", "Selenium", "TestRail", "Bloomberg Terminal"
            ]
        }
    
    def create_system_prompt(self) -> str:
        """Crea el prompt del sistema igual que en Make.com"""
        return f"""You are a strict data extractor and standardizer. You MUST return ONLY a valid JSON object and nothing else.
The JSON must follow this schema:

job_title_original (string)

job_title_short (string, normalized to one of these values: {self.normalized_values['job_title_short']})

experience_years (string, normalized to one of these formats: "0-3" for less than 3 years, "3-5" for ranges, "5+" for 5 or more years)

job_schedule_type (string, normalized to one of these values: {self.normalized_values['job_schedule_type']})

seniority (string, normalized to one of these values: {self.normalized_values['seniority']})

city (string, normalized to proper case, e.g., "New York", "Madrid". If not found, use "Unknown".)

state (string, normalized to two-letter abbreviation if in the US/CA, e.g., "NY", "CA". If not in the US/CA or not found, use "Unknown".)

country (string, normalized to proper case, e.g., "United States", "Spain", "Mexico", "United Kingdom", "Germany", "France", "Panamá", "Venezuela", "European Union", "Unknown")

degrees (array of strings, normalized to one of these values: {self.normalized_values['degrees']})

skills (array of strings, normalized to a fixed set of values like: {self.normalized_values['skills']})

software (array of strings, normalized to a fixed set of values like: {self.normalized_values['software']})

company_name (string)

If you cannot determine a value, use "Unknown" for strings and blank space for arrays, data slot must be empty. No extra text, no markdown, no explanation."""

    def create_user_prompt(self, description: str) -> str:
        """Crea el prompt del usuario"""
        return f"""INPUT: {{"text":"{description}"}}
TASK: Analyze INPUT.text and return the JSON according to the schema in the system instructions."""

    def call_gemini(self, description: str) -> Dict[str, Any]:
        """Llama a Google Gemini para procesar la descripción"""
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Google Gemini no está disponible")
        
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                system_prompt = self.create_system_prompt()
                user_prompt = self.create_user_prompt(description)
                
                response = self.model.generate_content([
                    {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}
                ])
                
                # Extraer JSON de la respuesta
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                return json.loads(response_text.strip())
                
            except Exception as e:
                error_str = str(e)
                
                # Verificar si es un error de rate limiting
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    retry_count += 1
                    
                    # Extraer el tiempo de espera del error si está disponible
                    wait_time = 60  # Tiempo por defecto
                    if "retry_delay" in error_str:
                        try:
                            # Buscar el tiempo de espera en el mensaje de error
                            import re
                            match = re.search(r'seconds":\s*(\d+)', error_str)
                            if match:
                                wait_time = int(match.group(1))
                        except:
                            pass
                    
                    print(f"⏳ Rate limit alcanzado. Esperando {wait_time} segundos... (intento {retry_count}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    # Si no es rate limiting, es un error real
                    print(f"❌ Error con Gemini: {e}")
                    return self.get_default_response()
        
        # Si se agotaron los reintentos
        print(f"❌ Se agotaron los reintentos por rate limiting")
        return self.get_default_response()

    def call_ollama(self, description: str) -> Dict[str, Any]:
        """Llama a Ollama para procesar la descripción"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("Requests no está disponible")
        
        try:
            system_prompt = self.create_system_prompt()
            user_prompt = self.create_user_prompt(description)
            
            payload = {
                "model": "llama3.2:3b",  # Puedes cambiar el modelo
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False
            }
            
            response = requests.post(f"{self.ollama_url}/api/chat", json=payload)
            response.raise_for_status()
            
            response_text = response.json()["message"]["content"].strip()
            
            # Extraer JSON de la respuesta
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            return json.loads(response_text.strip())
            
        except Exception as e:
            print(f"❌ Error con Ollama: {e}")
            return self.get_default_response()

    def get_default_response(self) -> Dict[str, Any]:
        """Retorna una respuesta por defecto en caso de error"""
        return {
            "job_title_original": "Unknown",
            "job_title_short": "Unknown",
            "experience_years": "Unknown",
            "job_schedule_type": "Unknown",
            "seniority": "Unknown",
            "city": "Unknown",
            "state": "Unknown",
            "country": "Unknown",
            "degrees": [],
            "skills": [],
            "software": [],
            "company_name": "Unknown"
        }

    def process_description(self, description: str) -> Dict[str, Any]:
        """Procesa una descripción usando el LLM configurado"""
        print(f"🤖 Procesando descripción con {self.llm_type.upper()}...")
        
        if self.llm_type == "gemini":
            return self.call_gemini(description)
        elif self.llm_type == "ollama":
            return self.call_ollama(description)
        else:
            raise ValueError(f"LLM tipo '{self.llm_type}' no soportado")

    def read_csv(self, file_path: str) -> List[Dict[str, str]]:
        """Lee el CSV de entrada"""
        print(f"📖 Leyendo CSV: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        data = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        
        print(f"✅ Leídos {len(data)} registros")
        return data

    def process_data(self, input_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Procesa todos los datos de entrada"""
        print(f"🔄 Procesando {len(input_data)} registros...")
        
        processed_data = []
        
        for i, row in enumerate(input_data, 1):
            print(f"📝 Procesando registro {i}/{len(input_data)}")
            
            # Extraer datos del CSV
            title = row.get('title', '')
            company = row.get('company', '')
            location = row.get('location', '')
            description = row.get('description', '')
            
            # Procesar con LLM con manejo de errores mejorado
            try:
                llm_result = self.process_description(description)
                
                # Verificar si el resultado es válido (no todo Unknown)
                if llm_result.get('job_title_short') == 'Unknown' and all(
                    v == 'Unknown' or v == [] for k, v in llm_result.items() 
                    if k not in ['job_title_original', 'degrees', 'skills', 'software']
                ):
                    print(f"⚠️  Resultado sospechoso para registro {i}, reintentando...")
                    # Reintentar una vez más
                    time.sleep(2)
                    llm_result = self.process_description(description)
                
                # Combinar datos originales con resultados del LLM
                processed_row = {
                    'Job title (original)': title,
                    'Job title (short)': llm_result.get('job_title_short', 'Unknown'),
                    'Company': llm_result.get('company_name', company),
                    'Country': llm_result.get('country', 'Unknown'),
                    'State': llm_result.get('state', 'Unknown'),
                    'City': llm_result.get('city', 'Unknown'),
                    'Schedule type': llm_result.get('job_schedule_type', 'Unknown'),
                    'Experience years': llm_result.get('experience_years', 'Unknown'),
                    'Seniority': llm_result.get('seniority', 'Unknown'),
                    'Skills': '; '.join(llm_result.get('skills', [])),
                    'Degrees': '; '.join(llm_result.get('degrees', [])),
                    'Software': '; '.join(llm_result.get('software', []))
                }
                
                processed_data.append(processed_row)
                
            except Exception as e:
                print(f"❌ Error procesando registro {i}: {e}")
                # Agregar una fila con datos mínimos en lugar de todo Unknown
                processed_row = {
                    'Job title (original)': title,
                    'Job title (short)': 'Error',
                    'Company': company,
                    'Country': 'Unknown',
                    'State': 'Unknown',
                    'City': 'Unknown',
                    'Schedule type': 'Unknown',
                    'Experience years': 'Unknown',
                    'Seniority': 'Unknown',
                    'Skills': '',
                    'Degrees': '',
                    'Software': ''
                }
                processed_data.append(processed_row)
            
            # Pausa para evitar rate limiting (ajustado a 5 segundos)
            if i < len(input_data):
                time.sleep(5)
        
        print(f"✅ Procesamiento completado")
        return processed_data

    def write_csv(self, data: List[Dict[str, Any]], output_path: str):
        """Escribe el CSV de salida"""
        print(f"💾 Guardando CSV: {output_path}")
        
        if not data:
            print("⚠️  No hay datos para guardar")
            return
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        print(f"✅ CSV guardado exitosamente")

    def run(self, input_file: str, output_file: Optional[str] = None):
        """Ejecuta el procesamiento completo generando un CSV por cada 10 filas procesadas"""
        print("🚀 Iniciando DataPM Processor")
        print(f"📊 LLM: {self.llm_type.upper()}")
        
        # Determinar directorio de salida
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_file:
            # Si se proporcionó una ruta, usar su directorio; si es un directorio, usarlo tal cual
            output_dir = output_file if os.path.isdir(output_file) else os.path.dirname(output_file) or os.path.join(REPO_ROOT, "csv", "src", "csv_processed")
        else:
            output_dir = os.path.join(REPO_ROOT, "csv", "src", "csv_processed")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Leer datos de entrada
            input_data = self.read_csv(input_file)
            
            # Procesar y guardar en batches de 10 filas
            batch_size = 10
            total_rows = len(input_data)
            batch_count = 0
            for i in range(0, total_rows, batch_size):
                batch_count += 1
                batch_slice = input_data[i:i+batch_size]
                print(f"🔄 Procesando batch {batch_count} con {len(batch_slice)} filas...")
                processed_batch = self.process_data(batch_slice)
                
                # Normalizar títulos (segunda pasada) si está disponible
                if normalize_titles is not None:
                    try:
                        df = pd.DataFrame(processed_batch)
                        df = normalize_titles(df)
                        processed_batch = df.to_dict(orient="records")
                    except Exception as e:
                        print(f"⚠️  No se pudo normalizar títulos: {e}")
                batch_filename = f"{timestamp}_DataPM_result_batch_{batch_count}.csv"
                batch_output_path = os.path.join(output_dir, batch_filename)
                self.write_csv(processed_batch, batch_output_path)
            
            print(f"🎉 Procesamiento completado exitosamente!")
            print(f"📁 Archivos de salida en: {output_dir}")
            
        except Exception as e:
            print(f"❌ Error durante el procesamiento: {e}")
            sys.exit(1)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="DataPM Processor - Análisis de descripciones de trabajo")
    parser.add_argument("input_file", help="Archivo CSV o carpeta de entrada (si se pasa carpeta, se usa el CSV más reciente). Use 'latest' para tomar el más reciente de csv/src/scrapped")
    parser.add_argument("--output", "-o", help="Archivo CSV de salida (opcional)")
    parser.add_argument("--llm", choices=["gemini", "ollama"], default="gemini", 
                       help="Tipo de LLM a usar (default: gemini)")
    parser.add_argument("--api-key", help="API key para Gemini (requerido si --llm=gemini)")
    parser.add_argument("--ollama-url", default="http://localhost:11434", 
                       help="URL del servidor Ollama (default: http://localhost:11434)")
    
    args = parser.parse_args()
    
    # Validaciones
    if args.llm == "gemini" and not args.api_key:
        print("❌ Error: --api-key es requerido para Gemini")
        print("💡 Obtén tu API key en: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    # Resolver input: permitir directorio o palabra clave 'latest'
    def resolve_input_path(input_arg: str) -> str:
        # Si es directorio, tomar el CSV más reciente
        if os.path.isdir(input_arg):
            candidates = [
                os.path.join(input_arg, f) for f in os.listdir(input_arg)
                if f.lower().endswith('.csv')
            ]
            if not candidates:
                raise FileNotFoundError(f"No se encontraron CSV en la carpeta: {input_arg}")
            return max(candidates, key=os.path.getmtime)
        
        # Si es 'latest', usar carpeta por defecto csv/src/scrapped
        if input_arg.strip().lower() in {"latest", "auto"}:
            default_scrapped = os.path.join(REPO_ROOT, "csv", "src", "scrapped")
            candidates = [
                os.path.join(default_scrapped, f) for f in os.listdir(default_scrapped)
                if f.lower().endswith('.csv')
            ]
            if not candidates:
                raise FileNotFoundError(f"No se encontraron CSV en: {default_scrapped}")
            return max(candidates, key=os.path.getmtime)
        
        # En otro caso, tratar como archivo
        return input_arg

    resolved_input = resolve_input_path(args.input_file)

    # Crear y ejecutar procesador
    processor = DataPMProcessor(
        llm_type=args.llm,
        api_key=args.api_key,
        ollama_url=args.ollama_url
    )
    
    processor.run(resolved_input, args.output)


if __name__ == "__main__":
    main()

```

- Integré la normalización de títulos al motor: ahora cada batch pasa por `utils/title_normalizer.normalize_titles` antes de escribirse a CSV.

Bloque clave añadido:
```412:427:csv_engine/engines/datapm_processor.py
# Normalizar títulos (segunda pasada) si está disponible
if normalize_titles is not None:
    try:
        df = pd.DataFrame(processed_batch)
        df = normalize_titles(df)
        processed_batch = df.to_dict(orient="records")
    except Exception as e:
        print(f"⚠️  No se pudo normalizar títulos: {e}")
```

- Importaciones agregadas:
```12:16:csv_engine/engines/datapm_processor.py
import argparse
import pandas as pd
...
from utils.title_normalizer import normalize_titles  # fallback seguro si no carga
```

- No hay errores de lint.

¿Deseas que normalicemos también skills/software con una función similar si la extraemos a utilidades en el futuro?

```python
# Normalizar títulos (segunda pasada) si está disponible
if normalize_titles is not None:
    try:
        df = pd.DataFrame(processed_batch)
        df = normalize_titles(df)
        processed_batch = df.to_dict(orient="records")
    except Exception as e:
        print(f"⚠️  No se pudo normalizar títulos: {e}")
```

```python
import argparse
import pandas as pd
...
from utils.title_normalizer import normalize_titles  # fallback seguro si no carga
```

---

**User**

¿eres capaz de añadir el filtro de búsqueda "Past week" de la búsqueda linkedin? te comparto el url entero de un enlace de búsqueda que lo tiene aplicado como referencia:

@https://www.linkedin.com/jobs/search/?currentJobId=4285391949&distance=25.0&f_TPR=r604800&f_WT=2&geoId=105646813&keywords=(%22Product%20Manager%22%20OR%20%22Product%20Associate%22%20OR%20%22Product%20Analyst%22%20OR%20%22Product%20Operations%22)%20AND%20(%22analyst%22%20OR%20%22product%22)%20NOT%20(%22Sr.%22%20OR%20%22senior%22%20OR%20%22lead%22%20OR%20%22director%22)&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true&spellCorrectionEnabled=true 

1) Confirma capacidad y código muestra antes de ejecutar cambios
2) De ser posible, confirma adicionalmente que se pueda añadir como parámetro configurable, que no quede fijo cómo única modalidad de búsqueda

---

**Cursor**

Sí, es posible. LinkedIn usa el parámetro f_TPR para filtrar por fecha; por ejemplo, “Past week” corresponde a f_TPR=r604800, como en tu URL de referencia [enlace](https://www.linkedin.com/jobs/search/?currentJobId=4285391949&distance=25.0&f_TPR=r604800&f_WT=2&geoId=105646813&keywords=(%22Product%20Manager%22%20OR%20%22Product%20Associate%22%20OR%20%22Product%20Analyst%22%20OR%20%22Product%20Operations%22)%20AND%20(%22analyst%22%20OR%20%22product%22)%20NOT%20(%22Sr.%22%20OR%20%22senior%22%20OR%20%22lead%22%20OR%20%22director%22)&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true&spellCorrectionEnabled=true).

Propuesta (configurable, no fijo). Muestra de código a añadir:
```python
# mapping y argumento CLI
POSTED_MAP = {'any': None, '24h': 'r86400', 'week': 'r604800', 'month': 'r2592000'}
parser.add_argument('--posted', choices=POSTED_MAP.keys(), default='any', help='Filtro por fecha de publicación')

# al construir la URL
encoded_keywords = quote_plus(KEYWORDS)
encoded_location = quote_plus(LOCATION)
posted_param = POSTED_MAP[args.posted]

search_url = (
    "https://www.linkedin.com/jobs/search/"
    f"?keywords={encoded_keywords}"
    f"&location={encoded_location}"
    f"&f_WT={REMOTE_FILTER}"
    f"&distance=25"
)
if posted_param:
    search_url += f"&f_TPR={posted_param}"
```

¿Procedo a implementar esto en `scrapper/linkedin_selenium.py` con `--posted` opcional (valores: any, 24h, week, month)?

```python
# mapping y argumento CLI
POSTED_MAP = {'any': None, '24h': 'r86400', 'week': 'r604800', 'month': 'r2592000'}
parser.add_argument('--posted', choices=POSTED_MAP.keys(), default='any', help='Filtro por fecha de publicación')

# al construir la URL
encoded_keywords = quote_plus(KEYWORDS)
encoded_location = quote_plus(LOCATION)
posted_param = POSTED_MAP[args.posted]

search_url = (
    "https://www.linkedin.com/jobs/search/"
    f"?keywords={encoded_keywords}"
    f"&location={encoded_location}"
    f"&f_WT={REMOTE_FILTER}"
    f"&distance=25"
)
if posted_param:
    search_url += f"&f_TPR={posted_param}"
```

---

**User**

1) ¿Los números quedarían fijos y funcionarían igual sin importar la fecha?
2) De ser afirmativa la respuesta a la pregunta, procede con la ejecución sin pedir confirmación adicional
3) Confirma que las instrucciones de aplicación sería poner el nombre de variable: any, week o month en el campo del parámetro correspondiente

---

**Cursor**

Voy a agregar un parámetro opcional '--posted' al scrapper con opciones any/week/month que mapea a f_TPR y actualizar la construcción del URL. Luego verifico lints.

```python
# --- FUNCIÓN REUTILIZABLE PARA NAVEGAR ENTRE PÁGINAS ---
def go_to_page(driver, target_page, current_page=None):
    """Navega a la página target_page desde la página actual o desde current_page si se indica."""
    print(f"Navegando hasta la página: {target_page}")
    for p in range((current_page or 1) + 1, target_page + 1):
        next_selectors = [
            f"button[aria-label='Page {p}']",
            "button[aria-label='Next']",
            "button[aria-label='Siguiente']",
            "li.artdeco-pagination__indicator--active + li button",
            "button.artdeco-pagination__button--next"
        ]
        next_button = None
        for selector in next_selectors:
            try:
                next_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except TimeoutException:
                continue
        if next_button:
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            random_delay(1, 2)
            next_button.click()
            print(f"✅ Navegado a página {p}")
            random_delay(3, 5)
        else:
            print(f"🚫 No se encontró botón para la página {p}. Abortando navegación.")
            break
from selenium import webdriver
from datetime import datetime
import time
import csv
import random
import re
import os
from urllib.parse import quote_plus

# --- CONFIGURACIÓN DE USUARIO ---
import argparse
EMAIL = "11-10466@usb.ve"  
PASSWORD = "SanJudas.2011"  
KEYWORDS = '("Product Manager" OR "Product Associate" OR "Product Analyst" OR "Product Operations") AND ("analyst" OR "product") NOT ("Sr." OR "senior" OR "lead" OR "director")'
LOCATION = "Spain"
REMOTE_FILTER = "2"   # 2 = Remote

# Argumentos para rango de páginas
parser = argparse.ArgumentParser(description="LinkedIn Scraper con rango de páginas")
parser.add_argument('--page-start', type=int, default=1, help='Página inicial a scrapear')
parser.add_argument('--page-end', type=int, default=2, help='Página final a scrapear')
parser.add_argument('--posted', choices=['any', 'week', 'month'], default='any', help='Filtro por fecha de publicación (any/week/month)')
args = parser.parse_args()
PAGE_START = args.page_start
PAGE_END = args.page_end

# --- CONFIGURACIÓN ANTI-DETECCIÓN ---
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ANTI-DETECCIÓN ---
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")

# Agregar User-Agent personalizado
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

# Deshabilitar WebGL para evitar fingerprinting
options.add_argument("--disable-webgl")
options.add_argument("--disable-3d-apis")

# Agregar preferencias adicionales
options.add_experimental_option("prefs", {
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False,
    "profile.default_content_setting_values.notifications": 2
})

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options)

# Ocultar que es automatizado
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def random_delay(min_seconds=1, max_seconds=3):
    """Pausa aleatoria para evitar detección"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def safe_find_element(driver, by, selector, timeout=10):
    """Busca elemento de forma segura con múltiples intentos"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    except TimeoutException:
        return None

def safe_find_elements(driver, by, selector, timeout=10):
    """Busca elementos de forma segura"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by, selector))
        )
    except TimeoutException:
        return []

def verify_login_success(driver):
    """Verifica si el login fue exitoso"""
    try:
        # Esperar a que aparezca el feed o el perfil
        WebDriverWait(driver, 15).until(
            EC.any_of(
                EC.url_contains("/feed/"),
                EC.url_contains("/mynetwork/"),
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.global-nav"))
            )
        )
        return True
    except TimeoutException:
        return False

def extract_text_safe(element, default=""):
    """Extrae texto de forma segura"""
    try:
        return element.text.strip() if element else default
    except:
        return default

def clean_text_for_csv(text):
    """Limpia texto para CSV"""
    if not text:
        return ""
    # Remover caracteres problemáticos y normalizar
    cleaned = re.sub(r'[\r\n\t]', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

# --- 1. LOGIN LINKEDIN CON VERIFICACIÓN ---
print("Iniciando login en LinkedIn...")
driver.get("https://www.linkedin.com/login")
random_delay(2, 4)

# Buscar campos de login
email_field = safe_find_element(driver, By.ID, "username")
password_field = safe_find_element(driver, By.ID, "password")

if not email_field or not password_field:
    print("❌ Error: No se encontraron los campos de login")
    driver.quit()
    exit(1)

# Llenar formulario de manera más humana
for char in EMAIL:
    email_field.send_keys(char)
    random_delay(0.1, 0.3)  # Pequeña pausa entre caracteres

random_delay(1, 2)  # Pausa antes de pasar a la contraseña

for char in PASSWORD:
    password_field.send_keys(char)
    random_delay(0.1, 0.3)  # Pequeña pausa entre caracteres

random_delay(1.5, 2.5)  # Pausa antes de dar enter
password_field.send_keys(Keys.RETURN)

# Verificar login exitoso con más tiempo de espera
print("Verificando login...")
if not verify_login_success(driver):
    print("❌ Error: Login fallido. Verifica credenciales o captcha")
    # Guardar screenshot para debug
    try:
        driver.save_screenshot("login_error.png")
        print("Se ha guardado una captura de pantalla en 'login_error.png'")
    except:
        pass
    driver.quit()
    exit(1)

print("✅ Login exitoso")

# --- 2. NAVEGAR A BÚSQUEDA CON VERIFICACIÓN ---
print("Navegando a resultados de búsqueda...")
encoded_keywords = quote_plus(KEYWORDS)
encoded_location = quote_plus(LOCATION)
search_url = (
    f"https://www.linkedin.com/jobs/search/"
    f"?keywords={encoded_keywords}"
    f"&location={encoded_location}"
    f"&f_WT={REMOTE_FILTER}"
    f"&distance=25"
)

# Añadir filtro de fecha (f_TPR) si se solicita
POSTED_MAP = {
    'any': None,
    'week': 'r604800',      # Past week
    'month': 'r2592000',    # Past month (~30 días)
}
posted_param = POSTED_MAP.get(args.posted)
if posted_param:
    search_url += f"&f_TPR={posted_param}"

driver.get(search_url)
random_delay(3, 5)

# Verificar que llegamos a la página de empleos
WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
)
job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")

if not job_cards:
    print("❌ Error: No se encontraron resultados de empleos")
    driver.quit()
    exit(1)

print(f"✅ Encontrados {len(job_cards)} empleos para procesar")

results = []
processed_count = 0


# --- NAVEGAR HASTA LA PÁGINA DE INICIO SI ES NECESARIO ---
if PAGE_START > 1:
    go_to_page(driver, PAGE_START, current_page=1)

for page in range(PAGE_START, PAGE_END + 1):
    print(f"\n📄 Procesando página {page}/{PAGE_END}...")
    
    # Esperar y localizar las tarjetas en la página actual
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
    )
    job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")
    
    if not job_cards:
        print(f"⚠️  No se encontraron ofertas en la página {page}. Saltando...")
        continue
    
    print(f"✅ Encontrados {len(job_cards)} empleos en página {page}")
    
    for idx, card in enumerate(job_cards, start=1):
        try:
            print(f"Procesando empleo {idx}/{len(job_cards)} (página {page})...")
            
            # Re-find el elemento para evitar StaleElementReferenceException
            card = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")[idx-1]
            
            # Scroll y click seguro
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            random_delay(1, 2)
            
            # Intentar click con múltiples estrategias
            try:
                card.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", card)
            except StaleElementReferenceException:
                # Re-find y reintentar
                card = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")[idx-1]
                card.click()

            # Esperar carga del panel de detalles con múltiples selectores
            detail_selectors = [
                "div.jobs-search__job-details--wrapper",
                "div.job-details-jobs-unified-top-card__container--two-pane",
                "div.jobs-unified-top-card__content"
            ]
            
            detail_loaded = False
            for selector in detail_selectors:
                if safe_find_element(driver, By.CSS_SELECTOR, selector, timeout=5):
                    detail_loaded = True
                    break
            
            if not detail_loaded:
                print(f"⚠️  Saltando empleo {page}-{idx}: No se cargaron los detalles")
                continue

            random_delay(1, 2)

            # Extraer datos con múltiples selectores de fallback
            title = ""
            title_selectors = [
                "div.job-details-jobs-unified-top-card__container--two-pane h1.t-24",
                "h1.t-24",
                "h1.job-details-jobs-unified-top-card__job-title",
                "h1"
            ]
            
            for selector in title_selectors:
                title_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if title_elem:
                    title = extract_text_safe(title_elem)
                    break
            
            company = ""
            company_selectors = [
                "div.job-details-jobs-unified-top-card__company-name a",
                "div.job-details-jobs-unified-top-card__company-name",
                "a[data-control-name='job_details_company_name']",
                "span.job-details-jobs-unified-top-card__company-name"
            ]
            
            for selector in company_selectors:
                company_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if company_elem:
                    company = extract_text_safe(company_elem)
                    break
            
            location = ""
            location_selectors = [
                "div.job-details-jobs-unified-top-card__primary-description-container span.tvm__text",
                "span.job-details-jobs-unified-top-card__bullet",
                "span[aria-label*='location']",
                "div.job-details-jobs-unified-top-card__primary-description-container"
            ]
            
            for selector in location_selectors:
                location_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if location_elem:
                    location = extract_text_safe(location_elem)
                    break
            
            description = ""
            description_selectors = [
                "article.jobs-description__container div.jobs-description-content__text--stretch",
                "div.jobs-description-content__text",
                "div.jobs-box__html-content",
                "div[data-job-description]"
            ]
            
            for selector in description_selectors:
                desc_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if desc_elem:
                    description = extract_text_safe(desc_elem)
                    break

            # Validar que tenemos al menos título y empresa
            if not title or not company:
                print(f"⚠️  Saltando empleo {page}-{idx}: Datos insuficientes")
                continue
        
            # Limpiar datos para CSV
            title = clean_text_for_csv(title)
            company = clean_text_for_csv(company)
            location = clean_text_for_csv(location)
            description = clean_text_for_csv(description)

            print(f"✅ [{page}-{idx}] {title[:50]}... | {company} | {location}")
            
            results.append({
                "title": title,
                "company": company,
                "location": location,
                "description": description
            })
            
            processed_count += 1
            random_delay(1, 3)  # Pausa entre empleos

        except Exception as e:
            print(f"❌ Error procesando empleo #{page}-{idx}: {str(e)}")
            continue
    
    # Buscar y hacer clic en "Siguiente" para la siguiente página
    if page < PAGE_END:  # No intentar navegar después de la última página configurada
        try:
            go_to_page(driver, page + 1, current_page=page)
        except Exception as e:
            print(f"❌ Error navegando a página {page + 1}: {str(e)}")
            break

# --- 4. GUARDAR EN CSV CON VALIDACIÓN ---
if results:
    # Crear directorio de salida absoluto: <repo_root>/csv/src/scrapped
    scrapped_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "csv",
        "src",
        "scrapped",
    )
    os.makedirs(scrapped_dir, exist_ok=True)

    # Guardar TODO en un único archivo CSV por ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scrape_filename = os.path.join(scrapped_dir, f"{timestamp}_linkedin_jobs.csv")

    try:
        with open(scrape_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "company", "location", "description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ {len(results)} ofertas guardadas en {scrape_filename}")
        print(f"✅ Proceso completado: {processed_count} ofertas totales procesadas")
    except Exception as e:
        print(f"❌ Error guardando CSV: {str(e)}")
else:
    print("❌ No se extrajo ningún empleo válido")

driver.quit()
```

- Sí: los valores f_TPR son intervalos relativos en segundos (e.g., r604800 = 7 días) y funcionan igual sin importar la fecha actual.
- Ya implementé el parámetro opcional en `scrapper/linkedin_selenium.py`.

Instrucciones:
- Usa el flag `--posted` con uno de: `any`, `week`, `month`.
- Ejemplos:
  - Sin filtro: `--posted any` (por defecto).
  - Última semana: `--posted week`.
  - Último mes: `--posted month`.

Resumen de cambios clave:
- Nuevo argumento CLI:
```python
parser.add_argument('--posted', choices=['any', 'week', 'month'], default='any', help='Filtro por fecha de publicación (any/week/month)')
```
- Mapeo al parámetro de LinkedIn:
```python
POSTED_MAP = {'any': None, 'week': 'r604800', 'month': 'r2592000'}
posted_param = POSTED_MAP.get(args.posted)
if posted_param:
    search_url += f"&f_TPR={posted_param}"
```

```python
parser.add_argument('--posted', choices=['any', 'week', 'month'], default='any', help='Filtro por fecha de publicación (any/week/month)')
```

```python
POSTED_MAP = {'any': None, 'week': 'r604800', 'month': 'r2592000'}
posted_param = POSTED_MAP.get(args.posted)
if posted_param:
    search_url += f"&f_TPR={posted_param}"
```

---

**User**

Haz que la modificación de este parámetro sea tan fácil como en el conjunto:

# --- CONFIGURACIÓN DE USUARIO ---

1) Añade el campo para la variable de rango de tiempo como último en esta lista, es decir, después de: REMOTE_FILTER =
de forma que sólo tenga que poner el valor de la variable luego del '='
2) Ahora este conjunto se llama: # --- CONFIGURACIÓN DE BÚSQUEDA ---
3) Agrega las opciones de value posibles para estas dos últimas opciones: REMOTE_FILTER y el del rango del tiempo como comentario en sus respectivas líneas

---

**Cursor**

Voy a añadir la variable de rango de tiempo en el bloque de configuración, renombrar la sección a “CONFIGURACIÓN DE BÚSQUEDA”, y ajustar el uso para que la variable sea la predeterminada y el flag CLI siga siendo opcional. Luego verifico lints.

```python
*** Begin Patch
*** Update File: scrapper/linkedin_selenium.py
@@
-# --- CONFIGURACIÓN DE USUARIO ---
+# --- CONFIGURACIÓN DE BÚSQUEDA ---
 import argparse
 EMAIL = "11-10466@usb.ve"  
 PASSWORD = "SanJudas.2011"  
 KEYWORDS = '("Business Analyst" OR "Product Analyst" OR "Data Analyst" OR "BI Analyst") AND (analyst OR "product") NOT (senior OR lead OR director)'
 LOCATION = "Spain"
-REMOTE_FILTER = "2"   # 2 = Remote
+REMOTE_FILTER = "2"   # 1=On-site, 2=Remote, 3=Hybrid
+POSTED_RANGE = "any"  # any | week | month
@@
-parser = argparse.ArgumentParser(description="LinkedIn Scraper con rango de páginas")
+parser = argparse.ArgumentParser(description="LinkedIn Scraper con rango de páginas")
 parser.add_argument('--page-start', type=int, default=1, help='Página inicial a scrapear')
 parser.add_argument('--page-end', type=int, default=2, help='Página final a scrapear')
-parser.add_argument('--posted', choices=['any', 'week', 'month'], default='any', help='Filtro por fecha de publicación (any/week/month)')
+parser.add_argument('--posted', choices=['any', 'week', 'month'], default=None, help='Filtro por fecha de publicación (any/week/month)')
 args = parser.parse_args()
 PAGE_START = args.page_start
 PAGE_END = args.page_end
@@
-# Añadir filtro de fecha (f_TPR) si se solicita
+# Añadir filtro de fecha (f_TPR) si se solicita
 POSTED_MAP = {
     'any': None,
     'week': 'r604800',      # Past week
     'month': 'r2592000',    # Past month (~30 días)
 }
-posted_param = POSTED_MAP.get(args.posted)
+posted_choice = args.posted if args.posted is not None else POSTED_RANGE
+posted_param = POSTED_MAP.get(posted_choice)
 if posted_param:
     search_url += f"&f_TPR={posted_param}"
*** End Patch
```

```python
# --- FUNCIÓN REUTILIZABLE PARA NAVEGAR ENTRE PÁGINAS ---
def go_to_page(driver, target_page, current_page=None):
    """Navega a la página target_page desde la página actual o desde current_page si se indica."""
    print(f"Navegando hasta la página: {target_page}")
    for p in range((current_page or 1) + 1, target_page + 1):
        next_selectors = [
            f"button[aria-label='Page {p}']",
            "button[aria-label='Next']",
            "button[aria-label='Siguiente']",
            "li.artdeco-pagination__indicator--active + li button",
            "button.artdeco-pagination__button--next"
        ]
        next_button = None
        for selector in next_selectors:
            try:
                next_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except TimeoutException:
                continue
        if next_button:
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            random_delay(1, 2)
            next_button.click()
            print(f"✅ Navegado a página {p}")
            random_delay(3, 5)
        else:
            print(f"🚫 No se encontró botón para la página {p}. Abortando navegación.")
            break
from selenium import webdriver
from datetime import datetime
import time
import csv
import random
import re
import os
from urllib.parse import quote_plus

# --- CONFIGURACIÓN DE BÚSQUEDA ---
import argparse
EMAIL = "11-10466@usb.ve"  
PASSWORD = "SanJudas.2011"  
KEYWORDS = '("Product Manager" OR "Product Associate" OR "Product Analyst" OR "Product Operations") AND ("analyst" OR "product") NOT ("Sr." OR "senior" OR "lead" OR "director")'
LOCATION = "Spain"
REMOTE_FILTER = "2"   # 1=On-site, 2=Remote, 3=Hybrid
POSTED_RANGE = "any"  # any | week | month

# Argumentos para rango de páginas
parser = argparse.ArgumentParser(description="LinkedIn Scraper con rango de páginas")
parser.add_argument('--page-start', type=int, default=1, help='Página inicial a scrapear')
parser.add_argument('--page-end', type=int, default=2, help='Página final a scrapear')
parser.add_argument('--posted', choices=['any', 'week', 'month'], default=None, help='Filtro por fecha de publicación (any/week/month)')
args = parser.parse_args()
PAGE_START = args.page_start
PAGE_END = args.page_end

# --- CONFIGURACIÓN ANTI-DETECCIÓN ---
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ANTI-DETECCIÓN ---
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")

# Agregar User-Agent personalizado
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

# Deshabilitar WebGL para evitar fingerprinting
options.add_argument("--disable-webgl")
options.add_argument("--disable-3d-apis")

# Agregar preferencias adicionales
options.add_experimental_option("prefs", {
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False,
    "profile.default_content_setting_values.notifications": 2
})

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options)

# Ocultar que es automatizado
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def random_delay(min_seconds=1, max_seconds=3):
    """Pausa aleatoria para evitar detección"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def safe_find_element(driver, by, selector, timeout=10):
    """Busca elemento de forma segura con múltiples intentos"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    except TimeoutException:
        return None

def safe_find_elements(driver, by, selector, timeout=10):
    """Busca elementos de forma segura"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by, selector))
        )
    except TimeoutException:
        return []

def verify_login_success(driver):
    """Verifica si el login fue exitoso"""
    try:
        # Esperar a que aparezca el feed o el perfil
        WebDriverWait(driver, 15).until(
            EC.any_of(
                EC.url_contains("/feed/"),
                EC.url_contains("/mynetwork/"),
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.global-nav"))
            )
        )
        return True
    except TimeoutException:
        return False

def extract_text_safe(element, default=""):
    """Extrae texto de forma segura"""
    try:
        return element.text.strip() if element else default
    except:
        return default

def clean_text_for_csv(text):
    """Limpia texto para CSV"""
    if not text:
        return ""
    # Remover caracteres problemáticos y normalizar
    cleaned = re.sub(r'[\r\n\t]', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

# --- 1. LOGIN LINKEDIN CON VERIFICACIÓN ---
print("Iniciando login en LinkedIn...")
driver.get("https://www.linkedin.com/login")
random_delay(2, 4)

# Buscar campos de login
email_field = safe_find_element(driver, By.ID, "username")
password_field = safe_find_element(driver, By.ID, "password")

if not email_field or not password_field:
    print("❌ Error: No se encontraron los campos de login")
    driver.quit()
    exit(1)

# Llenar formulario de manera más humana
for char in EMAIL:
    email_field.send_keys(char)
    random_delay(0.1, 0.3)  # Pequeña pausa entre caracteres

random_delay(1, 2)  # Pausa antes de pasar a la contraseña

for char in PASSWORD:
    password_field.send_keys(char)
    random_delay(0.1, 0.3)  # Pequeña pausa entre caracteres

random_delay(1.5, 2.5)  # Pausa antes de dar enter
password_field.send_keys(Keys.RETURN)

# Verificar login exitoso con más tiempo de espera
print("Verificando login...")
if not verify_login_success(driver):
    print("❌ Error: Login fallido. Verifica credenciales o captcha")
    # Guardar screenshot para debug
    try:
        driver.save_screenshot("login_error.png")
        print("Se ha guardado una captura de pantalla en 'login_error.png'")
    except:
        pass
    driver.quit()
    exit(1)

print("✅ Login exitoso")

# --- 2. NAVEGAR A BÚSQUEDA CON VERIFICACIÓN ---
print("Navegando a resultados de búsqueda...")
encoded_keywords = quote_plus(KEYWORDS)
encoded_location = quote_plus(LOCATION)
search_url = (
    f"https://www.linkedin.com/jobs/search/"
    f"?keywords={encoded_keywords}"
    f"&location={encoded_location}"
    f"&f_WT={REMOTE_FILTER}"
    f"&distance=25"
)

# Añadir filtro de fecha (f_TPR) si se solicita
POSTED_MAP = {
    'any': None,
    'week': 'r604800',      # Past week
    'month': 'r2592000',    # Past month (~30 días)
}
posted_param = POSTED_MAP.get(args.posted)
if posted_param:
    search_url += f"&f_TPR={posted_param}"

driver.get(search_url)
random_delay(3, 5)

# Verificar que llegamos a la página de empleos
WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
)
job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")

if not job_cards:
    print("❌ Error: No se encontraron resultados de empleos")
    driver.quit()
    exit(1)

print(f"✅ Encontrados {len(job_cards)} empleos para procesar")

results = []
processed_count = 0


# --- NAVEGAR HASTA LA PÁGINA DE INICIO SI ES NECESARIO ---
if PAGE_START > 1:
    go_to_page(driver, PAGE_START, current_page=1)

for page in range(PAGE_START, PAGE_END + 1):
    print(f"\n📄 Procesando página {page}/{PAGE_END}...")
    
    # Esperar y localizar las tarjetas en la página actual
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
    )
    job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")
    
    if not job_cards:
        print(f"⚠️  No se encontraron ofertas en la página {page}. Saltando...")
        continue
    
    print(f"✅ Encontrados {len(job_cards)} empleos en página {page}")
    
    for idx, card in enumerate(job_cards, start=1):
        try:
            print(f"Procesando empleo {idx}/{len(job_cards)} (página {page})...")
            
            # Re-find el elemento para evitar StaleElementReferenceException
            card = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")[idx-1]
            
            # Scroll y click seguro
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            random_delay(1, 2)
            
            # Intentar click con múltiples estrategias
            try:
                card.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", card)
            except StaleElementReferenceException:
                # Re-find y reintentar
                card = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")[idx-1]
                card.click()

            # Esperar carga del panel de detalles con múltiples selectores
            detail_selectors = [
                "div.jobs-search__job-details--wrapper",
                "div.job-details-jobs-unified-top-card__container--two-pane",
                "div.jobs-unified-top-card__content"
            ]
            
            detail_loaded = False
            for selector in detail_selectors:
                if safe_find_element(driver, By.CSS_SELECTOR, selector, timeout=5):
                    detail_loaded = True
                    break
            
            if not detail_loaded:
                print(f"⚠️  Saltando empleo {page}-{idx}: No se cargaron los detalles")
                continue

            random_delay(1, 2)

            # Extraer datos con múltiples selectores de fallback
            title = ""
            title_selectors = [
                "div.job-details-jobs-unified-top-card__container--two-pane h1.t-24",
                "h1.t-24",
                "h1.job-details-jobs-unified-top-card__job-title",
                "h1"
            ]
            
            for selector in title_selectors:
                title_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if title_elem:
                    title = extract_text_safe(title_elem)
                    break
            
            company = ""
            company_selectors = [
                "div.job-details-jobs-unified-top-card__company-name a",
                "div.job-details-jobs-unified-top-card__company-name",
                "a[data-control-name='job_details_company_name']",
                "span.job-details-jobs-unified-top-card__company-name"
            ]
            
            for selector in company_selectors:
                company_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if company_elem:
                    company = extract_text_safe(company_elem)
                    break
            
            location = ""
            location_selectors = [
                "div.job-details-jobs-unified-top-card__primary-description-container span.tvm__text",
                "span.job-details-jobs-unified-top-card__bullet",
                "span[aria-label*='location']",
                "div.job-details-jobs-unified-top-card__primary-description-container"
            ]
            
            for selector in location_selectors:
                location_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if location_elem:
                    location = extract_text_safe(location_elem)
                    break
            
            description = ""
            description_selectors = [
                "article.jobs-description__container div.jobs-description-content__text--stretch",
                "div.jobs-description-content__text",
                "div.jobs-box__html-content",
                "div[data-job-description]"
            ]
            
            for selector in description_selectors:
                desc_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if desc_elem:
                    description = extract_text_safe(desc_elem)
                    break

            # Validar que tenemos al menos título y empresa
            if not title or not company:
                print(f"⚠️  Saltando empleo {page}-{idx}: Datos insuficientes")
                continue
        
            # Limpiar datos para CSV
            title = clean_text_for_csv(title)
            company = clean_text_for_csv(company)
            location = clean_text_for_csv(location)
            description = clean_text_for_csv(description)

            print(f"✅ [{page}-{idx}] {title[:50]}... | {company} | {location}")
            
            results.append({
                "title": title,
                "company": company,
                "location": location,
                "description": description
            })
            
            processed_count += 1
            random_delay(1, 3)  # Pausa entre empleos

        except Exception as e:
            print(f"❌ Error procesando empleo #{page}-{idx}: {str(e)}")
            continue
    
    # Buscar y hacer clic en "Siguiente" para la siguiente página
    if page < PAGE_END:  # No intentar navegar después de la última página configurada
        try:
            go_to_page(driver, page + 1, current_page=page)
        except Exception as e:
            print(f"❌ Error navegando a página {page + 1}: {str(e)}")
            break

# --- 4. GUARDAR EN CSV CON VALIDACIÓN ---
if results:
    # Crear directorio de salida absoluto: <repo_root>/csv/src/scrapped
    scrapped_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "csv",
        "src",
        "scrapped",
    )
    os.makedirs(scrapped_dir, exist_ok=True)

    # Guardar TODO en un único archivo CSV por ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scrape_filename = os.path.join(scrapped_dir, f"{timestamp}_linkedin_jobs.csv")

    try:
        with open(scrape_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "company", "location", "description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ {len(results)} ofertas guardadas en {scrape_filename}")
        print(f"✅ Proceso completado: {processed_count} ofertas totales procesadas")
    except Exception as e:
        print(f"❌ Error guardando CSV: {str(e)}")
else:
    print("❌ No se extrajo ningún empleo válido")

driver.quit()
```

```python
# --- FUNCIÓN REUTILIZABLE PARA NAVEGAR ENTRE PÁGINAS ---
def go_to_page(driver, target_page, current_page=None):
    """Navega a la página target_page desde la página actual o desde current_page si se indica."""
    print(f"Navegando hasta la página: {target_page}")
    for p in range((current_page or 1) + 1, target_page + 1):
        next_selectors = [
            f"button[aria-label='Page {p}']",
            "button[aria-label='Next']",
            "button[aria-label='Siguiente']",
            "li.artdeco-pagination__indicator--active + li button",
            "button.artdeco-pagination__button--next"
        ]
        next_button = None
        for selector in next_selectors:
            try:
                next_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                break
            except TimeoutException:
                continue
        if next_button:
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            random_delay(1, 2)
            next_button.click()
            print(f"✅ Navegado a página {p}")
            random_delay(3, 5)
        else:
            print(f"🚫 No se encontró botón para la página {p}. Abortando navegación.")
            break
from selenium import webdriver
from datetime import datetime
import time
import csv
import random
import re
import os
from urllib.parse import quote_plus

# --- CONFIGURACIÓN DE BÚSQUEDA ---
import argparse
EMAIL = "11-10466@usb.ve"  
PASSWORD = "SanJudas.2011"  
KEYWORDS = '("Product Manager" OR "Product Associate" OR "Product Analyst" OR "Product Operations") AND ("analyst" OR "product") NOT ("Sr." OR "senior" OR "lead" OR "director")'
LOCATION = "Spain"
REMOTE_FILTER = "2"   # 1=On-site, 2=Remote, 3=Hybrid
POSTED_RANGE = "any"  # any | week | month

# Argumentos para rango de páginas
parser = argparse.ArgumentParser(description="LinkedIn Scraper con rango de páginas")
parser.add_argument('--page-start', type=int, default=1, help='Página inicial a scrapear')
parser.add_argument('--page-end', type=int, default=2, help='Página final a scrapear')
parser.add_argument('--posted', choices=['any', 'week', 'month'], default=None, help='Filtro por fecha de publicación (any/week/month)')
args = parser.parse_args()
PAGE_START = args.page_start
PAGE_END = args.page_end

# --- CONFIGURACIÓN ANTI-DETECCIÓN ---
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ANTI-DETECCIÓN ---
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")

# Agregar User-Agent personalizado
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

# Deshabilitar WebGL para evitar fingerprinting
options.add_argument("--disable-webgl")
options.add_argument("--disable-3d-apis")

# Agregar preferencias adicionales
options.add_experimental_option("prefs", {
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False,
    "profile.default_content_setting_values.notifications": 2
})

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options)

# Ocultar que es automatizado
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def random_delay(min_seconds=1, max_seconds=3):
    """Pausa aleatoria para evitar detección"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def safe_find_element(driver, by, selector, timeout=10):
    """Busca elemento de forma segura con múltiples intentos"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    except TimeoutException:
        return None

def safe_find_elements(driver, by, selector, timeout=10):
    """Busca elementos de forma segura"""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by, selector))
        )
    except TimeoutException:
        return []

def verify_login_success(driver):
    """Verifica si el login fue exitoso"""
    try:
        # Esperar a que aparezca el feed o el perfil
        WebDriverWait(driver, 15).until(
            EC.any_of(
                EC.url_contains("/feed/"),
                EC.url_contains("/mynetwork/"),
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.global-nav"))
            )
        )
        return True
    except TimeoutException:
        return False

def extract_text_safe(element, default=""):
    """Extrae texto de forma segura"""
    try:
        return element.text.strip() if element else default
    except:
        return default

def clean_text_for_csv(text):
    """Limpia texto para CSV"""
    if not text:
        return ""
    # Remover caracteres problemáticos y normalizar
    cleaned = re.sub(r'[\r\n\t]', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

# --- 1. LOGIN LINKEDIN CON VERIFICACIÓN ---
print("Iniciando login en LinkedIn...")
driver.get("https://www.linkedin.com/login")
random_delay(2, 4)

# Buscar campos de login
email_field = safe_find_element(driver, By.ID, "username")
password_field = safe_find_element(driver, By.ID, "password")

if not email_field or not password_field:
    print("❌ Error: No se encontraron los campos de login")
    driver.quit()
    exit(1)

# Llenar formulario de manera más humana
for char in EMAIL:
    email_field.send_keys(char)
    random_delay(0.1, 0.3)  # Pequeña pausa entre caracteres

random_delay(1, 2)  # Pausa antes de pasar a la contraseña

for char in PASSWORD:
    password_field.send_keys(char)
    random_delay(0.1, 0.3)  # Pequeña pausa entre caracteres

random_delay(1.5, 2.5)  # Pausa antes de dar enter
password_field.send_keys(Keys.RETURN)

# Verificar login exitoso con más tiempo de espera
print("Verificando login...")
if not verify_login_success(driver):
    print("❌ Error: Login fallido. Verifica credenciales o captcha")
    # Guardar screenshot para debug
    try:
        driver.save_screenshot("login_error.png")
        print("Se ha guardado una captura de pantalla en 'login_error.png'")
    except:
        pass
    driver.quit()
    exit(1)

print("✅ Login exitoso")

# --- 2. NAVEGAR A BÚSQUEDA CON VERIFICACIÓN ---
print("Navegando a resultados de búsqueda...")
encoded_keywords = quote_plus(KEYWORDS)
encoded_location = quote_plus(LOCATION)
search_url = (
    f"https://www.linkedin.com/jobs/search/"
    f"?keywords={encoded_keywords}"
    f"&location={encoded_location}"
    f"&f_WT={REMOTE_FILTER}"
    f"&distance=25"
)

# Añadir filtro de fecha (f_TPR) si se solicita
POSTED_MAP = {
    'any': None,
    'week': 'r604800',      # Past week
    'month': 'r2592000',    # Past month (~30 días)
}
posted_choice = args.posted if args.posted is not None else POSTED_RANGE
posted_param = POSTED_MAP.get(posted_choice)
if posted_param:
    search_url += f"&f_TPR={posted_param}"

driver.get(search_url)
random_delay(3, 5)

# Verificar que llegamos a la página de empleos
WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
)
job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")

if not job_cards:
    print("❌ Error: No se encontraron resultados de empleos")
    driver.quit()
    exit(1)

print(f"✅ Encontrados {len(job_cards)} empleos para procesar")

results = []
processed_count = 0


# --- NAVEGAR HASTA LA PÁGINA DE INICIO SI ES NECESARIO ---
if PAGE_START > 1:
    go_to_page(driver, PAGE_START, current_page=1)

for page in range(PAGE_START, PAGE_END + 1):
    print(f"\n📄 Procesando página {page}/{PAGE_END}...")
    
    # Esperar y localizar las tarjetas en la página actual
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
    )
    job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")
    
    if not job_cards:
        print(f"⚠️  No se encontraron ofertas en la página {page}. Saltando...")
        continue
    
    print(f"✅ Encontrados {len(job_cards)} empleos en página {page}")
    
    for idx, card in enumerate(job_cards, start=1):
        try:
            print(f"Procesando empleo {idx}/{len(job_cards)} (página {page})...")
            
            # Re-find el elemento para evitar StaleElementReferenceException
            card = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")[idx-1]
            
            # Scroll y click seguro
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            random_delay(1, 2)
            
            # Intentar click con múltiples estrategias
            try:
                card.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", card)
            except StaleElementReferenceException:
                # Re-find y reintentar
                card = driver.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]")[idx-1]
                card.click()

            # Esperar carga del panel de detalles con múltiples selectores
            detail_selectors = [
                "div.jobs-search__job-details--wrapper",
                "div.job-details-jobs-unified-top-card__container--two-pane",
                "div.jobs-unified-top-card__content"
            ]
            
            detail_loaded = False
            for selector in detail_selectors:
                if safe_find_element(driver, By.CSS_SELECTOR, selector, timeout=5):
                    detail_loaded = True
                    break
            
            if not detail_loaded:
                print(f"⚠️  Saltando empleo {page}-{idx}: No se cargaron los detalles")
                continue

            random_delay(1, 2)

            # Extraer datos con múltiples selectores de fallback
            title = ""
            title_selectors = [
                "div.job-details-jobs-unified-top-card__container--two-pane h1.t-24",
                "h1.t-24",
                "h1.job-details-jobs-unified-top-card__job-title",
                "h1"
            ]
            
            for selector in title_selectors:
                title_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if title_elem:
                    title = extract_text_safe(title_elem)
                    break
            
            company = ""
            company_selectors = [
                "div.job-details-jobs-unified-top-card__company-name a",
                "div.job-details-jobs-unified-top-card__company-name",
                "a[data-control-name='job_details_company_name']",
                "span.job-details-jobs-unified-top-card__company-name"
            ]
            
            for selector in company_selectors:
                company_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if company_elem:
                    company = extract_text_safe(company_elem)
                    break
            
            location = ""
            location_selectors = [
                "div.job-details-jobs-unified-top-card__primary-description-container span.tvm__text",
                "span.job-details-jobs-unified-top-card__bullet",
                "span[aria-label*='location']",
                "div.job-details-jobs-unified-top-card__primary-description-container"
            ]
            
            for selector in location_selectors:
                location_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if location_elem:
                    location = extract_text_safe(location_elem)
                    break
            
            description = ""
            description_selectors = [
                "article.jobs-description__container div.jobs-description-content__text--stretch",
                "div.jobs-description-content__text",
                "div.jobs-box__html-content",
                "div[data-job-description]"
            ]
            
            for selector in description_selectors:
                desc_elem = safe_find_element(driver, By.CSS_SELECTOR, selector)
                if desc_elem:
                    description = extract_text_safe(desc_elem)
                    break

            # Validar que tenemos al menos título y empresa
            if not title or not company:
                print(f"⚠️  Saltando empleo {page}-{idx}: Datos insuficientes")
                continue
        
            # Limpiar datos para CSV
            title = clean_text_for_csv(title)
            company = clean_text_for_csv(company)
            location = clean_text_for_csv(location)
            description = clean_text_for_csv(description)

            print(f"✅ [{page}-{idx}] {title[:50]}... | {company} | {location}")
            
            results.append({
                "title": title,
                "company": company,
                "location": location,
                "description": description
            })
            
            processed_count += 1
            random_delay(1, 3)  # Pausa entre empleos

        except Exception as e:
            print(f"❌ Error procesando empleo #{page}-{idx}: {str(e)}")
            continue
    
    # Buscar y hacer clic en "Siguiente" para la siguiente página
    if page < PAGE_END:  # No intentar navegar después de la última página configurada
        try:
            go_to_page(driver, page + 1, current_page=page)
        except Exception as e:
            print(f"❌ Error navegando a página {page + 1}: {str(e)}")
            break

# --- 4. GUARDAR EN CSV CON VALIDACIÓN ---
if results:
    # Crear directorio de salida absoluto: <repo_root>/csv/src/scrapped
    scrapped_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "csv",
        "src",
        "scrapped",
    )
    os.makedirs(scrapped_dir, exist_ok=True)

    # Guardar TODO en un único archivo CSV por ejecución
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scrape_filename = os.path.join(scrapped_dir, f"{timestamp}_linkedin_jobs.csv")

    try:
        with open(scrape_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "company", "location", "description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"\n✅ {len(results)} ofertas guardadas en {scrape_filename}")
        print(f"✅ Proceso completado: {processed_count} ofertas totales procesadas")
    except Exception as e:
        print(f"❌ Error guardando CSV: {str(e)}")
else:
    print("❌ No se extrajo ningún empleo válido")

driver.quit()
```

- Sí, f_TPR usa segundos relativos (r604800 = 7 días). Funciona igual sin importar la fecha.
- Ya apliqué los cambios pedidos.

Qué cambió en `scrapper/linkedin_selenium.py`:
- Renombré la sección a `# --- CONFIGURACIÓN DE BÚSQUEDA ---`.
- Añadí `POSTED_RANGE` al final del bloque de config para edición directa.
- Agregué comentarios con opciones válidas.

Fragmento:
```40:47:scrapper/linkedin_selenium.py
# --- CONFIGURACIÓN DE BÚSQUEDA ---
import argparse
EMAIL = "11-10466@usb.ve"  
PASSWORD = "SanJudas.2011"  
KEYWORDS = '("Product Manager" OR "Product Associate" OR "Product Analyst" OR "Product Operations") AND ("analyst" OR "product") NOT ("Sr." OR "senior" OR "lead" OR "director")'
LOCATION = "Spain"
REMOTE_FILTER = "2"   # 1=On-site, 2=Remote, 3=Hybrid
POSTED_RANGE = "any"  # any | week | month
```

Aplicación del filtro en URL (usa CLI si se pasa, si no usa POSTED_RANGE):
```205:217:scrapper/linkedin_selenium.py
POSTED_MAP = {
    'any': None,
    'week': 'r604800',      # Past week
    'month': 'r2592000',    # Past month (~30 días)
}
posted_choice = args.posted if args.posted is not None else POSTED_RANGE
posted_param = POSTED_MAP.get(posted_choice)
if posted_param:
    search_url += f"&f_TPR={posted_param}"
```

- Parámetro CLI opcional sigue disponible: `--posted any|week|month`.
- Instrucciones: puedes cambiar directamente en el bloque de búsqueda:
  - `REMOTE_FILTER = "1|2|3"`  // 1=On-site, 2=Remote, 3=Hybrid
  - `POSTED_RANGE = "any|week|month"`

```python
# --- CONFIGURACIÓN DE BÚSQUEDA ---
import argparse
EMAIL = "11-10466@usb.ve"  
PASSWORD = "SanJudas.2011"  
KEYWORDS = '("Product Manager" OR "Product Associate" OR "Product Analyst" OR "Product Operations") AND ("analyst" OR "product") NOT ("Sr." OR "senior" OR "lead" OR "director")'
LOCATION = "Spain"
REMOTE_FILTER = "2"   # 1=On-site, 2=Remote, 3=Hybrid
POSTED_RANGE = "any"  # any | week | month
```

```python
POSTED_MAP = {
    'any': None,
    'week': 'r604800',      # Past week
    'month': 'r2592000',    # Past month (~30 días)
}
posted_choice = args.posted if args.posted is not None else POSTED_RANGE
posted_param = POSTED_MAP.get(posted_choice)
if posted_param:
    search_url += f"&f_TPR={posted_param}"
```

---

**User**

Ahora ejecuta el motor:

D:\Work Work\Upwork\DataPM\csv_engine\engines\datapm_processor.py

Sobre los dos archivos más recientes de: 

D:\Work Work\Upwork\DataPM\csv\src\scrapped

Usando la API key:

AIzaSyCU2RQKO9i0Cm8t6NhBCcCozVuH3lgeUfY

---

**Cursor**

```powershell
$dir = "csv\src\scrapped"; 
$files = Get-ChildItem -Path $dir -Filter *.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 2; 
foreach($f in $files) { python "csv_engine\engines\datapm_processor.py" "$($f.FullName)" --llm gemini --api-key "KEY" | cat }
```

```powershell
$dir="csv\\src\\scrapped"; 
$files = Get-ChildItem -Path $dir -Filter *.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 2; 
foreach($f in $files) { python "csv_engine\\engines\\datapm_processor.py" "$($f.FullName)" --llm gemini --api-key "AIzaSy..." }
```

Voy a ejecutar el procesador sobre los dos CSV más recientes de `csv/src/scrapped` usando tu API key de Gemini. Esto puede tardar varios minutos por los llamados al LLM; lo lanzarė en segundo plano y te avisaré cuando termine.

Instalaré dependencias necesarias (google-generativeai, pandas, requests) y volveré a lanzar el procesador sobre los 2 CSV más recientes en segundo plano. Esto garantiza que Gemini funcione y que la normalización por pandas esté disponible.

- Ejecuté el procesador sobre los 2 CSV más recientes de `csv/src/scrapped` con Gemini usando tu API key. Instalé/actualicé `google-generativeai`, `pandas` y `requests` y dejé la ejecución en segundo plano.
- Salida esperada: archivos por lotes de 10 filas en `csv/src/csv_processed` con nombres tipo `<timestamp>_DataPM_result_batch_<N>.csv`. Cada batch aplica la normalización adicional de títulos.
- Esto puede tardar (pausas anti rate-limit + llamadas al LLM). Te aviso cuando termine y listo los archivos generados.

---

**User**

En los batches de: D:\Work Work\Upwork\DataPM\csv\src\csv_processed

Hay un error donde algunos roles de Product Analyst fueron identificados como "Data Analyst"

1) Identifica este error en los batches exportados en:

D:\Work Work\Upwork\DataPM\csv\src\csv_processed

2) Corrige estos mapeos erróneos en el conjunto TITLE_MAPPING de:

D:\Work Work\Upwork\DataPM\csv_engine\utils\title_normalizer.py

3) Ejecuta esta normalización en los batches ya exportados en:

D:\Work Work\Upwork\DataPM\csv\src\csv_processed

4) Retoma el procesamiento con:

D:\Work Work\Upwork\DataPM\csv_engine\engines\datapm_processor.py

por donde lo dejaste (leer en terminal)

---

**Cursor**

Voy a revisar los 5 CSV exportados para detectar filas donde el título original contenga “Product Analyst” pero el título corto sea “Data Analyst”. Luego actualizaré el mapeo en `title_normalizer.py`, aplicaré la normalización sobre esos archivos y retomaré el procesamiento con el segundo archivo que quedó a medias.

Voy a actualizar `TITLE_MAPPING` para mapear “Product Analyst” (y variantes como “Payments Product Analyst”) a “Product Analyst”, aplicar la normalización sobre los CSV ya generados en `csv/src/csv_processed`, y reanudar el procesamiento del segundo archivo scrappeado.

```python
#!/usr/bin/env python3
"""
Title Normalizer - Actualiza los CSVs procesados al nuevo schema de títulos
"""

import csv
import os
import shutil
from datetime import datetime
import pandas as pd

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "csv", "src", "csv_processed")  # Carpeta con los CSVs procesados
ARCHIVE_DIR = os.path.join(PROCESSED_DIR, "archive")

# Mapeo de títulos antiguos a nuevos
TITLE_MAPPING = {
     # Machine Learning / Data
    "Machine Learning Engineer": "ML Engineer",
    "ML Engineer": "ML Engineer",
    "Machine-Learning Engineer": "ML Engineer",
    "Data Scientist & AI": "Data Scientist",
    "Junior Data Scientist & AI": "Data Scientist",
    "Junior Data Scientist": "Data Scientist",
    "Senior Data Scientist": "Data Scientist",
    "Data Science Engineer": "Data Scientist",
    "Data Science": "Data Scientist",

    # Data general / BI
   "Senior Data Analyst": "Data Analyst",
    "Junior Data Analyst": "Data Analyst",
    "Business Intelligence Analyst": "BI Analyst",
    "Analytics Analyst": "Data Analyst",
    "Insights Analyst": "Data Analyst",
    "Experimentation Analyst": "Data Analyst",
    "Data Platform Engineer": "Data Engineer",
    "Data Architect": "Data Engineer",

    # QA / Testing
    "QA Manual": "QA / Test Engineer",
    "QA Manual Tester": "QA / Test Engineer",
    "Manual QA": "QA / Test Engineer",
    "QA Engineer": "QA / Test Engineer",
    "QA": "QA / Test Engineer",
    "Quality Assurance Analyst": "QA / Test Engineer",
    "Quality Assurance Engineer": "QA / Test Engineer",
    "QA accesibilidad": "QA / Test Engineer",
    "Consultor/a de pruebas QA": "QA / Test Engineer",
    "Test Engineer": "Test Engineer",
    "Tester": "Test Engineer",
    "Documentation Specialist": "Quality Analyst",

    # Documentación (si no hay canonical específico, se envía a Other / Consultant)
    "Clinical Documentation Specialist": "Other",
    "Trial Master File Specialist": "Other",
    
    # Product
    "Product Analyst": "Product Analyst",
    "Payments Product Analyst": "Product Analyst",
    "Payment Product Analyst": "Product Analyst",
    "Associate Product Manager": "Product Analyst",
    "Product-Owner": "Product Owner",
    "Product Owner (PO)": "Product Owner",
    "Product Specialist": "Product Manager",
    "Product Ops": "Product Operations",
    "Head of Product": "Product Manager",
    "VP of Product": "Product Manager",
    "Product Lead": "Product Manager",

    # Engineering variants
    "Senior Software Engineer": "Software Engineer",
    "Principal Software Engineer": "Software Engineer",
    "Fullstack Developer": "Full Stack Developer",
    "Frontend Engineer": "Frontend Developer",
    "Backend Engineer": "Backend Developer",
    "DevOps Engineer": "DevOps / SRE",
    "SRE": "DevOps / SRE",
    "Site Reliability Engineer": "DevOps / SRE",
    "iOS Developer": "Mobile Developer",
    "Android Developer": "Mobile Developer",
    "Backend/Frontend Developer": "Full Stack Developer",
    "Software Developer": "Software Engineer",

    # Marketing & Growth variants
    "Growth Analyst": "Growth / Performance Analyst",
    "Performance Marketing Specialist": "Growth / Performance Analyst",
    "Content Marketing Specialist": "Digital Marketing Specialist",
    "SEO Specialist": "Digital Marketing Specialist",
    "SEM Specialist": "Digital Marketing Specialist",

    # Project & Business
    "PMO": "Project Manager",
    "PMO Junior": "Project Manager",
    "Scrum Master": "Project Manager",
    "Project Coordinator": "Project Manager",
    "Program Manager": "Project Manager",
    "Business Development Specialist": "Business Analyst",
    "Process Designer": "Process Analyst",
    "Process Manager": "Process Analyst",
    "Implementation Consultant": "Implementation / Onboarding Manager",
    "Implementation Manager": "Implementation / Onboarding Manager",
    "Onboarding Specialist": "Implementation / Onboarding Manager",

    # Operations & IT
    "Supply Chain Manager": "Operations Manager",
    "Operations Analyst": "Operations Manager",
    "Sysadmin": "System Administrator",
    "IT Support": "Technical Support Engineer",
    "Helpdesk": "Technical Support Engineer",

    # Compliance & Quality (concordando con tu schema)
    "Compliance Specialist": "Compliance / Regulatory Specialist",
    "Compliance Analyst": "Compliance / Regulatory Specialist",
    "Regulatory Affairs Specialist": "Compliance / Regulatory Specialist",
    "Quality Analyst": "Quality Analyst",
    "Auditor": "Auditor",
    "Risk Analyst": "Risk Analyst",

    # Sales & Customer Success
    "Customer Success Manager": "Customer Success",
    "Customer Success Specialist": "Customer Success",
    "CSM": "Customer Success",
    "Key Account Manager": "Account Manager",
    "Business Development Manager": "Sales Manager",
    "Commercial Manager": "Sales Manager",
    "Sales Rep": "Sales Representative",

    # Research & UX Research
    "Market Research Analyst": "Research Analyst",
    "UX Researcher": "User Researcher",

    # Finance -> conservador a Business Analyst (no tiene Financial Analyst en schema)
    "Investment Banking Analyst": "Business Analyst",
    "Finanzas Júnior": "Business Analyst",
    "Financial Analyst": "Business Analyst",
    "Finance Analyst": "Business Analyst",

    # Admin & Others
    "Personal Assistant": "Assistant",
    "Executive Assistant": "Assistant",
    "Office Assistant": "Assistant",
    "Administrative Assistant": "Assistant",
    "Advisor / Consultant": "Consultant",
    "Specialist": "Consultant"
}

def ensure_directory(directory):
    """Asegura que el directorio existe"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def archive_file(file_path):
    """Archiva un archivo con timestamp"""
    ensure_directory(ARCHIVE_DIR)
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{name}_{timestamp}{ext}"
    archive_path = os.path.join(ARCHIVE_DIR, archive_name)
    shutil.copy2(file_path, archive_path)
    return archive_path

def normalize_titles(df):
    """Normaliza los títulos en el DataFrame"""
    # Primero intentar mapear desde el título original
    def map_title(row):
        for k, v in TITLE_MAPPING.items():
            if k.lower() in str(row['Job title (original)']).lower():
                return v
        return row['Job title (short)']
    df['Job title (short)'] = df.apply(map_title, axis=1)
    return df

def process_file(file_path):
    """Procesa un archivo CSV"""
    print(f"Procesando: {file_path}")
    # Leer CSV
    df = pd.read_csv(file_path)
    original_count = len(df)
    # Guardar copia para comparar
    df_before = df.copy(deep=True)
    # Normalizar títulos
    df = normalize_titles(df)
    final_count = len(df)
    if final_count != original_count:
        raise ValueError(f"¡Error! Registros no coinciden: {original_count} -> {final_count}")
    # Si no hay cambios, no archivar ni sobrescribir
    if df.equals(df_before):
        print("Sin cambios, no se archiva ni reemplaza.")
        return {'original': original_count, 'final': final_count, 'archived': None, 'updated': False}
    # Archivar versión actual
    archive_path = archive_file(file_path)
    print(f"Archivo respaldado en: {archive_path}")
    # Guardar versión normalizada en la ubicación original
    df.to_csv(file_path, index=False)
    print(f"Archivo actualizado: {file_path}")
    return {'original': original_count, 'final': final_count, 'archived': archive_path, 'updated': True}

def main():
    """Función principal"""
    print("Iniciando normalización de títulos...")
    results = []
    for filename in os.listdir(PROCESSED_DIR):
        file_path = os.path.join(PROCESSED_DIR, filename)
        # Omitir subcarpeta archive y archivos que no sean CSV
        if not filename.endswith('.csv') or os.path.isdir(file_path) or filename == 'archive':
            continue
        try:
            result = process_file(file_path)
            results.append({'file': filename, **result})
        except Exception as e:
            print(f"Error procesando {filename}: {str(e)}")
    # Imprimir resumen
    print("\nResumen de procesamiento:")
    print("-" * 50)
    for result in results:
        print(f"Archivo: {result['file']}")
        print(f"Registros: {result['original']} -> {result['final']}")
        if result.get('updated'):
            print(f"Respaldo: {os.path.basename(result['archived'])}")
        else:
            print("Sin cambios, no se archivó.")
        print("-" * 50)

if __name__ == "__main__":
    main()

```

Voy a corregir la ruta de `PROCESSED_DIR` en `csv_engine/utils/title_normalizer.py` para apuntar a `csv/src/csv_processed`, ejecutar la normalización sobre los CSV ya exportados y luego retomar el procesamiento del segundo archivo con Gemini en segundo plano.

```python
#!/usr/bin/env python3
"""
Title Normalizer - Actualiza los CSVs procesados al nuevo schema de títulos
"""

import csv
import os
import shutil
from datetime import datetime
import pandas as pd

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../csv_engine
REPO_ROOT = os.path.dirname(BASE_DIR)  # repo root
PROCESSED_DIR = os.path.join(REPO_ROOT, "csv", "src", "csv_processed")  # Carpeta con los CSVs procesados
ARCHIVE_DIR = os.path.join(PROCESSED_DIR, "archive")

# Mapeo de títulos antiguos a nuevos
TITLE_MAPPING = {
     # Machine Learning / Data
    "Machine Learning Engineer": "ML Engineer",
    "ML Engineer": "ML Engineer",
    "Machine-Learning Engineer": "ML Engineer",
    "Data Scientist & AI": "Data Scientist",
    "Junior Data Scientist & AI": "Data Scientist",
    "Junior Data Scientist": "Data Scientist",
    "Senior Data Scientist": "Data Scientist",
    "Data Science Engineer": "Data Scientist",
    "Data Science": "Data Scientist",

    # Data general / BI
   "Senior Data Analyst": "Data Analyst",
    "Junior Data Analyst": "Data Analyst",
    "Business Intelligence Analyst": "BI Analyst",
    "Analytics Analyst": "Data Analyst",
    "Insights Analyst": "Data Analyst",
    "Experimentation Analyst": "Data Analyst",
    "Data Platform Engineer": "Data Engineer",
    "Data Architect": "Data Engineer",

    # QA / Testing
    "QA Manual": "QA / Test Engineer",
    "QA Manual Tester": "QA / Test Engineer",
    "Manual QA": "QA / Test Engineer",
    "QA Engineer": "QA / Test Engineer",
    "QA": "QA / Test Engineer",
    "Quality Assurance Analyst": "QA / Test Engineer",
    "Quality Assurance Engineer": "QA / Test Engineer",
    "QA accesibilidad": "QA / Test Engineer",
    "Consultor/a de pruebas QA": "QA / Test Engineer",
    "Test Engineer": "Test Engineer",
    "Tester": "Test Engineer",
    "Documentation Specialist": "Quality Analyst",

    # Documentación (si no hay canonical específico, se envía a Other / Consultant)
    "Clinical Documentation Specialist": "Other",
    "Trial Master File Specialist": "Other",
    
    # Product
    "Product Analyst": "Product Analyst",
    "Payments Product Analyst": "Product Analyst",
    "Payment Product Analyst": "Product Analyst",
    "Associate Product Manager": "Product Analyst",
    "Product-Owner": "Product Owner",
    "Product Owner (PO)": "Product Owner",
    "Product Specialist": "Product Manager",
    "Product Ops": "Product Operations",
    "Head of Product": "Product Manager",
    "VP of Product": "Product Manager",
    "Product Lead": "Product Manager",

    # Engineering variants
    "Senior Software Engineer": "Software Engineer",
    "Principal Software Engineer": "Software Engineer",
    "Fullstack Developer": "Full Stack Developer",
    "Frontend Engineer": "Frontend Developer",
    "Backend Engineer": "Backend Developer",
    "DevOps Engineer": "DevOps / SRE",
    "SRE": "DevOps / SRE",
    "Site Reliability Engineer": "DevOps / SRE",
    "iOS Developer": "Mobile Developer",
    "Android Developer": "Mobile Developer",
    "Backend/Frontend Developer": "Full Stack Developer",
    "Software Developer": "Software Engineer",

    # Marketing & Growth variants
    "Growth Analyst": "Growth / Performance Analyst",
    "Performance Marketing Specialist": "Growth / Performance Analyst",
    "Content Marketing Specialist": "Digital Marketing Specialist",
    "SEO Specialist": "Digital Marketing Specialist",
    "SEM Specialist": "Digital Marketing Specialist",

    # Project & Business
    "PMO": "Project Manager",
    "PMO Junior": "Project Manager",
    "Scrum Master": "Project Manager",
    "Project Coordinator": "Project Manager",
    "Program Manager": "Project Manager",
    "Business Development Specialist": "Business Analyst",
    "Process Designer": "Process Analyst",
    "Process Manager": "Process Analyst",
    "Implementation Consultant": "Implementation / Onboarding Manager",
    "Implementation Manager": "Implementation / Onboarding Manager",
    "Onboarding Specialist": "Implementation / Onboarding Manager",

    # Operations & IT
    "Supply Chain Manager": "Operations Manager",
    "Operations Analyst": "Operations Manager",
    "Sysadmin": "System Administrator",
    "IT Support": "Technical Support Engineer",
    "Helpdesk": "Technical Support Engineer",

    # Compliance & Quality (concordando con tu schema)
    "Compliance Specialist": "Compliance / Regulatory Specialist",
    "Compliance Analyst": "Compliance / Regulatory Specialist",
    "Regulatory Affairs Specialist": "Compliance / Regulatory Specialist",
    "Quality Analyst": "Quality Analyst",
    "Auditor": "Auditor",
    "Risk Analyst": "Risk Analyst",

    # Sales & Customer Success
    "Customer Success Manager": "Customer Success",
    "Customer Success Specialist": "Customer Success",
    "CSM": "Customer Success",
    "Key Account Manager": "Account Manager",
    "Business Development Manager": "Sales Manager",
    "Commercial Manager": "Sales Manager",
    "Sales Rep": "Sales Representative",

    # Research & UX Research
    "Market Research Analyst": "Research Analyst",
    "UX Researcher": "User Researcher",

    # Finance -> conservador a Business Analyst (no tiene Financial Analyst en schema)
    "Investment Banking Analyst": "Business Analyst",
    "Finanzas Júnior": "Business Analyst",
    "Financial Analyst": "Business Analyst",
    "Finance Analyst": "Business Analyst",

    # Admin & Others
    "Personal Assistant": "Assistant",
    "Executive Assistant": "Assistant",
    "Office Assistant": "Assistant",
    "Administrative Assistant": "Assistant",
    "Advisor / Consultant": "Consultant",
    "Specialist": "Consultant"
}

def ensure_directory(directory):
    """Asegura que el directorio existe"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def archive_file(file_path):
    """Archiva un archivo con timestamp"""
    ensure_directory(ARCHIVE_DIR)
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{name}_{timestamp}{ext}"
    archive_path = os.path.join(ARCHIVE_DIR, archive_name)
    shutil.copy2(file_path, archive_path)
    return archive_path

def normalize_titles(df):
    """Normaliza los títulos en el DataFrame"""
    # Primero intentar mapear desde el título original
    def map_title(row):
        for k, v in TITLE_MAPPING.items():
            if k.lower() in str(row['Job title (original)']).lower():
                return v
        return row['Job title (short)']
    df['Job title (short)'] = df.apply(map_title, axis=1)
    return df

def process_file(file_path):
    """Procesa un archivo CSV"""
    print(f"Procesando: {file_path}")
    # Leer CSV
    df = pd.read_csv(file_path)
    original_count = len(df)
    # Guardar copia para comparar
    df_before = df.copy(deep=True)
    # Normalizar títulos
    df = normalize_titles(df)
    final_count = len(df)
    if final_count != original_count:
        raise ValueError(f"¡Error! Registros no coinciden: {original_count} -> {final_count}")
    # Si no hay cambios, no archivar ni sobrescribir
    if df.equals(df_before):
        print("Sin cambios, no se archiva ni reemplaza.")
        return {'original': original_count, 'final': final_count, 'archived': None, 'updated': False}
    # Archivar versión actual
    archive_path = archive_file(file_path)
    print(f"Archivo respaldado en: {archive_path}")
    # Guardar versión normalizada en la ubicación original
    df.to_csv(file_path, index=False)
    print(f"Archivo actualizado: {file_path}")
    return {'original': original_count, 'final': final_count, 'archived': archive_path, 'updated': True}

def main():
    """Función principal"""
    print("Iniciando normalización de títulos...")
    results = []
    for filename in os.listdir(PROCESSED_DIR):
        file_path = os.path.join(PROCESSED_DIR, filename)
        # Omitir subcarpeta archive y archivos que no sean CSV
        if not filename.endswith('.csv') or os.path.isdir(file_path) or filename == 'archive':
            continue
        try:
            result = process_file(file_path)
            results.append({'file': filename, **result})
        except Exception as e:
            print(f"Error procesando {filename}: {str(e)}")
    # Imprimir resumen
    print("\nResumen de procesamiento:")
    print("-" * 50)
    for result in results:
        print(f"Archivo: {result['file']}")
        print(f"Registros: {result['original']} -> {result['final']}")
        if result.get('updated'):
            print(f"Respaldo: {os.path.basename(result['archived'])}")
        else:
            print("Sin cambios, no se archivó.")
        print("-" * 50)

if __name__ == "__main__":
    main()

```

Voy a reanudar el procesamiento del segundo CSV donde quedó interrumpido, usando Gemini, en segundo plano. Esto puede tardar por límites de cuota.

- Detecté el error: “Payments Product Analyst” salió mal clasificado.
  - Evidencias:
```2:9:csv/src/csv_processed/20250818_133026_DataPM_result_batch_3.csv
Payments Product Analyst (Full remote within Spain),Data Analyst,Leadtech,Spain,Unknown,Barcelona,Full-time,0-3,Unknown,Data Analysis; Communication; Problem Solving; Business Acumen,,Microsoft Excel; Google Analytics
```
```2:8:csv/src/csv_processed/20250818_133026_DataPM_result_batch_2.csv
Payments Product Analyst (Full remote within Spain),Business Analyst,Leadtech,Spain,Unknown,Barcelona,Full-time,0-3,Unknown,Data Analysis; Product Management; Communication; Problem Solving; Business Acumen,,Microsoft Excel; Google Analytics
```

- Corrección aplicada en `csv_engine/utils/title_normalizer.py` (TITLE_MAPPING):
  - Añadidos: “Product Analyst”, “Payments Product Analyst”, “Payment Product Analyst” → “Product Analyst”.
  - Con esto, cualquier variación de “Product Analyst” se normaliza correctamente a “Product Analyst”.

- Normalización ejecutada sobre los CSV ya exportados en `csv/src/csv_processed`:
  - Actualicé los archivos in-place y se generaron respaldos en `csv/src/csv_processed/archive` para los que tuvieron cambios.

- Retomé el procesamiento del segundo CSV scrappeado con Gemini en segundo plano. Los nuevos batches se irán guardando en `csv/src/csv_processed`. Nota: puede tardar por límites de cuota de la API.

Resumen:
- Error localizado y documentado.
- Mapeo corregido en el normalizador.
- Batches existentes re-normalizados.
- Proceso reanudado con Gemini.

```csv
Payments Product Analyst (Full remote within Spain),Data Analyst,Leadtech,Spain,Unknown,Barcelona,Full-time,0-3,Unknown,Data Analysis; Communication; Problem Solving; Business Acumen,,Microsoft Excel; Google Analytics
```

```csv
Payments Product Analyst (Full remote within Spain),Business Analyst,Leadtech,Spain,Unknown,Barcelona,Full-time,0-3,Unknown,Data Analysis; Product Management; Communication; Problem Solving; Business Acumen,,Microsoft Excel; Google Analytics
```

---

**User**

¿estás ejecutando el procesador en segundo plano o se detuvo por tu último hallazgo?

Resumen corto de procesos recientes terminados y en curso (de haberlos)

---

**Cursor**

- Estado actual: No hay procesos del procesador ejecutándose ahora. El último intento se detuvo por límite de cuota de Gemini (429).
- Finalizados:
  - Procesado completo del CSV más reciente `20250818_132611_linkedin_jobs.csv` → 5 batches en `csv/src/csv_processed`.
  - Normalización de títulos aplicada a los batches ya generados (mapeo de Product Analyst corregido).
- En curso/pending:
  - El segundo archivo `20250818_113052_linkedin_jobs.csv` quedó interrumpido al inicio del batch 1 por cuota. Puedo reanudar cuando se restablezca la cuota o continuar ahora usando `--llm ollama`.

---

**User**

continúa usando gemini con la clave API:

AIzaSyDNCigTvTv5ItL8ht48LbhDVVvY0inG_bg

de no poder continuar usar la llave de respaldo:

AIzaSyBKJViSNDfdbjAboGMzEBjhqcGMz4TeMAg

---

**Cursor**

Voy a reanudar el procesado del CSV `csv/src/scrapped/20250818_113052_linkedin_jobs.csv` con la clave primaria de Gemini; si falla, haré fallback automático a la clave de respaldo. Configuro UTF-8 para evitar errores de consola.

- Reanudé el procesamiento del archivo `20250818_113052_linkedin_jobs.csv` con Gemini usando la clave primaria, con fallback automático a la clave de respaldo si falla.
- Forcé salida UTF-8 para evitar errores de consola. Te aviso cuando finalice y liste los nuevos batches.

---

**User**

Vamos a necesitar un reforzamiento en la normalización porque tenemos errores tontos como:

Sabiendo que los primeros dos headers son: Job title (original),Job title (short),

Tenemos filas como:

Business Analyst - Especialista en el área de aduanas,Consultant,... (el título claramente empieza por Business Analyst)

Business Analyst,IT Analyst,... (el título claramente empieza por Business Analyst)

Data Analyst Enablement Specialist,Consultant,.... (el título claramente empieza por Business Analyst)

1) Ejecuta mejoramiento del código para prevenir estos errores
2) Ejecuta la normalización mejorada sobre los batches en:

D:\Work Work\Upwork\DataPM\csv\src\csv_processed

3) La única carpeta de archivo debe ser: 

D:\Work Work\Upwork\DataPM\csv\src\archive

Aparentemente el normalizador (verificar cuál programa es) está creando una carpeta de archivo en:

D:\Work Work\Upwork\DataPM\csv\src\csv_processed\archive

Esa carpeta no debe existir en esa ubicación, esa carpeta es sólo para los batches procesados

---

**Cursor**

Voy a reforzar la normalización en `csv_engine/utils/title_normalizer.py` (reglas por prefijo para Business Analyst, Product Analyst, Data Analyst, BI Analyst, etc.), cambiaré la carpeta de archivo a `csv/src/archive`, migraré cualquier archivo de `csv/src/csv_processed/archive` y ejecutaré la normalización sobre los batches existentes. Luego confirmo resultados.

```python
#!/usr/bin/env python3
"""
Title Normalizer - Actualiza los CSVs procesados al nuevo schema de títulos
"""

import csv
import os
import shutil
from datetime import datetime
import pandas as pd

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../csv_engine
REPO_ROOT = os.path.dirname(BASE_DIR)  # repo root
PROCESSED_DIR = os.path.join(REPO_ROOT, "csv", "src", "csv_processed")  # Carpeta con los CSVs procesados
ARCHIVE_DIR = os.path.join(REPO_ROOT, "csv", "src", "archive")  # Única carpeta de archivo

# Mapeo de títulos antiguos a nuevos
TITLE_MAPPING = {
     # Machine Learning / Data
    "Machine Learning Engineer": "ML Engineer",
    "ML Engineer": "ML Engineer",
    "Machine-Learning Engineer": "ML Engineer",
    "Data Scientist & AI": "Data Scientist",
    "Junior Data Scientist & AI": "Data Scientist",
    "Junior Data Scientist": "Data Scientist",
    "Senior Data Scientist": "Data Scientist",
    "Data Science Engineer": "Data Scientist",
    "Data Science": "Data Scientist",

    # Data general / BI
   "Senior Data Analyst": "Data Analyst",
    "Junior Data Analyst": "Data Analyst",
    "Business Intelligence Analyst": "BI Analyst",
    "Analytics Analyst": "Data Analyst",
    "Insights Analyst": "Data Analyst",
    "Experimentation Analyst": "Data Analyst",
    "Data Platform Engineer": "Data Engineer",
    "Data Architect": "Data Engineer",

    # QA / Testing
    "QA Manual": "QA / Test Engineer",
    "QA Manual Tester": "QA / Test Engineer",
    "Manual QA": "QA / Test Engineer",
    "QA Engineer": "QA / Test Engineer",
    "QA": "QA / Test Engineer",
    "Quality Assurance Analyst": "QA / Test Engineer",
    "Quality Assurance Engineer": "QA / Test Engineer",
    "QA accesibilidad": "QA / Test Engineer",
    "Consultor/a de pruebas QA": "QA / Test Engineer",
    "Test Engineer": "Test Engineer",
    "Tester": "Test Engineer",
    "Documentation Specialist": "Quality Analyst",

    # Documentación (si no hay canonical específico, se envía a Other / Consultant)
    "Clinical Documentation Specialist": "Other",
    "Trial Master File Specialist": "Other",
    
    # Product
    "Product Analyst": "Product Analyst",
    "Payments Product Analyst": "Product Analyst",
    "Payment Product Analyst": "Product Analyst",
    "Associate Product Manager": "Product Analyst",
    "Product-Owner": "Product Owner",
    "Product Owner (PO)": "Product Owner",
    "Product Specialist": "Product Manager",
    "Product Ops": "Product Operations",
    "Head of Product": "Product Manager",
    "VP of Product": "Product Manager",
    "Product Lead": "Product Manager",

    # Engineering variants
    "Senior Software Engineer": "Software Engineer",
    "Principal Software Engineer": "Software Engineer",
    "Fullstack Developer": "Full Stack Developer",
    "Frontend Engineer": "Frontend Developer",
    "Backend Engineer": "Backend Developer",
    "DevOps Engineer": "DevOps / SRE",
    "SRE": "DevOps / SRE",
    "Site Reliability Engineer": "DevOps / SRE",
    "iOS Developer": "Mobile Developer",
    "Android Developer": "Mobile Developer",
    "Backend/Frontend Developer": "Full Stack Developer",
    "Software Developer": "Software Engineer",

    # Marketing & Growth variants
    "Growth Analyst": "Growth / Performance Analyst",
    "Performance Marketing Specialist": "Growth / Performance Analyst",
    "Content Marketing Specialist": "Digital Marketing Specialist",
    "SEO Specialist": "Digital Marketing Specialist",
    "SEM Specialist": "Digital Marketing Specialist",

    # Project & Business
    "PMO": "Project Manager",
    "PMO Junior": "Project Manager",
    "Scrum Master": "Project Manager",
    "Project Coordinator": "Project Manager",
    "Program Manager": "Project Manager",
    "Business Development Specialist": "Business Analyst",
    "Process Designer": "Process Analyst",
    "Process Manager": "Process Analyst",
    "Implementation Consultant": "Implementation / Onboarding Manager",
    "Implementation Manager": "Implementation / Onboarding Manager",
    "Onboarding Specialist": "Implementation / Onboarding Manager",

    # Operations & IT
    "Supply Chain Manager": "Operations Manager",
    "Operations Analyst": "Operations Manager",
    "Sysadmin": "System Administrator",
    "IT Support": "Technical Support Engineer",
    "Helpdesk": "Technical Support Engineer",

    # Compliance & Quality (concordando con tu schema)
    "Compliance Specialist": "Compliance / Regulatory Specialist",
    "Compliance Analyst": "Compliance / Regulatory Specialist",
    "Regulatory Affairs Specialist": "Compliance / Regulatory Specialist",
    "Quality Analyst": "Quality Analyst",
    "Auditor": "Auditor",
    "Risk Analyst": "Risk Analyst",

    # Sales & Customer Success
    "Customer Success Manager": "Customer Success",
    "Customer Success Specialist": "Customer Success",
    "CSM": "Customer Success",
    "Key Account Manager": "Account Manager",
    "Business Development Manager": "Sales Manager",
    "Commercial Manager": "Sales Manager",
    "Sales Rep": "Sales Representative",

    # Research & UX Research
    "Market Research Analyst": "Research Analyst",
    "UX Researcher": "User Researcher",

    # Finance -> conservador a Business Analyst (no tiene Financial Analyst en schema)
    "Investment Banking Analyst": "Business Analyst",
    "Finanzas Júnior": "Business Analyst",
    "Financial Analyst": "Business Analyst",
    "Finance Analyst": "Business Analyst",

    # Admin & Others
    "Personal Assistant": "Assistant",
    "Executive Assistant": "Assistant",
    "Office Assistant": "Assistant",
    "Administrative Assistant": "Assistant",
    "Advisor / Consultant": "Consultant",
    "Specialist": "Consultant"
}

def ensure_directory(directory):
    """Asegura que el directorio existe"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def archive_file(file_path):
    """Archiva un archivo con timestamp en csv/src/archive"""
    ensure_directory(ARCHIVE_DIR)
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{name}_{timestamp}{ext}"
    archive_path = os.path.join(ARCHIVE_DIR, archive_name)
    shutil.copy2(file_path, archive_path)
    return archive_path

def normalize_titles(df):
    """Normaliza los títulos en el DataFrame con reglas de mayor precisión"""
    import re

    def canonicalize_by_prefix(original_title: str, current_short: str) -> str:
        text = (original_title or "").strip().lower()
        # Reglas de prefijo con alta prioridad
        prefix_rules = [
            (r'^business\s+analyst\b', 'Business Analyst'),
            (r'^product\s+analyst\b', 'Product Analyst'),
            (r'^(bi|business\s+intelligence)\s+analyst\b', 'BI Analyst'),
            (r'^data\s+analyst\b', 'Data Analyst'),
            (r'^analytics\s+engineer\b', 'Analytics Engineer'),
        ]
        for pattern, canon in prefix_rules:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return canon
        return current_short

    def map_title(row):
        original = str(row.get('Job title (original)', '') or '')
        current_short = str(row.get('Job title (short)', '') or '')

        # 1) Prefijo manda
        prefixed = canonicalize_by_prefix(original, current_short)
        if prefixed != current_short:
            return prefixed

        # 2) Mapeo específico por inclusión (backfill)
        original_lower = original.lower()
        for k, v in TITLE_MAPPING.items():
            if k.lower() in original_lower:
                return v

        # 3) Sin cambios
        return current_short

    df['Job title (short)'] = df.apply(map_title, axis=1)
    return df

def process_file(file_path):
    """Procesa un archivo CSV"""
    print(f"Procesando: {file_path}")
    # Leer CSV
    df = pd.read_csv(file_path)
    original_count = len(df)
    # Guardar copia para comparar
    df_before = df.copy(deep=True)
    # Normalizar títulos
    df = normalize_titles(df)
    final_count = len(df)
    if final_count != original_count:
        raise ValueError(f"¡Error! Registros no coinciden: {original_count} -> {final_count}")
    # Si no hay cambios, no archivar ni sobrescribir
    if df.equals(df_before):
        print("Sin cambios, no se archiva ni reemplaza.")
        return {'original': original_count, 'final': final_count, 'archived': None, 'updated': False}
    # Archivar versión actual
    archive_path = archive_file(file_path)
    print(f"Archivo respaldado en: {archive_path}")
    # Guardar versión normalizada en la ubicación original
    df.to_csv(file_path, index=False)
    print(f"Archivo actualizado: {file_path}")
    return {'original': original_count, 'final': final_count, 'archived': archive_path, 'updated': True}

def main():
    """Función principal"""
    print("Iniciando normalización de títulos...")
    # Migrar archivos de carpeta antigua si existiera
    old_archive = os.path.join(PROCESSED_DIR, 'archive')
    if os.path.isdir(old_archive):
        ensure_directory(ARCHIVE_DIR)
        for fn in os.listdir(old_archive):
            src = os.path.join(old_archive, fn)
            dst = os.path.join(ARCHIVE_DIR, fn)
            try:
                shutil.move(src, dst)
            except Exception:
                pass
        try:
            os.rmdir(old_archive)
        except Exception:
            pass
    results = []
    for filename in os.listdir(PROCESSED_DIR):
        file_path = os.path.join(PROCESSED_DIR, filename)
        # Omitir subcarpeta archive y archivos que no sean CSV
        if not filename.endswith('.csv') or os.path.isdir(file_path) or filename == 'archive':
            continue
        try:
            result = process_file(file_path)
            results.append({'file': filename, **result})
        except Exception as e:
            print(f"Error procesando {filename}: {str(e)}")
    # Imprimir resumen
    print("\nResumen de procesamiento:")
    print("-" * 50)
    for result in results:
        print(f"Archivo: {result['file']}")
        print(f"Registros: {result['original']} -> {result['final']}")
        if result.get('updated'):
            print(f"Respaldo: {os.path.basename(result['archived'])}")
        else:
            print("Sin cambios, no se archivó.")
        print("-" * 50)

if __name__ == "__main__":
    main()

```

- Refuerzo aplicado: añadí normalización por prefijo de alta prioridad para evitar confusiones típicas.
  - Reglas clave: si el título original empieza con “Business Analyst/ Product Analyst/ BI Analyst/ Data Analyst/ Analytics Engineer”, se fija ese “Job title (short)” canónico.
  - Archivo editado: `csv_engine/utils/title_normalizer.py`
```python
# carpeta de archivo única
ARCHIVE_DIR = os.path.join(REPO_ROOT, "csv", "src", "archive")

# reglas por prefijo (alta prioridad)
prefix_rules = [
    (r'^business\s+analyst\b', 'Business Analyst'),
    (r'^product\s+analyst\b', 'Product Analyst'),
    (r'^(bi|business\s+intelligence)\s+analyst\b', 'BI Analyst'),
    (r'^data\s+analyst\b', 'Data Analyst'),
    (r'^analytics\s+engineer\b', 'Analytics Engineer'),
]
```

- Normalización ejecutada sobre batches en `csv/src/csv_processed`:
  - Sin cambios: `20250818_133026_DataPM_result_batch_1..5.csv` y `20250818_135343_DataPM_result_batch_4.csv`.
  - Actualizados (con respaldo creado): `20250818_135343_DataPM_result_batch_1.csv`, `_batch_2.csv`, `_batch_3.csv`, `_batch_5.csv`.
  - Respaldos en `csv/src/archive` con timestamp.

- Carpeta de archivo unificada:
  - Ahora sólo se usa `csv/src/archive`.
  - Si existía `csv/src/csv_processed/archive`, se migraron sus contenidos a `csv/src/archive` y se intentó eliminar.

- ¿Seguimos con otro lote o quieres revisar rápidamente los cambios en los CSV actualizados?

```python
# carpeta de archivo única
ARCHIVE_DIR = os.path.join(REPO_ROOT, "csv", "src", "archive")

# reglas por prefijo (alta prioridad)
prefix_rules = [
    (r'^business\s+analyst\b', 'Business Analyst'),
    (r'^product\s+analyst\b', 'Product Analyst'),
    (r'^(bi|business\s+intelligence)\s+analyst\b', 'BI Analyst'),
    (r'^data\s+analyst\b', 'Data Analyst'),
    (r'^analytics\s+engineer\b', 'Analytics Engineer'),
]
```

