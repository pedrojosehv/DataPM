#!/usr/bin/env python3
"""
Script para verificar que la carpeta csv_processed esté limpia
y solo contenga archivos procesados con la estructura correcta para PowerBI
"""

import os
import csv
from pathlib import Path
import pandas as pd

def verify_csv_processed():
    """Verificar que csv_processed solo contenga archivos procesados"""
    
    csv_processed_dir = Path("D:/Work Work/Upwork/DataPM/csv/src/csv_processed")
    csv_duplicates_dir = Path("D:/Work Work/Upwork/DataPM/csv/src/csv_duplicates")
    
    print("🔍 VERIFICANDO CARPETA CSV_PROCESSED")
    print("=" * 60)
    
    # Verificar que csv_processed existe
    if not csv_processed_dir.exists():
        print("❌ La carpeta csv_processed no existe")
        return
    
    # Verificar que csv_duplicates existe
    if not csv_duplicates_dir.exists():
        print("❌ La carpeta csv_duplicates no existe")
        return
    
    print(f"✅ Carpeta csv_processed: {csv_processed_dir}")
    print(f"✅ Carpeta csv_duplicates: {csv_duplicates_dir}")
    
    # Listar archivos en csv_processed
    csv_files = list(csv_processed_dir.glob("*.csv"))
    other_files = [f for f in csv_processed_dir.iterdir() if f.is_file() and not f.name.endswith('.csv')]
    subdirs = [f for f in csv_processed_dir.iterdir() if f.is_dir()]
    
    print(f"\n📊 CONTENIDO DE CSV_PROCESSED:")
    print(f"   - Archivos CSV: {len(csv_files)}")
    print(f"   - Otros archivos: {len(other_files)}")
    print(f"   - Subcarpetas: {len(subdirs)}")
    
    if other_files:
        print(f"\n⚠️  ARCHIVOS NO CSV ENCONTRADOS:")
        for file in other_files:
            print(f"   - {file.name}")
    
    if subdirs:
        print(f"\n⚠️  SUBCARPETAS ENCONTRADAS:")
        for subdir in subdirs:
            print(f"   - {subdir.name}")
    
    # Verificar estructura de los CSVs
    print(f"\n🔍 VERIFICANDO ESTRUCTURA DE CSVs:")
    
    expected_columns = [
        "Job title (original)", "Job title (short)", "Company", "Country", 
        "State", "City", "Schedule type", "Experience years", "Seniority", 
        "Skills", "Degrees", "Software"
    ]
    
    valid_files = 0
    invalid_files = 0
    
    for csv_file in csv_files:
        try:
            # Leer las primeras líneas para verificar estructura
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                # Verificar que tenga las columnas esperadas
                missing_columns = [col for col in expected_columns if col not in header]
                
                if not missing_columns:
                    print(f"   ✅ {csv_file.name} - Estructura correcta")
                    valid_files += 1
                else:
                    print(f"   ❌ {csv_file.name} - Faltan columnas: {missing_columns}")
                    invalid_files += 1
                    
        except Exception as e:
            print(f"   ❌ {csv_file.name} - Error al leer: {e}")
            invalid_files += 1
    
    print(f"\n📈 RESUMEN:")
    print(f"   - Archivos válidos: {valid_files}")
    print(f"   - Archivos inválidos: {invalid_files}")
    print(f"   - Total archivos CSV: {len(csv_files)}")
    
    # Verificar contenido de csv_duplicates
    print(f"\n📁 CONTENIDO DE CSV_DUPLICATES:")
    if csv_duplicates_dir.exists():
        duplicates_content = list(csv_duplicates_dir.iterdir())
        print(f"   - Elementos: {len(duplicates_content)}")
        for item in duplicates_content:
            if item.is_dir():
                print(f"   📁 {item.name}/")
            else:
                print(f"   📄 {item.name}")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    if other_files or subdirs:
        print(f"   ⚠️  La carpeta csv_processed contiene elementos no deseados")
        print(f"   🔧 Considera mover estos elementos a csv_duplicates")
    else:
        print(f"   ✅ La carpeta csv_processed está limpia")
    
    if invalid_files > 0:
        print(f"   ⚠️  Hay {invalid_files} archivos CSV con estructura incorrecta")
        print(f"   🔧 Considera reprocesar estos archivos")
    else:
        print(f"   ✅ Todos los archivos CSV tienen la estructura correcta para PowerBI")

if __name__ == "__main__":
    verify_csv_processed()
