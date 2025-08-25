#!/usr/bin/env python3
"""
Script de prueba para DataPM Processor
Verifica que el procesador funcione correctamente
"""

import os
import sys
import tempfile
import csv
from datapm_processor import DataPMProcessor

def create_test_csv():
    """Crea un CSV de prueba con datos mínimos"""
    test_data = [
        {
            'title': 'Product Designer Intern',
            'company': 'Test Company',
            'location': 'Madrid, Spain',
            'description': 'We are looking for a Product Designer intern to join our team. Requirements: Bachelor\'s degree in Design, experience with Figma, knowledge of UI/UX principles. This is a full-time internship position for recent graduates.'
        }
    ]
    
    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
    
    with open(temp_file.name, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['title', 'company', 'location', 'description']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in test_data:
            writer.writerow(row)
    
    return temp_file.name

def test_csv_reading():
    """Prueba la lectura de CSV"""
    print("🧪 Probando lectura de CSV...")
    
    # Crear CSV de prueba
    test_file = create_test_csv()
    
    try:
        processor = DataPMProcessor(llm_type="gemini", api_key="test")
        data = processor.read_csv(test_file)
        
        if len(data) == 1 and data[0]['title'] == 'Product Designer Intern':
            print("✅ Lectura de CSV exitosa")
            return True
        else:
            print("❌ Error en lectura de CSV")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de CSV: {e}")
        return False
    finally:
        # Limpiar archivo temporal
        os.unlink(test_file)

def test_prompt_creation():
    """Prueba la creación de prompts"""
    print("🧪 Probando creación de prompts...")
    
    try:
        processor = DataPMProcessor(llm_type="gemini", api_key="test")
        
        # Probar prompt del sistema
        system_prompt = processor.create_system_prompt()
        if "You are a strict data extractor" in system_prompt:
            print("✅ Prompt del sistema creado correctamente")
        else:
            print("❌ Error en prompt del sistema")
            return False
        
        # Probar prompt del usuario
        user_prompt = processor.create_user_prompt("Test description")
        if "INPUT:" in user_prompt and "TASK:" in user_prompt:
            print("✅ Prompt del usuario creado correctamente")
        else:
            print("❌ Error en prompt del usuario")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de prompts: {e}")
        return False

def test_default_response():
    """Prueba la respuesta por defecto"""
    print("🧪 Probando respuesta por defecto...")
    
    try:
        processor = DataPMProcessor(llm_type="gemini", api_key="test")
        default_response = processor.get_default_response()
        
        required_fields = [
            'job_title_original', 'job_title_short', 'experience_years',
            'job_schedule_type', 'seniority', 'city', 'state', 'country',
            'degrees', 'skills', 'software', 'company_name'
        ]
        
        for field in required_fields:
            if field not in default_response:
                print(f"❌ Campo faltante en respuesta por defecto: {field}")
                return False
        
        print("✅ Respuesta por defecto correcta")
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de respuesta por defecto: {e}")
        return False

def test_csv_writing():
    """Prueba la escritura de CSV"""
    print("🧪 Probando escritura de CSV...")
    
    try:
        processor = DataPMProcessor(llm_type="gemini", api_key="test")
        
        # Datos de prueba
        test_data = [
            {
                'Job title (original)': 'Test Job',
                'Job title (short)': 'Product Designer',
                'Company': 'Test Company',
                'Country': 'Spain',
                'State': 'Unknown',
                'City': 'Madrid',
                'Schedule type': 'Full-time',
                'Experience years': '0-3',
                'Seniority': 'Junior',
                'Skills': 'UI/UX Design; Product Design',
                'Degrees': 'Bachelor\'s Degree',
                'Software': 'Figma; Adobe XD'
            }
        ]
        
        # Crear archivo temporal para salida
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_file.close()
        
        # Escribir CSV
        processor.write_csv(test_data, temp_file.name)
        
        # Verificar que el archivo se creó
        if os.path.exists(temp_file.name):
            print("✅ Escritura de CSV exitosa")
            
            # Leer y verificar contenido
            with open(temp_file.name, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                if len(rows) == 1 and rows[0]['Job title (original)'] == 'Test Job':
                    print("✅ Contenido del CSV verificado")
                else:
                    print("❌ Error en contenido del CSV")
                    return False
        else:
            print("❌ Archivo CSV no creado")
            return False
        
        # Limpiar
        os.unlink(temp_file.name)
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de escritura de CSV: {e}")
        return False

def test_processor_initialization():
    """Prueba la inicialización del procesador"""
    print("🧪 Probando inicialización del procesador...")
    
    try:
        # Probar con Gemini
        processor_gemini = DataPMProcessor(llm_type="gemini", api_key="test")
        if processor_gemini.llm_type == "gemini":
            print("✅ Inicialización con Gemini exitosa")
        else:
            print("❌ Error en inicialización con Gemini")
            return False
        
        # Probar con Ollama
        processor_ollama = DataPMProcessor(llm_type="ollama", ollama_url="http://localhost:11434")
        if processor_ollama.llm_type == "ollama":
            print("✅ Inicialización con Ollama exitosa")
        else:
            print("❌ Error en inicialización con Ollama")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de inicialización: {e}")
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("🚀 Iniciando pruebas de DataPM Processor")
    print("=" * 50)
    
    tests = [
        test_processor_initialization,
        test_csv_reading,
        test_prompt_creation,
        test_default_response,
        test_csv_writing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Error inesperado en {test.__name__}: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Resultados: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El procesador está listo para usar.")
        return 0
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
