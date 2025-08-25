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
from difflib import SequenceMatcher
import pandas as pd
import re

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

# Import API Key Manager
try:
    from api_key_manager import get_datapm_api_key, mark_datapm_api_error
    API_KEY_MANAGER_AVAILABLE = True
except ImportError:
    API_KEY_MANAGER_AVAILABLE = False
    print("⚠️  API Key Manager no disponible, usando método tradicional")


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

# Canonicals/config centralizado
try:
    from utils import config  # type: ignore
except Exception:
    config = None


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
            # Cargar pool de keys con prioridad: arg, GEMINI_API_KEYS, GEMINI_API_KEY, config
            self.gemini_keys: List[str] = self._load_gemini_keys(api_key)
            if not self.gemini_keys:
                raise ValueError("API key requerida para Gemini (usa --api-key o GEMINI_API_KEY/GEMINI_API_KEYS)")
            self.current_key_idx = 0
            self._configure_gemini_for_key(self.gemini_keys[self.current_key_idx])
        
        # Schema de normalización (CSV final)
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
        if config is not None and hasattr(config, "NORMALIZATION_SCHEMA"):
            try:
                nv = config.NORMALIZATION_SCHEMA
                for key in ["job_title_short","skills","software","degrees","job_schedule_type","seniority","experience_years"]:
                    if key in nv:
                        self.normalized_values[key] = nv[key]
            except Exception:
                pass
    
    def create_system_prompt(self) -> str:
        """Crea el prompt del sistema igual que en Make.com"""
        return f"""You are a strict data extractor and standardizer. You MUST return ONLY a valid JSON object and nothing else.
The JSON must follow this schema:

job_title_original (string)

job_title_short (string, normalized to one of these values: {self.normalized_values['job_title_short']})

experience_years (string, normalized to one of these formats: "0-3" for less than 3 years, "3-5" for ranges, "5+" for 5 or more years)

job_schedule_type (string, normalized to one of these values: {self.normalized_values['job_schedule_type']})

seniority (string, normalized to one of these values: {self.normalized_values['seniority']})

city (string, proper case, e.g., "New York", "Madrid"; use "Unknown" if not found.)

state (string, state or province for the given country if determinable; use "Unknown" only if not found.)

country (string, proper case, e.g., "United States", "Spain", "Mexico", "United Kingdom", "Germany", "France", "Panamá", "Venezuela", "European Union", "Unknown")

degrees (array of strings, normalized to one of these values: {self.normalized_values['degrees']})

skills (array of strings, normalized to a fixed set of values like: {self.normalized_values['skills']})

software (array of strings, normalized to a fixed set of values like: {self.normalized_values['software']})

IMPORTANT: For software detection, carefully scan the entire job description for:
- Project management tools: Jira, Confluence, Trello, Asana, Monday.com
- Design tools: Figma, Sketch, Adobe XD, Adobe Creative Suite
- Analytics tools: Power BI, Tableau, Google Analytics, Looker, Mixpanel
- Development tools: GitHub, GitLab, AWS, Azure, GCP
- Business tools: Salesforce, SAP, HubSpot, Microsoft Office
- Testing tools: Selenium, Cypress, JUnit, TestRail
- Database tools: SQL, MongoDB, PostgreSQL, Oracle
- Programming languages: Python, R, Java, JavaScript, C++, C
- Cloud platforms: AWS, Azure, GCP, Vercel
- Other mentioned technologies, tools, or platforms

Extract ALL software, tools, platforms, and technologies mentioned in the job description, even if they appear only once.

company_name (string)

If you cannot determine a value, use "Unknown" for strings and blank space for arrays, data slot must be empty. No extra text, no markdown, no explanation."""

    def create_user_prompt(self, description: str) -> str:
        """Crea el prompt del usuario"""
        # Sanea posibles comillas problemáticas en descripción
        safe = (description or "").replace("\\", " ").replace("\n", " ")
        return f"""INPUT: {{"text":"{safe}"}}
TASK: Analyze INPUT.text and return the JSON according to the schema in the system instructions."""

    # Utilidades de robustez
    def _strip_fences(self, s: str) -> str:
        t = (s or "").strip()
        if t.startswith("```json"):
            t = t[7:]
        if t.startswith("```"):
            t = t[3:]
        if t.endswith("```"):
            t = t[:-3]
        return t.strip()

    def _safe_json_loads(self, s: str):
        try:
            return json.loads(s)
        except Exception:
            try:
                start, end = s.find('{'), s.rfind('}')
                if start != -1 and end != -1 and end > start:
                    return json.loads(s[start:end+1])
            except Exception:
                return None
        return None

    def _enforce_canonicals(self, result: Dict[str, Any]) -> Dict[str, Any]:
        def filter_list(values: List[str], canon: List[str]) -> List[str]:
            canon_lower = {c.lower(): c for c in canon}
            out: List[str] = []
            for v in values or []:
                key = (v or "").strip().lower()
                if key in canon_lower:
                    out.append(canon_lower[key])
            return out
        # enums
        if result.get('job_title_short') not in self.normalized_values['job_title_short']:
            result['job_title_short'] = 'Unknown'
        if result.get('job_schedule_type') not in self.normalized_values['job_schedule_type']:
            result['job_schedule_type'] = 'Unknown'
        if result.get('seniority') not in self.normalized_values['seniority']:
            result['seniority'] = 'Unknown'
        if result.get('experience_years') not in self.normalized_values['experience_years']:
            result['experience_years'] = 'Unknown'
        # lists
        result['skills'] = filter_list(result.get('skills', []), self.normalized_values['skills'])
        result['software'] = filter_list(result.get('software', []), self.normalized_values['software'])
        return result

    # ---------------------- Gemini API key rotation ----------------------
    def _load_gemini_keys(self, api_key: Optional[str]) -> List[str]:
        # Use API Key Manager if available
        if API_KEY_MANAGER_AVAILABLE:
            try:
                # Get all available keys from manager
                from api_key_manager import datapm_api_manager
                if datapm_api_manager.keys:
                    print(f"✅ DataPM: Loaded {len(datapm_api_manager.keys)} API keys from manager")
                    return datapm_api_manager.keys
            except Exception as e:
                print(f"⚠️ DataPM: Error loading keys from manager: {e}")
        
        # Fallback to traditional method
        keys: List[str] = []
        # 1) CLI arg takes precedence if provided
        if api_key:
            keys.append(api_key.strip())
        # 2) Environment variable GEMINI_API_KEYS (comma-separated)
        try:
            env_keys = os.getenv("GEMINI_API_KEYS", "")
            if env_keys:
                keys.extend([k.strip() for k in env_keys.split(",") if k.strip()])
        except Exception:
            pass
        # 3) Single env GEMINI_API_KEY
        try:
            single = os.getenv("GEMINI_API_KEY", "")
            if single:
                keys.append(single.strip())
        except Exception:
            pass
        # 4) Config list if available
        try:
            if config and isinstance(config.LLM_CONFIG.get("gemini", {}).get("api_keys", None), list):
                conf_list = [k for k in config.LLM_CONFIG["gemini"]["api_keys"] if isinstance(k, str) and k.strip()]
                keys.extend(conf_list)
        except Exception:
            pass
        # De-duplicate while preserving order
        seen = set()
        uniq: List[str] = []
        for k in keys:
            if k and k not in seen:
                seen.add(k)
                uniq.append(k)
        return uniq

    def _configure_gemini_for_key(self, key: str):
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Google Gemini no está disponible")
        genai.configure(api_key=key)
        model_name = 'gemini-2.0-flash-exp'
        try:
            if config and isinstance(config.LLM_CONFIG.get("gemini", {}).get("model", None), str):
                model_name = config.LLM_CONFIG["gemini"]["model"]
        except Exception:
            pass
        self.model = genai.GenerativeModel(model_name)

    def _rotate_gemini_key(self):
        if not hasattr(self, 'gemini_keys') or not self.gemini_keys:
            return
        self.current_key_idx = (self.current_key_idx + 1) % len(self.gemini_keys)
        next_key = self.gemini_keys[self.current_key_idx]
        self._configure_gemini_for_key(next_key)
    # --------------------------------------------------------------------

    # ---------------------- Geocoding (Nominatim) ----------------------
    def _init_geo_cache(self):
        if not hasattr(self, '_geo_cache'):
            self._geo_cache = {}
    
    def _geo_cache_get(self, key: str):
        self._init_geo_cache()
        return self._geo_cache.get(key)
    
    def _geo_cache_set(self, key: str, value: Dict[str, str]):
        self._init_geo_cache()
        self._geo_cache[key] = value
    
    def _geocode_state_country(self, city: str, country: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Query Nominatim to resolve state/province and country from city (+ optional country).
        Returns dict with keys city,state,country on success, or None on failure.
        Respects rate-limits with minimal backoff.
        """
        if not REQUESTS_AVAILABLE:
            return None
        q_city = (city or '').strip()
        q_country = (country or '').strip() if country else ''
        if not q_city:
            return None
        # Cache
        cache_key = f"{q_city.lower()}|{q_country.lower()}"
        cached = self._geo_cache_get(cache_key)
        if cached:
            return cached
        try:
            base = "https://nominatim.openstreetmap.org/search"
            params = {
                'city': q_city,
                'format': 'json',
                'addressdetails': 1,
                'limit': 1
            }
            if q_country:
                params['country'] = q_country
            headers = {
                'User-Agent': 'DataPM/1.0 (contact: admin@datapm.local)'
            }
            resp = requests.get(base, params=params, headers=headers, timeout=10)
            if resp.status_code == 429:
                time.sleep(1.5)
                resp = requests.get(base, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and data:
                addr = (data[0] or {}).get('address', {})
                found_city = addr.get('city') or addr.get('town') or addr.get('village') or q_city
                state = addr.get('state') or addr.get('region') or addr.get('state_district') or 'Unknown'
                found_country = addr.get('country') or q_country or 'Unknown'
                result = {'city': found_city, 'state': state, 'country': found_country}
                self._geo_cache_set(cache_key, result)
                return result
        except Exception:
            return None
        return None
    # ------------------------------------------------------------------

    def call_gemini(self, description: str) -> Dict[str, Any]:
        """Llama a Google Gemini para procesar la descripción"""
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Google Gemini no está disponible")
        
        max_retries = 5
        retry_count = 0
        keys_len = len(getattr(self, 'gemini_keys', [])) if self.llm_type == 'gemini' else 1
         
        while retry_count < max_retries:
            try:
                system_prompt = self.create_system_prompt()
                user_prompt = self.create_user_prompt(description)
                
                response = self.model.generate_content([
                    {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}
                ])
                
                # Extraer JSON de la respuesta con tolerancia
                response_text = self._strip_fences(response.text)
                parsed = self._safe_json_loads(response_text)
                if not isinstance(parsed, dict):
                    raise ValueError("Respuesta no parseable a JSON")
                # Defaults mínimos
                for k in ["job_title_original","job_title_short","experience_years","job_schedule_type","seniority","city","state","country","degrees","skills","software","company_name"]:
                    parsed.setdefault(k, [] if k in {"degrees","skills","software"} else "Unknown")
                parsed = self._enforce_canonicals(parsed)
                return parsed
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    # Rotar de inmediato la key y reintentar con pausa corta
                    retry_count += 1
                    
                    # Use API Key Manager if available
                    if API_KEY_MANAGER_AVAILABLE:
                        try:
                            # Mark current key as having error and get next key
                            current_key = getattr(self, 'gemini_keys', [None])[getattr(self, 'current_key_idx', 0)] if hasattr(self, 'gemini_keys') else None
                            if current_key:
                                mark_datapm_api_error(current_key, "rate_limit")
                            
                            # Get next key from manager
                            next_key = get_datapm_api_key("round_robin")
                            if next_key:
                                self._configure_gemini_for_key(next_key)
                                print(f"⏳ Rate limit. Rotando API key con manager (intento {retry_count}/{max_retries})...")
                                time.sleep(1.0)
                                continue
                        except Exception as e:
                            print(f"⚠️ Error con API Key Manager: {e}")
                    
                    # Fallback to traditional rotation
                    if getattr(self, 'gemini_keys', None):
                        self._rotate_gemini_key()
                        print(f"⏳ Rate limit. Rotando API key (intento {retry_count}/{max_retries})...")
                        time.sleep(1.0)
                        continue
                    else:
                        # Sin pool de keys, esperar breve y reintentar
                        time.sleep(2.0)
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
            
            response_text = self._strip_fences(response.json()["message"]["content"])
            parsed = self._safe_json_loads(response_text)
            if not isinstance(parsed, dict):
                raise ValueError("Respuesta no parseable a JSON")
            for k in ["job_title_original","job_title_short","experience_years","job_schedule_type","seniority","city","state","country","degrees","skills","software","company_name"]:
                parsed.setdefault(k, [] if k in {"degrees","skills","software"} else "Unknown")
            parsed = self._enforce_canonicals(parsed)
            return parsed
            
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
                # Fix location if missing by parsing raw location string from scrapping
                city_val = llm_result.get('city', 'Unknown')
                state_val = llm_result.get('state', 'Unknown')
                country_val = llm_result.get('country', 'Unknown')
                if (location and isinstance(location, str)) and ('Unknown' in [city_val, state_val, country_val]):
                    cty, st, ctry = self._parse_location(location)
                    if city_val == 'Unknown' and cty:
                        city_val = cty
                    if state_val == 'Unknown' and st:
                        state_val = st
                    if country_val == 'Unknown' and ctry:
                        country_val = ctry
                # Detect region tokens early
                region = self._extract_region_token(city_val, state_val, country_val, location)
                if region:
                    country_val = region
                    city_val = 'Unknown'
                    state_val = 'Unknown'
                else:
                    # If still Unknowns and we have city, attempt geocoding via Nominatim
                    if city_val != 'Unknown' and ('Unknown' in [state_val, country_val]):
                        geo = self._geocode_state_country(city_val, country_val if country_val != 'Unknown' else None)
                        if isinstance(geo, dict):
                            if state_val == 'Unknown' and geo.get('state'):
                                state_val = geo['state']
                            if country_val == 'Unknown' and geo.get('country'):
                                country_val = geo['country']
                    # Deterministic fallback by city+country for selected countries
                    if state_val == 'Unknown' and city_val != 'Unknown' and country_val != 'Unknown':
                        inferred = self._infer_state_from_city_country(city_val, country_val)
                        if inferred:
                            state_val = inferred
                    # LLM-assisted completion per rules
                    loc_completed = self._complete_location_with_llm(description, city_val, state_val, country_val, raw_location=location)
                    city_val = loc_completed['city']
                    state_val = loc_completed['state']
                    country_val = loc_completed['country']

                # Ensure software names not in Skills
                skills_list = llm_result.get('skills', [])
                software_list = llm_result.get('software', [])
                canon_software_lower = {s.lower() for s in self.normalized_values.get('software', [])}
                clean_skills = []
                moved_sw = []
                for s in skills_list:
                    if (s or '').lower() in canon_software_lower:
                        moved_sw.append(s)
                    else:
                        clean_skills.append(s)
                # Blacklist specific skill label
                clean_skills = [s for s in clean_skills if s.strip().lower() != 'product management']
                software_list = software_list + moved_sw

                # Deduplicate tokens preserving order
                def dedup_list(seq: List[str]) -> List[str]:
                    seen = set()
                    out: List[str] = []
                    for v in seq:
                        k = (v or '').strip().lower()
                        if k and k not in seen:
                            seen.add(k)
                            out.append(v)
                    return out

                clean_skills = dedup_list(clean_skills)
                software_list = dedup_list(software_list)
                degrees_list = dedup_list(llm_result.get('degrees', []))

                # Final sanitation for region tokens
                city_val, state_val, country_val = self._purge_region_tokens(city_val, state_val, country_val)

                processed_row = {
                    'Job title (original)': title,
                    'Job title (short)': llm_result.get('job_title_short', 'Unknown'),
                    'Company': llm_result.get('company_name', company),
                    'Country': country_val,
                    'State': state_val,
                    'City': city_val,
                    'Schedule type': llm_result.get('job_schedule_type', 'Unknown'),
                    'Experience years': llm_result.get('experience_years', 'Unknown'),
                    'Seniority': llm_result.get('seniority', 'Unknown'),
                    'Skills': '; '.join(clean_skills),
                    'Degrees': '; '.join(degrees_list),
                    'Software': '; '.join(software_list)
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

    def run(self, input_file: str, output_file: Optional[str] = None, max_rows: Optional[int] = None):
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
            if max_rows:
                input_data = input_data[:max_rows]
            
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

    def _parse_location(self, location_text: str):
        text = (location_text or '').replace('(Remote)', '').strip()
        parts = [p.strip() for p in text.split(',') if p.strip()]
        country = 'Unknown'
        state = 'Unknown'
        city = 'Unknown'
        try:
            countries = set([c.lower() for c in config.LOCATION_CONFIG.get('countries', [])]) if config else set()
            us_states = config.LOCATION_CONFIG.get('us_states', {}) if config else {}
            ca_provinces = config.LOCATION_CONFIG.get('ca_provinces', {}) if config else {}
        except Exception:
            countries, us_states, ca_provinces = set(), {}, {}
        if parts:
            # Assume last token is country if matches configured list
            last = parts[-1].lower()
            if countries and last in countries:
                country = parts[-1]
                if len(parts) >= 2:
                    state = parts[-2]
                if len(parts) >= 3:
                    city = parts[-3]
            else:
                # Fallback simple mapping City, Region, Country pattern
                if len(parts) >= 3:
                    city, state, country = parts[-3], parts[-2], parts[-1]
                elif len(parts) == 2:
                    city, country = parts[0], parts[1]
                elif len(parts) == 1:
                    city = parts[0]
        return city or 'Unknown', state or 'Unknown', country or 'Unknown'

    def _complete_location_with_llm(self, description: str, city: str, state: str, country: str, raw_location: Optional[str] = None) -> Dict[str, str]:
        """Use the configured LLM to fill missing location fields per rules:
        - If only country is present: keep Unknown for city/state (no deduction)
        - If country and city present but state Unknown: deduce state
        - If only city present: deduce country and state
        Returns dict with possibly updated city/state/country.
        """
        city = city or 'Unknown'
        state = state or 'Unknown'
        country = country or 'Unknown'
        # Rule 1: only country present -> do nothing
        only_country = (country != 'Unknown' and city == 'Unknown' and state == 'Unknown')
        if only_country:
            return {'city': city, 'state': state, 'country': country}
        # Determine need
        need_state = (country != 'Unknown' and city != 'Unknown' and state == 'Unknown')
        need_country_state = (city != 'Unknown' and country == 'Unknown')
        if not (need_state or need_country_state):
            return {'city': city, 'state': state, 'country': country}
        # Build compact prompt
        system_text = (
            "You normalize geographic locations. Return ONLY one single-line JSON with keys city,state,country. "
            "If you cannot determine a field with high confidence, output 'Unknown'."
        )
        hint = f"; raw={raw_location}" if raw_location else ""
        if need_state:
            user_text = (
                f"INPUT: city={city}; country={country}{hint}. TASK: Provide state/province (and echo city/country). "
                "Output JSON: {\"city\":...,\"state\":...,\"country\":...}"
            )
        else:
            user_text = (
                f"INPUT: city={city}{hint}. TASK: Provide state/province and country. "
                "Output JSON: {\"city\":...,\"state\":...,\"country\":...}"
            )
        try:
            raw = ''
            if self.llm_type == 'gemini' and GEMINI_AVAILABLE:
                resp = self.model.generate_content([
                    {"role": "user", "parts": [{"text": system_text + "\n\n" + user_text}]}
                ])
                raw = getattr(resp, 'text', '') or ''
            elif self.llm_type == 'ollama' and REQUESTS_AVAILABLE:
                payload = {
                    "model": "llama3.2:3b",
                    "messages": [
                        {"role": "system", "content": system_text},
                        {"role": "user", "content": user_text}
                    ],
                    "stream": False
                }
                r = requests.post(f"{self.ollama_url}/api/chat", json=payload, timeout=30)
                r.raise_for_status()
                raw = (r.json().get('message', {}) or {}).get('content', '')
            else:
                return {'city': city, 'state': state, 'country': country}
            cleaned = self._strip_fences(raw)
            parsed = self._safe_json_loads(cleaned)
            if isinstance(parsed, dict):
                new_city = str(parsed.get('city', city) or city)
                new_state = str(parsed.get('state', state) or state)
                new_country = str(parsed.get('country', country) or country)
                # Keep original known values; only fill Unknown
                if city == 'Unknown':
                    city = new_city
                if state == 'Unknown':
                    state = new_state
                if country == 'Unknown':
                    country = new_country
        except Exception:
            pass
        return {'city': city, 'state': state, 'country': country}

    def _infer_state_from_city_country(self, city: str, country: str) -> Optional[str]:
        """Deterministic mapping of major cities to regions for selected countries."""
        if not city or not country:
            return None
        ctry = country.strip().lower()
        c = city.strip().lower()
        es = {
            'madrid': 'Community of Madrid',
            'barcelona': 'Catalonia',
            'valencia': 'Valencian Community',
            'sevilla': 'Andalusia', 'seville': 'Andalusia',
            'malaga': 'Andalusia', 'málaga': 'Andalusia',
            'zaragoza': 'Aragon',
            'bilbao': 'Basque Country',
            'vigo': 'Galicia',
            'alicante': 'Valencian Community',
            'cordoba': 'Andalusia', 'córdoba': 'Andalusia',
        }
        it = {
            'milan': 'Lombardy', 'milano': 'Lombardy',
            'rome': 'Lazio', 'roma': 'Lazio',
            'naples': 'Campania', 'napoli': 'Campania',
            'turin': 'Piedmont', 'torino': 'Piedmont',
            'bologna': 'Emilia-Romagna',
            'florence': 'Tuscany', 'firenze': 'Tuscany',
            'venice': 'Veneto', 'venezia': 'Veneto',
            'genoa': 'Liguria', 'genova': 'Liguria',
        }
        hr = {
            'zagreb': 'City of Zagreb',
            'split': 'Split-Dalmatia County',
            'rijeka': 'Primorje-Gorski Kotar County',
            'zadar': 'Zadar County',
        }
        if ctry == 'spain':
            return es.get(c)
        if ctry == 'italy':
            return it.get(c)
        if ctry == 'croatia':
            return hr.get(c)
        return None

    def _is_region_country(self, country: Optional[str]) -> bool:
        if not country:
            return False
        c = country.strip().lower()
        region_tokens = {
            'emea', 'european union', 'eu', 'european economic area', 'eea',
            'apac', 'latam', 'middle east', 'north america', 'south america',
            'europe', 'asia', 'americas', 'european', 'economic area'
        }
        return c in region_tokens

    def _purge_region_tokens(self, city: Optional[str], state: Optional[str], country: Optional[str]):
        c_city = (city or '').strip()
        c_state = (state or '').strip()
        c_country = (country or '').strip()
        # If country is a region, force city/state Unknown
        if self._is_region_country(c_country):
            return 'Unknown', 'Unknown', c_country
        # Drop region tokens in state/city
        if self._is_region_country(c_state):
            c_state = 'Unknown'
        if self._is_region_country(c_city):
            c_city = 'Unknown'
        return c_city or 'Unknown', c_state or 'Unknown', c_country or 'Unknown'

    def _extract_region_token(self, city: Optional[str], state: Optional[str], country: Optional[str], raw_location: Optional[str]) -> Optional[str]:
        candidates = [country or '', state or '', city or '', raw_location or '']
        for s in candidates:
            if not s:
                continue
            text = s.strip()
            # Check each token split by separators as well as full string
            tokens = [text] + [t.strip() for t in re.split(r"[,;/|-]", text) if t.strip()]
            for t in tokens:
                if self._is_region_country(t):
                    # Normalize some common variants
                    tl = t.strip()
                    norm = tl
                    low = tl.lower()
                    if low in {"eu"}:
                        norm = "European Union"
                    elif low in {"european economic area", "eea"}:
                        norm = "European Economic Area"
                    elif low == "emea":
                        norm = "EMEA"
                    elif low == "apac":
                        norm = "APAC"
                    elif low == "latam":
                        norm = "LATAM"
                    elif low == "europe":
                        norm = "Europe"
                    elif low == "asia":
                        norm = "Asia"
                    elif low == "americas":
                        norm = "Americas"
                    return norm
        return None


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
    parser.add_argument("--max-rows", type=int, default=None, help="Límite de filas a procesar (p.ej., 20)")
    
    args = parser.parse_args()
    
    # Validaciones - Check for API keys in environment variables first
    if args.llm == "gemini":
        # Check if we have API keys from environment or config
        has_env_keys = bool(os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY"))
        has_config_keys = False
        try:
            if config and isinstance(config.LLM_CONFIG.get("gemini", {}).get("api_keys", None), list):
                has_config_keys = bool(config.LLM_CONFIG["gemini"]["api_keys"])
        except Exception:
            pass
        
        # Check if API Key Manager has keys
        has_manager_keys = False
        if API_KEY_MANAGER_AVAILABLE:
            try:
                from api_key_manager import datapm_api_manager
                has_manager_keys = bool(datapm_api_manager.keys)
            except Exception:
                pass
        
        if not args.api_key and not has_env_keys and not has_config_keys and not has_manager_keys:
            print("❌ Error: --api-key es requerido para Gemini")
            print("💡 Obtén tu API key en: https://makersuite.google.com/app/apikey")
            print("💡 O usa variables de entorno: GEMINI_API_KEY o GEMINI_API_KEYS")
            print("💡 O asegúrate de que el API Key Manager tenga keys disponibles")
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
    
    processor.run(resolved_input, args.output, args.max_rows)


if __name__ == "__main__":
    main()
