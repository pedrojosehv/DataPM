#!/usr/bin/env python3
"""
DataPM Processor - Versión GPT-2 (Hugging Face)
Procesa descripciones de trabajo con GPT-2 local y genera CSV estructurado
"""

import csv
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse
from transformers import pipeline

class DataPMProcessorGPT2:
    """Procesador principal para análisis de descripciones de trabajo usando GPT-2"""

    def __init__(self, model: str = "gpt2"):
        self.model = model
        self.generator = pipeline('text-generation', model=self.model)
        # Puedes copiar el mismo schema de normalización del archivo de Ollama si lo necesitas
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

    def create_prompt(self, description: str) -> str:
        """Crea el prompt para GPT-2, adaptando el schema"""
        schema = """
Devuelve SOLO un objeto JSON válido con la siguiente estructura y valores normalizados:
{
  "job_title_original": string,
  "job_title_short": string (usa una de las categorías estándar del schema),
  "experience_years": string ("0-3", "3-5", "5+"),
  "job_schedule_type": string ("Full-time", "Part-time", "Contract", "Internship", "Unknown"),
  "seniority": string ("Intern", "Junior", "Mid", "Senior", "Lead", "Manager", "Unknown"),
  "city": string,
  "state": string,
  "country": string,
  "degrees": array de strings,
  "skills": array de strings,
  "software": array de strings,
  "company_name": string
}
No agregues explicaciones ni texto extra. Si no puedes determinar un valor, usa "Unknown" o un array vacío.
Descripción: """ + description + """
"""
        return schema

    def call_gpt2(self, description: str) -> Dict[str, Any]:
        prompt = self.create_prompt(description)
        result = self.generator(prompt, max_length=350, num_return_sequences=1, do_sample=True, temperature=0.7)[0]['generated_text']
        # Intentar extraer JSON de la respuesta
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = result[json_start:json_end]
            try:
                return json.loads(json_str)
            except Exception:
                pass
        # Si falla, devolver respuesta por defecto
        return self.get_default_response()

    def get_default_response(self) -> Dict[str, Any]:
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
        print(f"🤖 Procesando descripción con GPT-2 ({self.model})...")
        return self.call_gpt2(description)

    def read_csv(self, file_path: str) -> List[Dict[str, str]]:
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
        print(f"🔄 Procesando {len(input_data)} registros...")
        processed_data = []
        for i, row in enumerate(input_data, 1):
            print(f"📝 Procesando registro {i}/{len(input_data)}")
            title = row.get('title', '')
            company = row.get('company', '')
            location = row.get('location', '')
            description = row.get('description', '')
            try:
                llm_result = self.process_description(description)
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
            if i < len(input_data):
                time.sleep(0.2)
        print(f"✅ Procesamiento completado")
        return processed_data

    def write_csv(self, data: List[Dict[str, Any]], output_path: str):
        print(f"💾 Guardando CSV: {output_path}")
        if not data:
            print("⚠️  No hay datos para guardar")
            return
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        print(f"✅ CSV guardado exitosamente")

    def run(self, input_file: str, output_file: Optional[str] = None):
        print("🚀 Iniciando DataPM Processor (GPT-2)")
        print(f"📊 LLM: GPT-2 ({self.model})")
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"csv/archive/{timestamp}_DataPM_GPT2_result.csv"
        try:
            input_data = self.read_csv(input_file)
            processed_data = self.process_data(input_data)
            self.write_csv(processed_data, output_file)
            print(f"🎉 Procesamiento completado exitosamente!")
            print(f"📁 Archivo de salida: {output_file}")
        except Exception as e:
            print(f"❌ Error durante el procesamiento: {e}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="DataPM Processor (GPT-2) - Análisis de descripciones de trabajo")
    parser.add_argument("input_file", help="Archivo CSV de entrada")
    parser.add_argument("--output", "-o", help="Archivo CSV de salida (opcional)")
    parser.add_argument("--model", default="gpt2", help="Modelo de Hugging Face a usar (default: gpt2)")
    args = parser.parse_args()
    processor = DataPMProcessorGPT2(model=args.model)
    processor.run(args.input_file, args.output)

if __name__ == "__main__":
    main()
