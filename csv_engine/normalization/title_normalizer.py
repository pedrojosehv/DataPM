#!/usr/bin/env python3
"""
Title Normalizer - Actualiza los CSVs procesados al nuevo schema de títulos
"""

import csv
import os
import shutil
from datetime import datetime
import pandas as pd
from difflib import SequenceMatcher
try:
    from csv_engine.utils import config  # type: ignore
except Exception:
    config = None

# Configuración de rutas
PROCESSED_DIR = r"D:\Work Work\Upwork\DataPM\csv\src\csv_processed"
ARCHIVE_DIR = r"D:\Work Work\Upwork\DataPM\csv\src\archive"

# Mapeo de títulos antiguos a nuevos
TITLE_MAPPING = {
    # Data Science & AI
    "Machine Learning Engineer": "Data Scientist",
    "Data Scientist & AI": "Data Scientist",
    "Junior Data Scientist & AI": "Data Scientist",
    
    # Quality Assurance
    "QA Manual": "Quality Assurance Engineer",
    "QA Engineer": "Quality Assurance Engineer",
    "Quality Assurance Analyst": "Quality Assurance Engineer",
    "QA accesibilidad": "Quality Assurance Engineer",
    "Consultor/a de pruebas QA": "Quality Assurance Engineer",
    
    # Documentation
    "Clinical Documentation Specialist": "Documentation Specialist",
    "Trial Master File Specialist": "Documentation Specialist",
    
    # Project Management
    "PMO": "Project Manager",
    "PMO Junior": "Project Manager",
    
    # Finance & Business
    "Investment Banking Analyst": "Financial Analyst",
    "Finanzas Júnior": "Financial Analyst",
    "Business Development Specialist": "Business Analyst",
    
    # Operations & Management
    "Supply Chain Manager": "Operations Manager",
    "Product Specialist": "Product Manager",
    
    # Compliance & Regulatory
    "Compliance Specialist": "Compliance Analyst",
    # Administrative
    "Personal Assistant": "Administrative Assistant",
    "Executive Assistant": "Administrative Assistant",
    "Office Assistant": "Administrative Assistant"
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
    # Canonical lists
    canon_titles = (config.NORMALIZATION_SCHEMA["job_title_short"] if config else list(set(TITLE_MAPPING.values())))
    canon_skills = (config.NORMALIZATION_SCHEMA["skills"] if config else [])
    canon_software = (config.NORMALIZATION_SCHEMA["software"] if config else [])

    SKILL_BLACKLIST = {"Product Management"}

    def fuzzy_best(value: str, canon: list) -> str:
        if not value:
            return "Unknown"
        best, score = None, 0.0
        for c in canon:
            s = SequenceMatcher(None, value.lower(), c.lower()).ratio()
            if s > score:
                best, score = c, s
        return best if score >= 0.80 else "Unknown"

    # Title normalization: rule-based map then fuzzy to canon
    def map_title(row):
        original = str(row.get('Job title (original)', '') or '')
        current = str(row.get('Job title (short)', '') or '')
        mapped = current
        for k, v in TITLE_MAPPING.items():
            if k.lower() in original.lower():
                mapped = v
                break
        mapped = fuzzy_best(mapped or original, canon_titles)
        return mapped

    df['Job title (short)'] = df.apply(map_title, axis=1)

    # Skills/Software canonical reassignment and filtering
    canon_skills_lower = {c.lower(): c for c in canon_skills}
    canon_software_lower = {c.lower(): c for c in canon_software}

    def split_tokens(cell: str) -> list:
        return [t.strip() for t in (cell or '').split(';') if t.strip()]

    def join_tokens(tokens: list) -> str:
        seen = set()
        out = []
        for t in tokens:
            k = t.lower()
            if k not in seen:
                seen.add(k)
                out.append(t)
        return '; '.join(out)

    def normalize_skill_software_row(row):
        skills_tokens = split_tokens(row.get('Skills', ''))
        software_tokens = split_tokens(row.get('Software', ''))

        # Move any software tokens found in skills to software
        moved_to_software = []
        kept_skills = []
        for t in skills_tokens:
            tl = t.lower()
            if tl in canon_software_lower:
                moved_to_software.append(canon_software_lower[tl])
            elif tl in canon_skills_lower:
                canon_val = canon_skills_lower[tl]
                if canon_val not in SKILL_BLACKLIST:
                    kept_skills.append(canon_val)
            # else drop unknown tokens

        # Keep only canonical software in software column
        kept_software = []
        for t in software_tokens:
            tl = t.lower()
            if tl in canon_software_lower:
                kept_software.append(canon_software_lower[tl])

        # Merge and deduplicate
        final_skills = join_tokens(kept_skills)
        final_software = join_tokens(kept_software + moved_to_software)
        row['Skills'] = final_skills
        row['Software'] = final_software
        return row

    if 'Skills' in df.columns and 'Software' in df.columns:
        df = df.apply(normalize_skill_software_row, axis=1)

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
