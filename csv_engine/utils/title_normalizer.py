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
