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
KEYWORDS = "yuno"
LOCATION = "Spain"
REMOTE_FILTER = "2"   # 1=On-site, 2=Remote, 3=Hybrid (On-site + Hybrid)
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

# Initialize global variables
results = []
processed_count = 0

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

def main():
    """Función principal del scraper"""
    global results, processed_count
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options)

    # Ocultar que es automatizado
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        # --- 1. LOGIN LINKEDIN CON VERIFICACIÓN ---
        print("Iniciando login en LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        random_delay(2, 4)

        # Buscar campos de login
        email_field = safe_find_element(driver, By.ID, "username")
        password_field = safe_find_element(driver, By.ID, "password")

        if not email_field or not password_field:
            print("❌ Error: No se encontraron los campos de login")
            return

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
            return

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
            return

        print(f"✅ Encontrados {len(job_cards)} empleos para procesar")

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
                        "div.job-details-jobs-unified-top-card__primary-description-container",
                        "div.artdeco-entity-lockup__caption ul.job-card-container__metadata-wrapper li span[dir='ltr']",
                        "div.artdeco-entity-lockup__caption span[dir='ltr']"
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
                    # Quitar notas entre paréntesis como (Remote)
                    location = clean_text_for_csv(location)
                    if '(' in location and ')' in location:
                        try:
                            # remove parenthetical notes
                            import re as _re
                            location = _re.sub(r"\([^\)]*\)", "", location).strip()
                        except Exception:
                            pass
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

    finally:
        driver.quit()

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

if __name__ == "__main__":
    main()