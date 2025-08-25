#!/usr/bin/env python3
"""
Script de ejemplo para ejecutar DataPM Processor
Muestra diferentes formas de usar el procesador
"""

import os
import sys
from datapm_processor import DataPMProcessor

def run_with_gemini():
    """Ejecuta el procesador con Google Gemini"""
    print("🔧 Configurando para Google Gemini...")
    
    # Obtener API key desde variable de entorno o input
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        api_key = input("🔑 Ingresa tu API key de Gemini: ").strip()
        if not api_key:
            print("❌ API key requerida para Gemini")
            return
    
    # Configurar procesador
    processor = DataPMProcessor(
        llm_type="gemini",
        api_key=api_key
    )
    
    # Ejecutar procesamiento
    input_file = "csv/linkedin_jobs_make.csv"
    output_file = "csv/archive/gemini_result.csv"
    
    processor.run(input_file, output_file)

def run_with_ollama():
    """Ejecuta el procesador con Ollama"""
    print("🔧 Configurando para Ollama...")
    
    # Verificar que Ollama esté corriendo
    ollama_url = input("🌐 URL de Ollama (default: http://localhost:11434): ").strip()
    if not ollama_url:
        ollama_url = "http://localhost:11434"
    
    # Configurar procesador
    processor = DataPMProcessor(
        llm_type="ollama",
        ollama_url=ollama_url
    )
    
    # Ejecutar procesamiento
    input_file = "csv/linkedin_jobs_make.csv"
    output_file = "csv/archive/ollama_result.csv"
    
    processor.run(input_file, output_file)

def main():
    """Función principal del script de ejemplo"""
    print("🚀 DataPM Processor - Script de Ejemplo")
    print("=" * 50)
    
    # Verificar que el archivo de entrada existe
    input_file = "csv/linkedin_jobs_make.csv"
    if not os.path.exists(input_file):
        print(f"❌ Archivo de entrada no encontrado: {input_file}")
        print("💡 Asegúrate de que el archivo CSV esté en la ubicación correcta")
        return
    
    # Crear directorio de salida si no existe
    os.makedirs("csv/archive", exist_ok=True)
    
    # Menú de opciones
    print("\n📋 Opciones disponibles:")
    print("1. Usar Google Gemini")
    print("2. Usar Ollama")
    print("3. Salir")
    
    choice = input("\n🎯 Selecciona una opción (1-3): ").strip()
    
    if choice == "1":
        run_with_gemini()
    elif choice == "2":
        run_with_ollama()
    elif choice == "3":
        print("👋 ¡Hasta luego!")
    else:
        print("❌ Opción inválida")

if __name__ == "__main__":
    main()
