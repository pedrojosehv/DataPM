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
            
            print(f"🎉 Procesamiento completado exitosamente!")
            print(f"📁 Archivo de salida: {output_file}")
            
        except Exception as e:
            print(f"❌ Error durante el procesamiento: {e}")
            sys.exit(1)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="DataPM Processor - Análisis de descripciones de trabajo")
    parser.add_argument("input_file", help="Archivo CSV de entrada")
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
    
    # Crear y ejecutar procesador
    processor = DataPMProcessor(
        llm_type=args.llm,
        api_key=args.api_key,
        ollama_url=args.ollama_url
    )
    
    processor.run(args.input_file, args.output)


if __name__ == "__main__":
    main()
