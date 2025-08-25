#!/usr/bin/env python3
"""
DataPM Processor - Versión Ollama
Replica la automatización de Make.com para análisis de trabajos usando Ollama
Procesa descripciones de trabajo con LLM local (Ollama) y genera CSV estructurado
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
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Requests no disponible. Instala con: pip install requests")


DEEPSEEK_MODEL_DEFAULT = "deepseek-coder:6.7b"

class DataPMProcessorOllama:
    """Procesador principal para análisis de descripciones de trabajo usando Ollama"""
    
    def __init__(self, model: str = "llama3.2:3b", ollama_url: str = "http://localhost:11434"):
        """
        Inicializa el procesador con Ollama
        
        Args:
            model: Modelo de Ollama a usar (default: llama3.2:3b)
            ollama_url: URL del servidor Ollama
        """
        self.model = model
        self.ollama_url = ollama_url
        
        # Verificar que Ollama esté disponible
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("Requests no está disponible. Instala con: pip install requests")
        
        # Verificar conexión con Ollama
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
            print(f"✅ Conexión exitosa con Ollama en {ollama_url}")
        except Exception as e:
            print(f"❌ Error conectando con Ollama: {e}")
            print("💡 Asegúrate de que Ollama esté instalado y ejecutándose")
            print("📖 Instrucciones: https://ollama.ai/download")
            raise
        
        # Schema de normalización expandido (igual que en la versión Gemini)
        self.normalized_values = {
            "job_title_short": [
                # Product Management
                "Product Manager", "Product Owner", "Product Lead", "Product Director", 
                "VP of Product", "Head of Product", "Product Specialist", "Product Coordinator", 
                "Product Analyst", "Product Associate",
                
                # Data Roles
                "Data Analyst", "Data Scientist", "Data Engineer", "Data Architect", 
                "Data Manager", "Data Lead", "Data Specialist", "Business Intelligence Analyst", 
                "BI Analyst", "Analytics Manager", "Machine Learning Engineer", "ML Engineer", 
                "AI Engineer", "AI Specialist",
                
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

    def call_ollama(self, description: str) -> Dict[str, Any]:
        """Llama a Ollama para procesar la descripción"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                system_prompt = self.create_system_prompt()
                user_prompt = self.create_user_prompt(description)
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Baja temperatura para respuestas más consistentes
                        "top_p": 0.9,
                        "top_k": 40
                    }
                }
                
                response = requests.post(f"{self.ollama_url}/api/chat", json=payload, timeout=120)
                response.raise_for_status()
                
                response_text = response.json()["message"]["content"].strip()
                
                # Extraer JSON de la respuesta
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                # Intentar parsear JSON con manejo de errores mejorado
                try:
                    return json.loads(response_text.strip())
                except json.JSONDecodeError as json_error:
                    print(f"⚠️  Error parsing JSON: {json_error}")
                    print(f"📄 Respuesta recibida: {response_text[:200]}...")
                    # Si no es JSON válido, intentar extraer información básica
                    return self.extract_basic_info(response_text)
                
            except requests.exceptions.Timeout:
                retry_count += 1
                print(f"⏰ Timeout con Ollama (intento {retry_count}/{max_retries})")
                
                if retry_count < max_retries:
                    wait_time = retry_count * 5  # Espera progresiva: 5s, 10s, 15s
                    print(f"⏳ Reintentando en {wait_time} segundos...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Se agotaron los reintentos por timeout")
                    return self.get_default_response()
            except Exception as e:
                retry_count += 1
                print(f"❌ Error con Ollama (intento {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    print(f"⏳ Reintentando en 2 segundos...")
                    time.sleep(2)
                    continue
                else:
                    return self.get_default_response()
        
        return self.get_default_response()

    def extract_basic_info(self, response_text: str) -> Dict[str, Any]:
        """Extrae información básica de una respuesta no-JSON válida"""
        result = self.get_default_response()
        
        # Intentar extraer información básica usando palabras clave
        text_lower = response_text.lower()
        
        # Buscar job titles comunes
        job_titles = ["product manager", "data analyst", "designer", "developer", "engineer"]
        for title in job_titles:
            if title in text_lower:
                result["job_title_short"] = title.title()
                break
        
        # Buscar seniority
        if "senior" in text_lower:
            result["seniority"] = "Senior"
        elif "junior" in text_lower:
            result["seniority"] = "Junior"
        elif "mid" in text_lower:
            result["seniority"] = "Mid"
        
        # Buscar experiencia
        if "0-3" in response_text or "entry" in text_lower:
            result["experience_years"] = "0-3"
        elif "3-5" in response_text:
            result["experience_years"] = "3-5"
        elif "5+" in response_text or "senior" in text_lower:
            result["experience_years"] = "5+"
        
        return result

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
        """Procesa una descripción usando Ollama"""
        print(f"🤖 Procesando descripción con OLLAMA ({self.model})...")
        return self.call_ollama(description)

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
            
            # Pausa más corta para Ollama (sin rate limiting)
            if i < len(input_data):
                time.sleep(0.2)  # Reducir pausa para acelerar procesamiento
        
        print(f"✅ Procesamiento completado")
        return processed_data

    def write_csv(self, data: List[Dict[str, Any]], output_path: str):
        """Escribe el CSV de salida"""
        print(f"💾 Guardando CSV: {output_path}")
        
        if not data:
            print("⚠️  No hay datos para guardar")
            return
        
        # Si el archivo va a csv_processed pero no cumple el formato batch, redirigir a not_normalized
        processed_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../csv/src/csv_processed'))
        not_normalized_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../csv/src/not_normalized'))
        output_path_abs = os.path.abspath(output_path)
        if processed_dir in output_path_abs:
            filename = os.path.basename(output_path_abs)
            if not (filename.endswith('.csv') and '_batch_' in filename and filename.count('_') >= 4):
                # Redirigir a not_normalized
                print(f"⚠️  Archivo {filename} no cumple formato batch, moviendo a not_normalized")
                os.makedirs(not_normalized_dir, exist_ok=True)
                output_path_abs = os.path.join(not_normalized_dir, filename)
        else:
            os.makedirs(os.path.dirname(output_path_abs), exist_ok=True)
        
        with open(output_path_abs, 'w', newline='', encoding='utf-8') as file:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        print(f"✅ CSV guardado exitosamente en {output_path_abs}")

    def run(self, input_file: str, output_file: Optional[str] = None):
        """Ejecuta el procesamiento completo"""
        print("🚀 Iniciando DataPM Processor (Ollama)")
        print(f"📊 LLM: OLLAMA ({self.model})")
        print(f"🌐 URL: {self.ollama_url}")
        
        # Generar nombre de archivo de salida si no se proporciona
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"csv/archive/{timestamp}_DataPM_Ollama_result.csv"
        
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
    parser = argparse.ArgumentParser(
        description="""
        DataPM Processor (Ollama) - Análisis de descripciones de trabajo
        
        Soporta cualquier modelo Ollama compatible, incluyendo:
        - llama3.2:3b (por defecto)
        - deepseek-coder:6.7b (DeepSeek, recomendado para hardware limitado)
        - phi3, mistral, codellama, etc.
        
        Para usar DeepSeek, pase --model deepseek o --model deepseek-coder:6.7b
        """
    )
    parser.add_argument("input_file", help="Archivo CSV de entrada")
    parser.add_argument("--output", "-o", help="Archivo CSV de salida (opcional)")
    parser.add_argument(
        "--model",
        default="llama3.2:3b",
        help="Modelo de Ollama a usar (default: llama3.2:3b). Ejemplo: --model deepseek-coder:6.7b para DeepSeek. También acepta --model deepseek como atajo."
    )
    parser.add_argument("--ollama-url", default="http://localhost:11434", 
                        help="URL del servidor Ollama (default: http://localhost:11434)")

    args = parser.parse_args()

    # Shortcut: if user passes --model deepseek, map to recommended DeepSeek model
    model_arg = args.model.strip().lower()
    if model_arg == "deepseek":
        model_arg = DEEPSEEK_MODEL_DEFAULT
        print(f"ℹ️  Usando modelo DeepSeek recomendado: {DEEPSEEK_MODEL_DEFAULT}")
    else:
        model_arg = args.model

    # Crear y ejecutar procesador
    processor = DataPMProcessorOllama(
        model=model_arg,
        ollama_url=args.ollama_url
    )

    processor.run(args.input_file, args.output)


if __name__ == "__main__":
    main()
