from selenium import webdriver
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
import time
import csv
import random
import re

# --- CONFIGURACIÓN DE USUARIO ---
EMAIL = "pjherrera23@gmail.com"
PASSWORD = "SarayGaby.2006"
KEYWORDS = "product"
LOCATION = "Spain"
REMOTE_FILTER = "2"   # 2 = Remote
PAGES_TO_SCRAPE = 1   # Solo primera página por ahora

# --- CONFIGURACIÓN ANTI-DETECCIÓN ---
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

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

# Llenar formulario
email_field.send_keys(EMAIL)
random_delay(0.5, 1)
password_field.send_keys(PASSWORD)
random_delay(0.5, 1)
password_field.send_keys(Keys.RETURN)

# Verificar login exitoso
print("Verificando login...")
if not verify_login_success(driver):
    print("❌ Error: Login fallido. Verifica credenciales o captcha")
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

# --- 3. SCRAPING DETALLADO CON MANEJO ROBUSTO ---
results = []
processed_count = 0

for idx, card in enumerate(job_cards, start=1):
    try:
        print(f"Procesando empleo {idx}/{len(job_cards)}...")
        
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
            print(f"⚠️  Saltando empleo {idx}: No se cargaron los detalles")
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
            print(f"⚠️  Saltando empleo {idx}: Datos insuficientes")
            continue

        # Limpiar datos para CSV
        title = clean_text_for_csv(title)
        company = clean_text_for_csv(company)
        location = clean_text_for_csv(location)
        description = clean_text_for_csv(description)

        print(f"✅ [{idx}] {title[:50]}... | {company} | {location}")
        
        results.append({
            "title": title,
            "company": company,
            "location": location,
            "description": description
        })
        
        processed_count += 1
        random_delay(1, 3)  # Pausa entre empleos

    except Exception as e:
        print(f"❌ Error procesando empleo #{idx}: {str(e)}")
        continue

# --- 4. GUARDAR EN CSV CON VALIDACIÓN ---
if results:
    filename = "linkedin_jobs_detailed.csv"
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "company", "location", "description"])
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\n✅ Extracción completada: {processed_count} ofertas guardadas en {filename}")
    except Exception as e:
        print(f"❌ Error guardando CSV: {str(e)}")
else:
    print("❌ No se extrajo ningún empleo válido")

driver.quit()