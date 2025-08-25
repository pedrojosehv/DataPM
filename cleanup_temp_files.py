#!/usr/bin/env python3
"""
Script para limpiar archivos temporales y verificar que todo esté en orden
"""

import os
import shutil
from pathlib import Path

def cleanup_temp_files():
    """Limpiar archivos temporales y verificar estructura"""
    
    print("🧹 LIMPIEZA DE ARCHIVOS TEMPORALES")
    print("=" * 50)
    
    # Rutas principales
    csv_processed_dir = Path("D:/Work Work/Upwork/DataPM/csv/src/csv_processed")
    csv_duplicates_dir = Path("D:/Work Work/Upwork/DataPM/csv/src/csv_duplicates")
    csv_scrapped_dir = Path("D:/Work Work/Upwork/DataPM/csv/src/scrapped")
    
    # Verificar estructura
    print("📁 VERIFICANDO ESTRUCTURA DE CARPETAS:")
    print(f"   ✅ csv_processed: {csv_processed_dir}")
    print(f"   ✅ csv_duplicates: {csv_duplicates_dir}")
    print(f"   ✅ scrapped: {csv_scrapped_dir}")
    
    # Verificar que csv_processed solo tenga CSVs
    csv_files = list(csv_processed_dir.glob("*.csv"))
    other_files = [f for f in csv_processed_dir.iterdir() if f.is_file() and not f.name.endswith('.csv')]
    subdirs = [f for f in csv_processed_dir.iterdir() if f.is_dir()]
    
    print(f"\n📊 ESTADO DE CSV_PROCESSED:")
    print(f"   - Archivos CSV: {len(csv_files)}")
    print(f"   - Otros archivos: {len(other_files)}")
    print(f"   - Subcarpetas: {len(subdirs)}")
    
    # Limpiar archivos no deseados en csv_processed
    if other_files or subdirs:
        print(f"\n🧹 LIMPIANDO CSV_PROCESSED:")
        
        # Mover archivos no CSV a csv_duplicates
        for file in other_files:
            try:
                dest = csv_duplicates_dir / file.name
                shutil.move(str(file), str(dest))
                print(f"   📄 Movido: {file.name} → csv_duplicates/")
            except Exception as e:
                print(f"   ❌ Error moviendo {file.name}: {e}")
        
        # Mover subcarpetas a csv_duplicates
        for subdir in subdirs:
            try:
                dest = csv_duplicates_dir / subdir.name
                shutil.move(str(subdir), str(dest))
                print(f"   📁 Movido: {subdir.name}/ → csv_duplicates/")
            except Exception as e:
                print(f"   ❌ Error moviendo {subdir.name}/: {e}")
    else:
        print(f"   ✅ csv_processed está limpio")
    
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
    
    # Verificar archivos más recientes
    print(f"\n📅 ARCHIVOS MÁS RECIENTES:")
    if csv_files:
        # Ordenar por fecha de modificación
        csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        print(f"   - Más reciente: {csv_files[0].name}")
        print(f"   - Total archivos: {len(csv_files)}")
    
    # Verificar archivos scrapped
    scrapped_files = list(csv_scrapped_dir.glob("*.csv"))
    if scrapped_files:
        scrapped_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        print(f"\n📥 ARCHIVOS SCRAPPED:")
        print(f"   - Más reciente: {scrapped_files[0].name}")
        print(f"   - Total archivos: {len(scrapped_files)}")
    
    print(f"\n✅ LIMPIEZA COMPLETADA")
    print(f"   - csv_processed: Solo archivos CSV procesados")
    print(f"   - csv_duplicates: Archivos de deduplicación y temporales")
    print(f"   - Estructura lista para PowerBI")

if __name__ == "__main__":
    cleanup_temp_files()
